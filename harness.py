#!/usr/bin/env python3
"""
CLI harness for Claude Code to interact with the bin-packing system.

Commands:
    python harness.py status              — Archive summary + strategy stats (JSON)
    python harness.py select-strategy     — Pick strategy + parents (JSON)
    python harness.py evaluate <file>     — Evaluate a candidate heuristic (JSON)
    python harness.py admit <file> [opts] — Attempt archive admission (JSON)
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
from evaluate import evaluate_candidate, DISTRIBUTIONS, SIZES


LOG_FILE = "results.tsv"
STRATEGY_STATS_FILE = "strategy_stats.json"

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


def _format_profile_table(entry):
    """Format a performance profile as a readable table."""
    if not entry.profile:
        return "(no profile available)"
    lines = ["Distribution      | " + " | ".join(f"n={s:>6}" for s in SIZES)]
    lines.append("-" * len(lines[0]))
    idx = 0
    for dist_name in DISTRIBUTIONS:
        row = f"{dist_name:17s} |"
        for _ in SIZES:
            if idx < len(entry.profile):
                row += f" {entry.profile[idx]:>6.3f} |"
            idx += 1
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
# Helpers
# ---------------------------------------------------------------------------

def _load_strategy_stats():
    if os.path.exists(STRATEGY_STATS_FILE):
        try:
            with open(STRATEGY_STATS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {name: {"attempts": 0, "archive_admissions": 0} for name in STRATEGIES}


def _save_strategy_stats(stats):
    with open(STRATEGY_STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def _get_last_generation():
    if not os.path.exists(LOG_FILE):
        return 0
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
        if len(lines) <= 1:
            return 0
        last_line = lines[-1].strip()
        if last_line:
            return int(last_line.split("\t")[0])
    except (ValueError, IndexError, OSError):
        pass
    return 0


def _ensure_log_header():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("gen\tstrategy\tparents\tstatus\tquality\tnovelty\tsimplicity\tcombined\n")


def _log_result(generation, strategy, parent_names, status, scores):
    _ensure_log_header()
    q = scores.get("quality", 0) if scores else 0
    n = scores.get("novelty", 0) if scores else 0
    s = scores.get("simplicity", 0) if scores else 0
    c = scores.get("combined", 0) if scores else 0
    parents_str = "+".join(parent_names)
    with open(LOG_FILE, "a") as f:
        f.write(f"{generation:05d}\t{strategy}\t{parents_str}\t{status}\t{q:.4f}\t{n:.4f}\t{s:.4f}\t{c:.4f}\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(args):
    """Print archive status and strategy stats as JSON."""
    archive = Archive.load_or_create("archive/")
    stats = _load_strategy_stats()
    generation = _get_last_generation()

    if not archive.has_canonical():
        archive.seed_canonical("archive/canonical/")
        archive.save("archive/")

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
        "archive_size": len(archive),
        "next_generation": generation + 1,
        "entries": entries,
        "strategy_stats": stats,
    }
    print(json.dumps(result, indent=2))


def cmd_select_strategy(args):
    """Select a strategy and parents, return everything needed to generate."""
    archive = Archive.load_or_create("archive/")
    stats = _load_strategy_stats()

    if not archive.has_canonical():
        archive.seed_canonical("archive/canonical/")
        archive.save("archive/")

    strategy = select_strategy(stats)
    parents = select_parents(archive, strategy)
    generation = _get_last_generation() + 1

    parent_data = []
    for p in parents:
        parent_data.append({
            "name": p.name,
            "source": p.source,
            "quality": p.scores.get("quality", 0),
            "novelty": p.scores.get("novelty", 0),
            "profile_table": _format_profile_table(p),
        })

    archive_summary = _archive_summary(archive)

    result = {
        "strategy": strategy,
        "generation": generation,
        "parents": parent_data,
        "archive_summary": archive_summary,
        "archive_size": len(archive),
    }
    print(json.dumps(result, indent=2))


def cmd_evaluate(args):
    """Evaluate a candidate packing heuristic."""
    source_file = args.file
    if not os.path.exists(source_file):
        print(json.dumps({"error": f"File not found: {source_file}"}))
        sys.exit(1)

    with open(source_file) as f:
        source_code = f.read()

    archive = Archive.load_or_create("archive/")

    if not archive.has_canonical():
        archive.seed_canonical("archive/canonical/")
        archive.save("archive/")

    t0 = time.time()
    scores = evaluate_candidate(source_code, archive)
    elapsed = time.time() - t0

    if scores is None:
        result = {"correctness": False, "reason": "evaluation_returned_none", "elapsed": elapsed}
    else:
        result = dict(scores)
        result["elapsed"] = elapsed
        if "profile" in result:
            result["profile_length"] = len(result["profile"])
            del result["profile"]

    print(json.dumps(result, indent=2))


def cmd_admit(args):
    """Attempt to admit a candidate to the archive."""
    source_file = args.file
    if not os.path.exists(source_file):
        print(json.dumps({"error": f"File not found: {source_file}"}))
        sys.exit(1)

    with open(source_file) as f:
        source_code = f.read()

    archive = Archive.load_or_create("archive/")

    if not archive.has_canonical():
        archive.seed_canonical("archive/canonical/")
        archive.save("archive/")

    scores = evaluate_candidate(source_code, archive)

    if scores is None or not scores.get("correctness"):
        reason = scores.get("reason", "unknown") if scores else "unknown"
        result = {"admitted": False, "reason": reason}
        _log_result(args.generation, args.strategy, args.parents.split("+") if args.parents else ["none"],
                     "incorrect", scores)
        _stats = _load_strategy_stats()
        _stats.setdefault(args.strategy, {"attempts": 0, "archive_admissions": 0})
        _stats[args.strategy]["attempts"] += 1
        _save_strategy_stats(_stats)
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

    stats = _load_strategy_stats()
    stats.setdefault(args.strategy, {"attempts": 0, "archive_admissions": 0})
    stats[args.strategy]["attempts"] += 1
    if admitted:
        stats[args.strategy]["archive_admissions"] += 1
    _save_strategy_stats(stats)

    parent_names = args.parents.split("+") if args.parents else ["none"]
    status = "admitted" if admitted else "discarded"
    _log_result(args.generation, args.strategy, parent_names, status, scores)

    if admitted:
        archive.save("archive/")

    result = {
        "admitted": admitted,
        "status": status,
        "quality": scores.get("quality", 0),
        "novelty": scores.get("novelty", 0),
        "simplicity": scores.get("simplicity", 0),
        "combined": scores.get("combined", 0),
        "archive_size": len(archive),
    }
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Bin packing research CLI harness")
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

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "select-strategy":
        cmd_select_strategy(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "admit":
        cmd_admit(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
