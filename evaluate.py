"""
Evaluation harness for online bin packing heuristic candidates.

Scores candidates on correctness, quality (bin count vs lower bound),
and simplicity.
DO NOT MODIFY -- this is the fixed evaluation function.
"""

import ast
import math
import random
import sys
import time
from math import exp, log


# ---------------------------------------------------------------------------
# Item generation distributions
# ---------------------------------------------------------------------------

DISTRIBUTIONS = {
    "uniform_small":   lambda n, rng: [rng.uniform(0.01, 0.30) for _ in range(n)],
    "uniform_medium":  lambda n, rng: [rng.uniform(0.10, 0.60) for _ in range(n)],
    "uniform_large":   lambda n, rng: [rng.uniform(0.30, 0.90) for _ in range(n)],
    "uniform_full":    lambda n, rng: [rng.uniform(0.01, 0.99) for _ in range(n)],
    "bimodal":         lambda n, rng: [rng.choice([rng.uniform(0.05, 0.20),
                                                    rng.uniform(0.60, 0.90)]) for _ in range(n)],
    "trimodal":        lambda n, rng: [rng.choice([rng.uniform(0.01, 0.10),
                                                    rng.uniform(0.25, 0.40),
                                                    rng.uniform(0.60, 0.80)]) for _ in range(n)],
    "heavy_tail":      lambda n, rng: [min(0.99, rng.paretovariate(1.5) * 0.05) for _ in range(n)],
    "decreasing":      lambda n, rng: [max(0.01, 0.99 - i / n) for i in range(n)],
    "increasing":      lambda n, rng: [min(0.99, 0.01 + i / n) for i in range(n)],
    "thirds":          lambda n, rng: [rng.uniform(0.26, 0.34) for _ in range(n)],
}

SIZES = [50, 200, 1000]

BIN_CAPACITY = 1.0


# ---------------------------------------------------------------------------
# Lower bound computation
# ---------------------------------------------------------------------------

def _lower_bound(items):
    """L2 lower bound: max(ceil(sum), count of items > 0.5, ...)"""
    total = sum(items)
    lb_sum = math.ceil(total)
    lb_large = sum(1 for x in items if x > 0.5)
    return max(lb_sum, lb_large, 1)


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------

def evaluate_correctness(pack_fn, trials=200):
    """
    Returns True only if the function packs correctly on ALL trials.

    Correctness means:
    - Returns a list of bins (each bin is a list of floats)
    - Every item appears exactly once across all bins
    - No bin exceeds capacity (1.0)
    """
    rng = random.Random(42)

    # Fixed edge cases
    test_cases = [
        [],
        [0.5],
        [1.0],
        [0.01],
        [0.5, 0.5],
        [0.5, 0.5, 0.5],
        [0.3, 0.3, 0.3, 0.3],
        [0.9, 0.9, 0.9],
        [0.1] * 20,
        [0.99] * 5,
        [0.5, 0.3, 0.2, 0.8, 0.1, 0.6, 0.4, 0.7],
        [0.01] * 100,
        [0.49, 0.51],
        [0.33, 0.33, 0.34],
        [0.25, 0.25, 0.25, 0.25],
    ]

    # Random test cases
    for _ in range(trials):
        n = rng.randint(0, 500)
        items = [round(rng.uniform(0.01, 0.99), 6) for _ in range(n)]
        test_cases.append(items)

    for items in test_cases:
        try:
            result = pack_fn(list(items), BIN_CAPACITY)
        except Exception:
            return False

        # Must return a list of bins
        if not isinstance(result, list):
            return False

        # Empty input
        if len(items) == 0:
            if len(result) != 0 and result != [[]]:
                all_empty = all(len(b) == 0 for b in result)
                if not all_empty:
                    return False
            continue

        # Flatten all bins
        packed_items = []
        for bin_contents in result:
            if not isinstance(bin_contents, list):
                return False
            for item in bin_contents:
                if not isinstance(item, (int, float)):
                    return False
                packed_items.append(item)

        # Every item must appear exactly once (by value, sorted comparison)
        if sorted(packed_items) != sorted(items):
            return False

        # No bin exceeds capacity (with small tolerance for float rounding)
        for bin_contents in result:
            if sum(bin_contents) > BIN_CAPACITY + 1e-9:
                return False

    return True


# ---------------------------------------------------------------------------
# Quality (performance profile)
# ---------------------------------------------------------------------------

def evaluate_quality(pack_fn):
    """
    Returns (quality_score, profile_vector).
    quality_score in [0, 1]. 1.0 = matches optimal bin count.
    profile_vector is a list of ratios (lower_bound / bins_used).
    """
    rng = random.Random(123)
    ratios = []

    for dist_name, gen in DISTRIBUTIONS.items():
        for size in SIZES:
            items = gen(size, rng)
            # Clamp items to valid range
            items = [max(0.01, min(0.99, x)) for x in items]

            try:
                result = pack_fn(list(items), BIN_CAPACITY)
                bins_used = len([b for b in result if b])  # non-empty bins
            except Exception:
                bins_used = len(items)  # worst case: 1 item per bin

            lb = _lower_bound(items)
            ratio = lb / max(bins_used, 1)  # 1.0 = optimal, lower = worse
            ratios.append(min(ratio, 1.0))

    # Geometric mean of ratios
    geo_mean = exp(sum(log(max(r, 1e-10)) for r in ratios) / len(ratios))
    quality = min(geo_mean, 1.0)

    return quality, ratios


# ---------------------------------------------------------------------------
# Simplicity
# ---------------------------------------------------------------------------

def _max_nesting_depth(node, current=0):
    """Compute maximum nesting depth of an AST."""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.If, ast.With,
                              ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)):
            max_depth = max(max_depth, _max_nesting_depth(child, current + 1))
        else:
            max_depth = max(max_depth, _max_nesting_depth(child, current))
    return max_depth


def _cyclomatic_complexity(tree):
    """Approximate cyclomatic complexity."""
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


def simplicity_score(source_code):
    """Simpler code scores higher. Returns float in [0, 1]."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return 0.0

    loc = len([n for n in ast.walk(tree) if isinstance(n, ast.stmt)])
    cyclomatic = _cyclomatic_complexity(tree)
    max_depth = _max_nesting_depth(tree)

    loc_score = max(0.0, 1.0 - loc / 100)
    cc_score = max(0.0, 1.0 - cyclomatic / 30)
    depth_score = max(0.0, 1.0 - max_depth / 10)

    return (loc_score * cc_score * depth_score) ** (1 / 3)


# ---------------------------------------------------------------------------
# Combined scoring
# ---------------------------------------------------------------------------

def combined_score(correctness, quality, novelty, simplicity):
    """The score that determines keep/discard."""
    if not correctness:
        return 0.0
    qn_score = quality * novelty
    return qn_score * (0.7 + 0.3 * simplicity)


# ---------------------------------------------------------------------------
# Candidate extraction
# ---------------------------------------------------------------------------

def extract_and_compile(source_code):
    """
    Extract the pack function from source code and return a callable.
    Returns None if the code is invalid.

    The function must be named 'pack' and accept (items, capacity).

    NOTE: Intentionally executes candidate code -- this is the core mechanism
    of the algorithm discovery system. Candidates run in an isolated namespace.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None

    # Find the pack function
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "pack":
            break
    else:
        return None

    namespace = {}
    try:
        compiled = compile(tree, "<candidate>", "exec")
        exec(compiled, namespace)  # noqa: S307
    except Exception:
        return None

    fn = namespace.get("pack")
    if fn is None or not callable(fn):
        return None
    return fn


def evaluate_candidate(source_code, archive, timeout=180):
    """
    Full evaluation pipeline.
    Returns scores dict or None if invalid.
    """
    from novelty import ast_novelty, behavioral_novelty, novelty_score

    # 1. Extract and compile
    pack_fn = extract_and_compile(source_code)
    if pack_fn is None:
        return {"correctness": False, "reason": "compile_error"}

    # 2. Correctness gate
    if not evaluate_correctness(pack_fn):
        return {"correctness": False, "reason": "incorrect_output"}

    # 3. Quality (bin efficiency profile)
    quality, profile = evaluate_quality(pack_fn)

    # 4. Novelty (against archive)
    all_sources = archive.get_all_sources()
    all_profiles = archive.get_all_profiles()
    ast_nov = ast_novelty(source_code, all_sources)
    beh_nov = behavioral_novelty(profile, all_profiles)
    novelty = novelty_score(ast_nov, beh_nov)

    # 5. Simplicity
    simpl = simplicity_score(source_code)

    # 6. Combined
    combined = combined_score(True, quality, novelty, simpl)

    return {
        "correctness": True,
        "quality": quality,
        "novelty": novelty,
        "ast_novelty": ast_nov,
        "behavioral_novelty": beh_nov,
        "simplicity": simpl,
        "combined": combined,
        "profile": profile,
    }
