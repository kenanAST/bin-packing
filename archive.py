"""
Archive management: admission, eviction, diversity maintenance, lineage tracking.

The archive maintains a diverse population of bin packing heuristics,
not just a single best. Inspired by MAP-Elites and FunSearch's island model.
"""

import ast
import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from novelty import _cosine_distance, _euclidean_distance, ast_novelty


# ---------------------------------------------------------------------------
# Archive entry
# ---------------------------------------------------------------------------

@dataclass
class ArchiveEntry:
    name: str
    source: str
    scores: dict
    profile: list
    behavioral_signature: list = field(default_factory=list)
    parents: list = field(default_factory=list)
    strategy: str = ""
    generation: int = 0
    reasoning: str = ""
    is_canonical: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "scores": self.scores,
            "profile": self.profile,
            "behavioral_signature": self.behavioral_signature,
            "parents": self.parents,
            "strategy": self.strategy,
            "generation": self.generation,
            "reasoning": self.reasoning,
            "is_canonical": self.is_canonical,
        }

    @classmethod
    def from_dict(cls, d, source=""):
        return cls(
            name=d["name"],
            source=source,
            scores=d.get("scores", {}),
            profile=d.get("profile", []),
            behavioral_signature=d.get("behavioral_signature", []),
            parents=d.get("parents", []),
            strategy=d.get("strategy", ""),
            generation=d.get("generation", 0),
            reasoning=d.get("reasoning", ""),
            is_canonical=d.get("is_canonical", False),
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ARCHIVE_MAX_SIZE = 100
BEHAVIORAL_NICHE_THRESHOLD = 0.05  # Euclidean distance on 270-element behavioral signatures
STRUCTURAL_NICHE_THRESHOLD = 0.3


# ---------------------------------------------------------------------------
# Archive
# ---------------------------------------------------------------------------

class Archive:
    def __init__(self):
        self.algorithms: dict[str, ArchiveEntry] = {}

    def __len__(self):
        return len(self.algorithms)

    def has_canonical(self):
        return any(a.is_canonical for a in self.algorithms.values())

    def get_all_sources(self):
        return [a.source for a in self.algorithms.values()]

    def get_all_profiles(self):
        return [a.profile for a in self.algorithms.values() if a.profile]

    def get_all_behavioral_signatures(self):
        return [a.behavioral_signature for a in self.algorithms.values()
                if a.behavioral_signature]

    def get_all_entries(self):
        return list(self.algorithms.values())

    def get_entry(self, name):
        return self.algorithms.get(name)

    # ----- Seeding -----

    def seed_canonical(self, canonical_dir, extract_fn=None, correctness_fn=None,
                       quality_fn=None, simplicity_fn=None):
        """Load canonical bin packing heuristics from a directory.

        For online track, pass the evaluator functions from evaluate_online.
        Defaults to offline evaluator functions from evaluate.py.
        """
        canonical_dir = Path(canonical_dir)
        if not canonical_dir.exists():
            return

        if extract_fn is None:
            from evaluate import evaluate_correctness, evaluate_quality, simplicity_score, extract_and_compile
            extract_fn = extract_and_compile
            correctness_fn = evaluate_correctness
            quality_fn = evaluate_quality
            simplicity_fn = simplicity_score

        for py_file in sorted(canonical_dir.glob("*.py")):
            source = py_file.read_text()
            name = py_file.stem

            pack_fn = extract_fn(source)
            if pack_fn is None:
                print(f"  SKIP {name}: failed to compile")
                continue

            if not correctness_fn(pack_fn, trials=100):
                print(f"  SKIP {name}: failed correctness")
                continue

            quality, profile, beh_sig = quality_fn(pack_fn)
            simpl = simplicity_fn(source)

            entry = ArchiveEntry(
                name=name,
                source=source,
                scores={
                    "correctness": True,
                    "quality": quality,
                    "novelty": 0.0,
                    "simplicity": simpl,
                    "combined": 0.0,
                },
                profile=profile,
                behavioral_signature=beh_sig,
                is_canonical=True,
            )
            self.algorithms[name] = entry
            print(f"  Seeded {name}: quality={quality:.4f} simplicity={simpl:.4f}")

    # ----- Admission -----

    def try_admit(self, source_code, scores, parents, strategy, generation, reasoning=""):
        """Admit if the candidate increases archive diversity or is Pareto-improving."""
        profile = scores.get("profile", [])
        beh_sig = scores.get("behavioral_signature", [])

        # Condition 1: Pareto improvement
        if self._is_pareto_improvement(scores):
            self._admit(source_code, scores, parents, strategy, generation, reasoning)
            return True

        # Condition 2: Behavioral niche (rich signatures with Euclidean distance)
        if beh_sig:
            arch_sigs = [a.behavioral_signature for a in self.algorithms.values()
                         if a.behavioral_signature and len(a.behavioral_signature) == len(beh_sig)]
            if arch_sigs:
                min_dist = min(_euclidean_distance(beh_sig, s) for s in arch_sigs)
                if min_dist > BEHAVIORAL_NICHE_THRESHOLD:
                    self._admit(source_code, scores, parents, strategy, generation, reasoning)
                    return True

        # Condition 2b: Legacy behavioral niche (cosine on profiles, for old entries)
        if not beh_sig and profile and self.get_all_profiles():
            min_behavioral_dist = min(
                _cosine_distance(profile, a.profile)
                for a in self.algorithms.values()
                if a.profile
            )
            if min_behavioral_dist > BEHAVIORAL_NICHE_THRESHOLD:
                self._admit(source_code, scores, parents, strategy, generation, reasoning)
                return True

        # Condition 3: Structural niche
        all_sources = self.get_all_sources()
        if all_sources:
            ast_nov = ast_novelty(source_code, all_sources)
            if ast_nov > STRUCTURAL_NICHE_THRESHOLD:
                self._admit(source_code, scores, parents, strategy, generation, reasoning)
                return True

        return False

    def _is_pareto_improvement(self, scores):
        """Check if scores are not dominated by any existing member on all axes."""
        q = scores.get("quality", 0)
        n = scores.get("novelty", 0)
        s = scores.get("simplicity", 0)

        for a in self.algorithms.values():
            aq = a.scores.get("quality", 0)
            an = a.scores.get("novelty", 0)
            a_s = a.scores.get("simplicity", 0)
            if aq >= q and an >= n and a_s >= s and (aq > q or an > n or a_s > s):
                return False

        for a in self.algorithms.values():
            aq = a.scores.get("quality", 0)
            an = a.scores.get("novelty", 0)
            a_s = a.scores.get("simplicity", 0)
            if q >= aq and n >= an and s >= a_s and (q > aq or n > an or s > a_s):
                return True

        return False

    def _admit(self, source_code, scores, parents, strategy, generation, reasoning):
        """Add a candidate to the archive."""
        code_hash = hashlib.sha256(source_code.encode()).hexdigest()[:8]
        name = f"gen_{generation:05d}_{code_hash}"

        parent_names = [p.name for p in parents] if parents else []

        entry = ArchiveEntry(
            name=name,
            source=source_code,
            scores=scores,
            profile=scores.get("profile", []),
            behavioral_signature=scores.get("behavioral_signature", []),
            parents=parent_names,
            strategy=strategy,
            generation=generation,
            reasoning=reasoning,
            is_canonical=False,
        )
        self.algorithms[name] = entry
        self._evict_if_full()

    def _evict_if_full(self):
        """Remove the algorithm whose removal least reduces diversity."""
        if len(self.algorithms) <= ARCHIVE_MAX_SIZE:
            return

        min_loss = float("inf")
        evict_candidate = None

        for name, algo in self.algorithms.items():
            if algo.is_canonical:
                continue
            loss = self._diversity_loss_if_removed(name)
            if loss < min_loss:
                min_loss = loss
                evict_candidate = name

        if evict_candidate:
            del self.algorithms[evict_candidate]

    def _diversity_loss_if_removed(self, name):
        """How much diversity is lost if we remove this algorithm?"""
        algo = self.algorithms[name]

        total = 0.0
        for other_name, other in self.algorithms.items():
            if other_name == name:
                continue
            # Prefer behavioral signature distance, fall back to profile cosine
            if algo.behavioral_signature and other.behavioral_signature:
                total += _euclidean_distance(algo.behavioral_signature,
                                             other.behavioral_signature)
            elif algo.profile and other.profile:
                total += _cosine_distance(algo.profile, other.profile)
        return total

    # ----- Persistence -----

    def save(self, base_dir, track="offline"):
        """Save archive state to disk."""
        base_dir = Path(base_dir)
        prefix = "online_" if track == "online" else ""
        discovered_dir = base_dir / f"{prefix}discovered"
        profiles_dir = base_dir / f"{prefix}profiles"
        signatures_dir = base_dir / f"{prefix}signatures"
        discovered_dir.mkdir(parents=True, exist_ok=True)
        profiles_dir.mkdir(parents=True, exist_ok=True)
        signatures_dir.mkdir(parents=True, exist_ok=True)

        state = {}
        for name, entry in self.algorithms.items():
            state[name] = entry.to_dict()

            if not entry.is_canonical:
                (discovered_dir / f"{name}.py").write_text(entry.source)

            if entry.profile:
                (profiles_dir / f"{name}.json").write_text(
                    json.dumps(entry.profile)
                )

            if entry.behavioral_signature:
                (signatures_dir / f"{name}.json").write_text(
                    json.dumps(entry.behavioral_signature)
                )

        (base_dir / f"{prefix}archive_state.json").write_text(
            json.dumps(state, indent=2)
        )

    @classmethod
    def load_or_create(cls, base_dir, track="offline"):
        """Load archive from disk or create a new one."""
        base_dir = Path(base_dir)
        prefix = "online_" if track == "online" else ""
        state_file = base_dir / f"{prefix}archive_state.json"

        archive = cls()

        if not state_file.exists():
            return archive

        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            return archive

        canonical_dir = base_dir / f"{prefix}canonical"
        discovered_dir = base_dir / f"{prefix}discovered"

        for name, data in state.items():
            if data.get("is_canonical"):
                source_file = canonical_dir / f"{name}.py"
            else:
                source_file = discovered_dir / f"{name}.py"

            source = ""
            if source_file.exists():
                source = source_file.read_text()

            profile_file = base_dir / f"{prefix}profiles" / f"{name}.json"
            profile = data.get("profile", [])
            if not profile and profile_file.exists():
                try:
                    profile = json.loads(profile_file.read_text())
                except (json.JSONDecodeError, OSError):
                    pass

            sig_file = base_dir / f"{prefix}signatures" / f"{name}.json"
            beh_sig = data.get("behavioral_signature", [])
            if not beh_sig and sig_file.exists():
                try:
                    beh_sig = json.loads(sig_file.read_text())
                except (json.JSONDecodeError, OSError):
                    pass

            data["profile"] = profile
            data["behavioral_signature"] = beh_sig
            entry = ArchiveEntry.from_dict(data, source=source)
            archive.algorithms[name] = entry

        return archive
