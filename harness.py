#!/usr/bin/env python3
"""
CLI harness for Claude Code to interact with the bin-packing system.

Supports both offline and online bin packing tracks via --track flag.

Commands:
    python harness.py status              — Archive summary + strategy stats (JSON)
    python harness.py select-strategy     — Pick strategy + parents (JSON)
    python harness.py evaluate <file>     — Evaluate a candidate heuristic (JSON)
    python harness.py admit <file> [opts] — Attempt archive admission (JSON)
    python harness.py backfill [--force]  — Recompute behavioral signatures
    python harness.py red-team [--target] — Analyze weaknesses

Add --track online to any command to use the online bin packing track.
"""

import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np

from archive import Archive


# ---------------------------------------------------------------------------
# Track configuration
# ---------------------------------------------------------------------------

class TrackConfig:
    """Encapsulates all track-specific paths, evaluators, and constants."""

    def __init__(self, track="online"):
        self.track = track
        self.base_dir = "archive/"
        if track == "online":
            self._prefix = "online_"
            self._log_file = "results.tsv"
            self._stats_file = "strategy_stats.json"
        else:
            self._prefix = ""
            self._log_file = "results.tsv"
            self._stats_file = "strategy_stats.json"

    @property
    def canonical_dir(self):
        return f"archive/{self._prefix}canonical/"

    @property
    def log_file(self):
        return self._log_file

    @property
    def stats_file(self):
        return self._stats_file

    def load_archive(self):
        return Archive.load_or_create(self.base_dir, track=self.track)

    def save_archive(self, archive):
        archive.save(self.base_dir, track=self.track)

    def seed_if_needed(self, archive):
        """Seed canonical heuristics if not already present."""
        if archive.has_canonical():
            return
        if self.track == "online":
            from evaluate_online import (
                extract_online_packer, evaluate_correctness,
                evaluate_quality, simplicity_score,
            )
            archive.seed_canonical(
                self.canonical_dir,
                extract_fn=extract_online_packer,
                correctness_fn=evaluate_correctness,
                quality_fn=evaluate_quality,
                simplicity_fn=simplicity_score,
            )
        else:
            archive.seed_canonical(self.canonical_dir)
        self.save_archive(archive)

    def evaluate_candidate(self, source_code, archive):
        if self.track == "online":
            from evaluate_online import evaluate_candidate
            return evaluate_candidate(source_code, archive)
        else:
            from evaluate import evaluate_candidate
            return evaluate_candidate(source_code, archive)

    def get_distributions(self):
        if self.track == "online":
            from evaluate_online import DISTRIBUTIONS
            return DISTRIBUTIONS
        else:
            from evaluate import DISTRIBUTIONS
            return DISTRIBUTIONS

    def get_sizes(self):
        if self.track == "online":
            from evaluate_online import SIZES
            return SIZES
        else:
            from evaluate import SIZES
            return SIZES

    def extract_and_run(self, source_code):
        """Extract and compile/create a runnable packing function or factory."""
        if self.track == "online":
            from evaluate_online import extract_online_packer
            return extract_online_packer(source_code)
        else:
            from evaluate import extract_and_compile
            return extract_and_compile(source_code)

    def run_quality(self, pack_fn):
        """Run quality evaluation, returns (quality, profile, beh_sig)."""
        if self.track == "online":
            from evaluate_online import evaluate_quality
            return evaluate_quality(pack_fn)
        else:
            from evaluate import evaluate_quality
            return evaluate_quality(pack_fn)

    def load_strategy_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {name: {"attempts": 0, "archive_admissions": 0} for name in STRATEGIES}

    def save_strategy_stats(self, stats):
        with open(self.stats_file, "w") as f:
            json.dump(stats, f, indent=2)

    def get_last_generation(self):
        if not os.path.exists(self.log_file):
            return 0
        try:
            with open(self.log_file) as f:
                lines = f.readlines()
            if len(lines) <= 1:
                return 0
            last_line = lines[-1].strip()
            if last_line:
                return int(last_line.split("\t")[0])
        except (ValueError, IndexError, OSError):
            pass
        return 0

    def ensure_log_header(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("gen\tstrategy\tparents\tstatus\tquality\tnovelty\tsimplicity\tcombined\n")

    def log_result(self, generation, strategy, parent_names, status, scores):
        self.ensure_log_header()
        q = scores.get("quality", 0) if scores else 0
        n = scores.get("novelty", 0) if scores else 0
        s = scores.get("simplicity", 0) if scores else 0
        c = scores.get("combined", 0) if scores else 0
        parents_str = "+".join(parent_names)
        with open(self.log_file, "a") as f:
            f.write(f"{generation:05d}\t{strategy}\t{parents_str}\t{status}\t{q:.4f}\t{n:.4f}\t{s:.4f}\t{c:.4f}\n")


# ---------------------------------------------------------------------------
# Strategy definitions
# ---------------------------------------------------------------------------

STRATEGIES = {
    "standard_mutation":    0.15,
    "anomaly_hunt":         0.15,
    "cross_domain":         0.15,
    "first_principles":     0.10,
    "constraint_inject":    0.15,
    "distribution_aware":   0.10,
    "outsider_perspective": 0.10,
    "novelty_search":       0.10,
}


def select_strategy(strategy_stats):
    """Adaptive strategy selection via UCB1 bandit."""
    total_attempts = sum(s.get("attempts", 0) for s in strategy_stats.values())
    weights = {}
    for name, base_weight in STRATEGIES.items():
        stats = strategy_stats.get(name, {"attempts": 0, "archive_admissions": 0})
        attempts = stats.get("attempts", 0)
        successes = stats.get("archive_admissions", 0)
        if attempts == 0:
            weights[name] = float("inf")
        else:
            success_rate = successes / attempts
            exploration_bonus = math.sqrt(2 * math.log(max(total_attempts, 1)) / attempts)
            weights[name] = base_weight * (1 + success_rate + exploration_bonus)

    items = list(weights.items())
    inf_items = [name for name, w in items if w == float("inf")]
    if inf_items:
        return random.choice(inf_items)

    total = sum(w for _, w in items)
    r = random.random() * total
    cumulative = 0
    for name, w in items:
        cumulative += w
        if r <= cumulative:
            return name
    return items[-1][0]


def select_parents(archive, strategy):
    """Select 1-2 parent heuristics from the archive."""
    from novelty import _cosine_distance

    entries = archive.get_all_entries()
    if not entries:
        return []

    if strategy == "cross_domain":
        if len(entries) < 2:
            return entries[:1]
        max_dist = -1
        best_pair = (entries[0], entries[1])
        for i, a in enumerate(entries):
            for j, b in enumerate(entries):
                if i >= j or not a.profile or not b.profile:
                    continue
                dist = _cosine_distance(a.profile, b.profile)
                if dist > max_dist:
                    max_dist = dist
                    best_pair = (a, b)
        return list(best_pair)
    elif strategy == "anomaly_hunt":
        best = entries[0]
        max_var = -1
        for entry in entries:
            if not entry.profile:
                continue
            var = float(np.var(entry.profile))
            if var > max_var:
                max_var = var
                best = entry
        return [best]
    elif strategy == "first_principles":
        return []
    else:
        sample = random.sample(entries, min(3, len(entries)))
        winner = max(sample, key=lambda e: e.scores.get("combined", 0) + 0.5 * e.scores.get("novelty", 0))
        return [winner]


def _format_profile_table(entry, tc):
    """Format a performance profile as a readable table."""
    if not entry.profile:
        return "(no profile available)"

    distributions = tc.get_distributions()
    sizes = tc.get_sizes()

    if tc.track == "online":
        return _format_online_profile_table(entry, distributions, sizes)

    lines = ["Distribution      | " + " | ".join(f"n={s:>6}" for s in sizes)]
    lines.append("-" * len(lines[0]))
    idx = 0
    for dist_name in distributions:
        row = f"{dist_name:17s} |"
        for _ in sizes:
            if idx < len(entry.profile):
                row += f" {entry.profile[idx]:>6.3f} |"
            idx += 1
        lines.append(row)
    return "\n".join(lines)


def _format_online_profile_table(entry, distributions, sizes):
    """Format online profile table: dist × size, averaged across arrival orders."""
    from evaluate_online import ARRIVAL_ORDERS
    n_orders = len(ARRIVAL_ORDERS)

    lines = ["Distribution      | " + " | ".join(f"n={s:>6}" for s in sizes)]
    lines.append("-" * len(lines[0]))

    idx = 0
    for dist_name in distributions:
        row = f"{dist_name:17s} |"
        for _ in sizes:
            # Average across arrival orders for this (dist, size) cell
            vals = []
            for _ in range(n_orders):
                if idx < len(entry.profile):
                    vals.append(entry.profile[idx])
                idx += 1
            avg = sum(vals) / len(vals) if vals else 0
            row += f" {avg:>6.3f} |"
        lines.append(row)
    return "\n".join(lines)


def _archive_summary(archive):
    """Brief summary of all heuristics in the archive."""
    entries = archive.get_all_entries()
    lines = []
    for e in entries:
        q = e.scores.get("quality", 0)
        n = e.scores.get("novelty", 0)
        lines.append(f"- {e.name}: quality={q:.3f}, novelty={n:.3f}, strategy={e.strategy or 'canonical'}")
    return "\n".join(lines) if lines else "(empty archive)"


# ---------------------------------------------------------------------------
# Creativity-enhancing prompts (based on innovation research)
# ---------------------------------------------------------------------------

CREATIVITY_PROMPTS = {
    "standard_mutation": (
        "VERBALIZED SAMPLING: Before modifying the parent, generate 5 distinct mutation ideas. "
        "Estimate the probability each will beat the parent. DEVELOP THE ONE YOU RATE < 5% — "
        "counterintuitive approaches often break through plateaus. "
        "ANTI-PATTERN: The parent uses a conventional approach. What assumption does it make "
        "that could be wrong? What if you violated that assumption entirely?"
    ),
    "anomaly_hunt": (
        "ROOT CAUSE ANALYSIS: For the worst-performing (distribution, size) cell: "
        "1) What specific item sequences cause poor packing? "
        "2) WHY does the algorithm fail on those sequences? (not 'it wastes space' — WHY?) "
        "3) What mathematical property of those items is unexploited? "
        "Design a fix that addresses the ROOT CAUSE, not the symptom."
    ),
    "cross_domain": (
        "ANALOGICAL MAPPING: Don't just combine code from two parents. "
        "1) Identify the ABSTRACT PRINCIPLE behind each parent (not its implementation). "
        "2) What deeper idea do they share? What contradicts between them? "
        "3) Synthesize a new principle that resolves the contradiction. "
        "The result should be something neither parent could do alone."
    ),
    "first_principles": (
        "CONSTRAINT RELAXATION: List 5 implicit assumptions ALL known bin packing heuristics make. "
        "Examples: 'items must be sorted', 'bins are filled one at a time', 'placement is greedy'. "
        "Now violate at least 2 of these assumptions. What algorithm emerges? "
        "VERBALIZED SAMPLING: Generate 5 approaches and estimate each one's probability "
        "of being genuinely novel. Develop the most unlikely one."
    ),
    "constraint_inject": (
        "FORCED NOVELTY: The constraint isn't just a limitation — it's a design driver. "
        "How does the constraint force you to discover structures that unconstrained "
        "algorithms would never find? The best constrained algorithms often outperform "
        "unconstrained ones in specific regimes."
    ),
    "distribution_aware": (
        "PREDICTION-DRIVEN: Don't just detect the distribution — predict what items "
        "will arrive next and pre-allocate bin space accordingly. What statistical "
        "properties (skewness, kurtosis, mode count) are informative? "
        "Design a heuristic that would look insane for uniform data but excels on "
        "the specific distribution it detects."
    ),
    "outsider_perspective": (
        "ORDINARY PERSONA (research shows these beat 'Steve Jobs' personas): "
        "Think as a specific non-expert — a kindergarten teacher sorting blocks by color "
        "and size, a Tetris speedrunner who thinks in shapes, a postal worker who's sorted "
        "mail for 30 years. What intuition would they bring that CS theory misses? "
        "Their approach should feel WEIRD to a computer scientist."
    ),
    "novelty_search": (
        "MAXIMUM STRUCTURAL DIFFERENCE: Your goal is NOT quality — it's being different. "
        "Use programming constructs nobody in the archive has tried: generators, dataclasses, "
        "Counter, enumerate as primary loop, array.array, bitwise ops. "
        "The algorithm should make a CS professor say 'that's not how you do bin packing' "
        "while still being correct."
    ),
}


def _creativity_prompt(strategy, archive):
    """Generate a creativity-enhancing prompt for the given strategy."""
    return CREATIVITY_PROMPTS.get(strategy, "")


def _anti_convergence_note(archive):
    """Analyze archive for over-represented patterns and warn about convergence."""
    all_sources = archive.get_all_sources()
    if not all_sources:
        return ""

    n = len(all_sources)
    patterns = {
        "sorted(items, reverse=True) or sorted(..., reverse=True)": sum(
            1 for s in all_sources if "reverse=True" in s
        ),
        "bisect_right for complement seeking": sum(
            1 for s in all_sources if "bisect_right" in s
        ),
        "linear scan for best-fit bin (for i/k in range(len(bins)))": sum(
            1 for s in all_sources if "best_" in s and "range(len(" in s
        ),
        "bin_sums as parallel tracking list": sum(
            1 for s in all_sources if "bin_sums" in s or "sums[" in s
        ),
    }

    warnings = []
    for pattern, count in patterns.items():
        if count > n * 0.4:
            warnings.append(f"- {pattern}: used by {count}/{n} members ({100*count//n}%)")

    if not warnings:
        return ""

    header = (
        "ANTI-CONVERGENCE WARNING: The archive is dominated by these patterns. "
        "Candidates using them are unlikely to achieve behavioral novelty:\n"
    )
    footer = (
        "\nTo achieve admission, use fundamentally different data structures and "
        "control flow. Quality 0.95 with genuine novelty > quality 0.99 without."
    )
    return header + "\n".join(warnings) + footer


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(args, tc):
    """Print archive status and strategy stats as JSON."""
    archive = tc.load_archive()
    stats = tc.load_strategy_stats()
    generation = tc.get_last_generation()

    tc.seed_if_needed(archive)

    entries = []
    for entry in archive.get_all_entries():
        entries.append({
            "name": entry.name,
            "quality": entry.scores.get("quality", 0),
            "novelty": entry.scores.get("novelty", 0),
            "simplicity": entry.scores.get("simplicity", 0),
            "combined": entry.scores.get("combined", 0),
            "strategy": entry.strategy or "canonical",
            "is_canonical": entry.is_canonical,
            "generation": entry.generation,
            "parents": entry.parents,
        })

    result = {
        "track": tc.track,
        "archive_size": len(archive),
        "next_generation": generation + 1,
        "entries": entries,
        "strategy_stats": stats,
    }
    print(json.dumps(result, indent=2))


def cmd_select_strategy(args, tc):
    """Select a strategy and parents, return everything needed to generate."""
    archive = tc.load_archive()
    stats = tc.load_strategy_stats()

    tc.seed_if_needed(archive)

    strategy = select_strategy(stats)
    parents = select_parents(archive, strategy)
    generation = tc.get_last_generation() + 1

    parent_data = []
    for p in parents:
        parent_data.append({
            "name": p.name,
            "source": p.source,
            "quality": p.scores.get("quality", 0),
            "novelty": p.scores.get("novelty", 0),
            "profile_table": _format_profile_table(p, tc),
        })

    archive_summary = _archive_summary(archive)
    creativity_prompt = _creativity_prompt(strategy, archive)
    anti_convergence = _anti_convergence_note(archive)

    result = {
        "track": tc.track,
        "strategy": strategy,
        "generation": generation,
        "parents": parent_data,
        "archive_summary": archive_summary,
        "archive_size": len(archive),
        "creativity_prompt": creativity_prompt,
        "anti_convergence": anti_convergence,
    }

    # For online track, include interface reminder
    if tc.track == "online":
        result["interface"] = (
            "ONLINE INTERFACE: Define create_packer(capacity) returning an object with "
            "place(item) -> int and get_bins() -> list[list[float]]. "
            "Items arrive one at a time — NO lookahead, NO reordering."
        )

    print(json.dumps(result, indent=2))


def cmd_evaluate(args, tc):
    """Evaluate a candidate packing heuristic."""
    source_file = args.file
    if not os.path.exists(source_file):
        print(json.dumps({"error": f"File not found: {source_file}"}))
        sys.exit(1)

    with open(source_file) as f:
        source_code = f.read()

    archive = tc.load_archive()
    tc.seed_if_needed(archive)

    t0 = time.time()
    scores = tc.evaluate_candidate(source_code, archive)
    elapsed = time.time() - t0

    if scores is None:
        result = {"correctness": False, "reason": "evaluation_returned_none", "elapsed": elapsed}
    else:
        result = dict(scores)
        result["track"] = tc.track
        result["elapsed"] = elapsed
        if "profile" in result:
            result["profile_length"] = len(result["profile"])
            del result["profile"]
        if "behavioral_signature" in result:
            result["signature_length"] = len(result["behavioral_signature"])
            del result["behavioral_signature"]

    print(json.dumps(result, indent=2))


def cmd_admit(args, tc):
    """Attempt to admit a candidate to the archive."""
    source_file = args.file
    if not os.path.exists(source_file):
        print(json.dumps({"error": f"File not found: {source_file}"}))
        sys.exit(1)

    with open(source_file) as f:
        source_code = f.read()

    archive = tc.load_archive()
    tc.seed_if_needed(archive)

    scores = tc.evaluate_candidate(source_code, archive)

    if scores is None or not scores.get("correctness"):
        reason = scores.get("reason", "unknown") if scores else "unknown"
        result = {"admitted": False, "reason": reason}
        tc.log_result(args.generation, args.strategy,
                      args.parents.split("+") if args.parents else ["none"],
                      "incorrect", scores)
        stats = tc.load_strategy_stats()
        stats.setdefault(args.strategy, {"attempts": 0, "archive_admissions": 0})
        stats[args.strategy]["attempts"] += 1
        tc.save_strategy_stats(stats)
        print(json.dumps(result, indent=2))
        return

    parents_list = []
    if args.parents:
        for pname in args.parents.split("+"):
            entry = archive.get_entry(pname)
            if entry:
                parents_list.append(entry)

    admitted = archive.try_admit(
        source_code=source_code,
        scores=scores,
        parents=parents_list,
        strategy=args.strategy,
        generation=args.generation,
        reasoning=args.reasoning or "",
    )

    stats = tc.load_strategy_stats()
    stats.setdefault(args.strategy, {"attempts": 0, "archive_admissions": 0})
    stats[args.strategy]["attempts"] += 1
    if admitted:
        stats[args.strategy]["archive_admissions"] += 1
    tc.save_strategy_stats(stats)

    parent_names = args.parents.split("+") if args.parents else ["none"]
    status = "admitted" if admitted else "discarded"
    tc.log_result(args.generation, args.strategy, parent_names, status, scores)

    if admitted:
        tc.save_archive(archive)

    result = {
        "admitted": admitted,
        "status": status,
        "track": tc.track,
        "quality": scores.get("quality", 0),
        "novelty": scores.get("novelty", 0),
        "simplicity": scores.get("simplicity", 0),
        "combined": scores.get("combined", 0),
        "archive_size": len(archive),
    }
    print(json.dumps(result, indent=2))


def cmd_backfill(args, tc):
    """Recompute behavioral signatures for all archive entries."""
    archive = tc.load_archive()
    tc.seed_if_needed(archive)

    updated = 0
    total = len(archive)

    for name, entry in archive.algorithms.items():
        if entry.behavioral_signature and not args.force:
            continue
        if not entry.source:
            print(f"  SKIP {name}: no source code")
            continue

        pack_fn = tc.extract_and_run(entry.source)
        if pack_fn is None:
            print(f"  SKIP {name}: failed to compile")
            continue

        _, profile, beh_sig = tc.run_quality(pack_fn)
        entry.behavioral_signature = beh_sig
        entry.profile = profile
        updated += 1
        print(f"  Backfilled {name} (signature length: {len(beh_sig)})")

    tc.save_archive(archive)

    # Compute pairwise distances for threshold calibration
    from novelty import _euclidean_distance
    sigs = [(name, entry.behavioral_signature)
            for name, entry in archive.algorithms.items()
            if entry.behavioral_signature]

    if len(sigs) >= 2:
        distances = []
        for i in range(len(sigs)):
            for j in range(i + 1, len(sigs)):
                d = _euclidean_distance(sigs[i][1], sigs[j][1])
                distances.append((d, sigs[i][0], sigs[j][0]))
        distances.sort()

        print(f"\n--- Pairwise behavioral distance statistics ({len(distances)} pairs) ---")
        vals = [d[0] for d in distances]
        print(f"  Min:    {vals[0]:.6f}  ({distances[0][1]} vs {distances[0][2]})")
        print(f"  Median: {vals[len(vals)//2]:.6f}")
        print(f"  Mean:   {sum(vals)/len(vals):.6f}")
        print(f"  Max:    {vals[-1]:.6f}  ({distances[-1][1]} vs {distances[-1][2]})")
        print(f"  P90:    {vals[int(len(vals)*0.9)]:.6f}")
        print(f"  P10:    {vals[int(len(vals)*0.1)]:.6f}")
        from archive import BEHAVIORAL_NICHE_THRESHOLD
        print(f"\n  Current BEHAVIORAL_NICHE_THRESHOLD: {BEHAVIORAL_NICHE_THRESHOLD}")
        p75 = vals[int(len(vals) * 0.75)]
        print(f"  Suggested threshold (P75): {p75:.4f}")

    result = {"track": tc.track, "updated": updated, "total": total}
    print(json.dumps(result, indent=2))


def cmd_red_team(args, tc):
    """Analyze the best heuristic's weaknesses in detail."""
    archive = tc.load_archive()
    tc.seed_if_needed(archive)

    target_name = args.target if hasattr(args, 'target') and args.target else None
    if target_name:
        entry = archive.get_entry(target_name)
    else:
        entries = archive.get_all_entries()
        entry = max(entries, key=lambda e: e.scores.get("quality", 0))

    if not entry or not entry.source:
        print(json.dumps({"error": "Target not found or has no source"}))
        return

    pack_fn = tc.extract_and_run(entry.source)
    if not pack_fn:
        print(json.dumps({"error": "Failed to compile target"}))
        return

    distributions = tc.get_distributions()
    sizes = tc.get_sizes()

    rng = random.Random(123)
    analysis = {
        "track": tc.track,
        "target": entry.name,
        "quality": entry.scores.get("quality", 0),
        "weak_spots": [],
        "suggestions": [],
    }

    if tc.track == "online":
        _red_team_online(pack_fn, distributions, sizes, rng, analysis)
    else:
        _red_team_offline(pack_fn, distributions, sizes, rng, analysis)

    # Generate suggestions
    if analysis["weak_spots"]:
        worst = max(analysis["weak_spots"], key=lambda w: w["excess_bins"])
        analysis["suggestions"].append(
            f"Biggest gap: {worst['distribution']} n={worst['n']} — "
            f"{worst['excess_bins']} excess bins, worst fill {worst.get('worst_bin_fill', 0):.2f}. "
            f"Focus on improving packing for this distribution."
        )
        underfilled_dists = [w for w in analysis["weak_spots"] if w.get("bins_under_80pct", 0) > 2]
        if underfilled_dists:
            analysis["suggestions"].append(
                f"{len(underfilled_dists)} cases have bins under 80% fill."
            )
    else:
        analysis["suggestions"].append("No significant weak spots found (all ratios > 0.97).")

    print(json.dumps(analysis, indent=2))


def _red_team_offline(pack_fn, distributions, sizes, rng, analysis):
    """Red-team analysis for offline heuristics."""
    from evaluate import _lower_bound
    for dist_name, gen in distributions.items():
        for size in sizes:
            items = gen(size, rng)
            items = [max(0.01, min(0.99, x)) for x in items]
            try:
                result = pack_fn(list(items), 1.0)
                bins = [b for b in result if b]
            except Exception:
                bins = [[x] for x in items]

            lb = _lower_bound(items)
            bins_used = len(bins)
            ratio = lb / max(bins_used, 1)

            if ratio < 0.97:
                fills = [sum(b) for b in bins]
                analysis["weak_spots"].append({
                    "distribution": dist_name,
                    "n": size,
                    "ratio": round(ratio, 4),
                    "bins_used": bins_used,
                    "lower_bound": lb,
                    "excess_bins": bins_used - lb,
                    "worst_bin_fill": round(min(fills) if fills else 0, 4),
                    "bins_under_80pct": sum(1 for f in fills if f < 0.8),
                    "avg_fill": round(sum(fills) / len(fills) if fills else 0, 4),
                })


def _red_team_online(packer_factory, distributions, sizes, rng, analysis):
    """Red-team analysis for online heuristics."""
    from evaluate_online import _lower_bound, ARRIVAL_ORDERS, BIN_CAPACITY
    for dist_name, gen in distributions.items():
        for size in sizes:
            items = gen(size, rng)
            items = [max(0.01, min(0.99, x)) for x in items]
            lb = _lower_bound(items)

            for order_name, reorder in ARRIVAL_ORDERS.items():
                order_rng = random.Random(rng.randint(0, 2**31))
                ordered = reorder(items, order_rng)
                try:
                    packer = packer_factory(BIN_CAPACITY)
                    for item in ordered:
                        packer.place(item)
                    result = packer.get_bins()
                    bins = [b for b in result if b]
                except Exception:
                    bins = [[x] for x in items]

                bins_used = len(bins)
                ratio = lb / max(bins_used, 1)

                if ratio < 0.95:  # Online has wider gaps, use 0.95 threshold
                    fills = [sum(b) for b in bins]
                    analysis["weak_spots"].append({
                        "distribution": dist_name,
                        "n": size,
                        "arrival_order": order_name,
                        "ratio": round(ratio, 4),
                        "bins_used": bins_used,
                        "lower_bound": lb,
                        "excess_bins": bins_used - lb,
                        "worst_bin_fill": round(min(fills) if fills else 0, 4),
                        "bins_under_80pct": sum(1 for f in fills if f < 0.8),
                        "avg_fill": round(sum(fills) / len(fills) if fills else 0, 4),
                    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Bin packing research CLI harness")
    parser.add_argument("--track", choices=["online", "offline"], default="online",
                        help="Bin packing track: online (items one at a time) or offline (full list)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show archive status")
    sub.add_parser("select-strategy", help="Select strategy and parents")

    eval_p = sub.add_parser("evaluate", help="Evaluate a candidate")
    eval_p.add_argument("file", help="Path to candidate .py file")

    admit_p = sub.add_parser("admit", help="Admit a candidate to the archive")
    admit_p.add_argument("file", help="Path to candidate .py file")
    admit_p.add_argument("--strategy", required=True, help="Strategy used")
    admit_p.add_argument("--generation", type=int, required=True, help="Generation number")
    admit_p.add_argument("--parents", default="", help="Parent names joined by +")
    admit_p.add_argument("--reasoning", default="", help="LLM reasoning")

    backfill_p = sub.add_parser("backfill", help="Recompute behavioral signatures for all archive entries")
    backfill_p.add_argument("--force", action="store_true", help="Recompute even if signature exists")

    red_team_p = sub.add_parser("red-team", help="Analyze a heuristic's weaknesses")
    red_team_p.add_argument("--target", default="", help="Archive entry name (default: best quality)")

    args = parser.parse_args()
    tc = TrackConfig(track=args.track)

    if args.command == "status":
        cmd_status(args, tc)
    elif args.command == "select-strategy":
        cmd_select_strategy(args, tc)
    elif args.command == "evaluate":
        cmd_evaluate(args, tc)
    elif args.command == "admit":
        cmd_admit(args, tc)
    elif args.command == "backfill":
        cmd_backfill(args, tc)
    elif args.command == "red-team":
        cmd_red_team(args, tc)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
