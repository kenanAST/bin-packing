"""
Evaluation harness for ONLINE bin packing heuristic candidates.

Online heuristics receive items one at a time via place(item) and must
assign each item immediately without knowledge of future items.

Interface: create_packer(capacity) -> object with place(item) and get_bins()
"""

import ast
import math
import random
import time
from math import exp, log


# ---------------------------------------------------------------------------
# Item generation distributions + arrival orders
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
    "thirds":          lambda n, rng: [rng.uniform(0.26, 0.34) for _ in range(n)],
}

ARRIVAL_ORDERS = {
    "random":      lambda items, rng: _shuffle(items, rng),
    "increasing":  lambda items, rng: sorted(items),
    "decreasing":  lambda items, rng: sorted(items, reverse=True),
    "oscillating": lambda items, rng: _oscillate(items),
}

SIZES = [50, 200, 1000]

BIN_CAPACITY = 1.0


def _shuffle(items, rng):
    lst = list(items)
    rng.shuffle(lst)
    return lst


def _oscillate(items):
    """Alternate between large and small items."""
    s = sorted(items)
    result = []
    lo, hi = 0, len(s) - 1
    toggle = True
    while lo <= hi:
        if toggle:
            result.append(s[hi])
            hi -= 1
        else:
            result.append(s[lo])
            lo += 1
        toggle = not toggle
    return result


# ---------------------------------------------------------------------------
# Lower bound computation
# ---------------------------------------------------------------------------

def _lower_bound(items):
    """L2 lower bound: max(ceil(sum), count of items > 0.5, ...)"""
    total = sum(items)
    lb_sum = math.ceil(total)
    lb_large = sum(1 for x in items if x > 0.5)
    return max(lb_sum, lb_large, 1)


def _ffd_bins(items, capacity=1.0):
    """First Fit Decreasing -- tight offline upper bound for reference."""
    s = sorted(items, reverse=True)
    bins = []
    sums = []
    for item in s:
        placed = False
        for i in range(len(bins)):
            if sums[i] + item <= capacity + 1e-9:
                bins[i].append(item)
                sums[i] += item
                placed = True
                break
        if not placed:
            bins.append([item])
            sums.append(item)
    return len([b for b in bins if b])


# ---------------------------------------------------------------------------
# Candidate extraction
# ---------------------------------------------------------------------------

def extract_online_packer(source_code):
    """Extract create_packer from source code and return factory callable."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None

    has_create_packer = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "create_packer":
            has_create_packer = True
            break

    if not has_create_packer:
        return None

    namespace = {}
    try:
        compiled = compile(tree, "<candidate>", "exec")
        # Intentional: this is the core mechanism of the discovery system.
        # Candidates run in an isolated namespace.
        exec(compiled, namespace)  # noqa: S102
    except Exception:
        return None

    factory = namespace.get("create_packer")
    if factory is None or not callable(factory):
        return None

    # Verify the factory returns an object with place() and get_bins()
    try:
        test_packer = factory(1.0)
        if not hasattr(test_packer, 'place') or not hasattr(test_packer, 'get_bins'):
            return None
        if not callable(test_packer.place) or not callable(test_packer.get_bins):
            return None
    except Exception:
        return None

    return factory


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------

def evaluate_correctness(packer_factory, trials=200):
    """
    Returns True only if the packer works correctly on ALL trials.

    Online correctness:
    - place(item) returns an integer for each item
    - get_bins() returns valid bins after all items placed
    - Every item appears exactly once, no bin exceeds capacity
    """
    rng = random.Random(42)

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

    for _ in range(trials):
        n = rng.randint(0, 500)
        items = [round(rng.uniform(0.01, 0.99), 6) for _ in range(n)]
        test_cases.append(items)

    for items in test_cases:
        try:
            packer = packer_factory(BIN_CAPACITY)

            for item in items:
                idx = packer.place(item)
                if not isinstance(idx, int):
                    return False

            result = packer.get_bins()
        except Exception:
            return False

        if not isinstance(result, list):
            return False

        if len(items) == 0:
            non_empty = [b for b in result if b]
            if non_empty:
                return False
            continue

        packed_items = []
        for bin_contents in result:
            if not isinstance(bin_contents, list):
                return False
            for item in bin_contents:
                if not isinstance(item, (int, float)):
                    return False
                packed_items.append(item)

        if sorted(packed_items) != sorted(items):
            return False

        for bin_contents in result:
            if sum(bin_contents) > BIN_CAPACITY + 1e-9:
                return False

    return True


# ---------------------------------------------------------------------------
# Quality (distributions x orders x sizes)
# ---------------------------------------------------------------------------

def evaluate_quality(packer_factory):
    """
    Returns (quality_score, profile_vector, behavioral_signature).

    Tests across 8 distributions x 4 arrival orders x 3 sizes = 96 cases.
    Quality = geometric mean of (lower_bound / bins_used).
    """
    rng = random.Random(123)
    ratios = []
    signature = []

    for dist_name, gen in DISTRIBUTIONS.items():
        for size in SIZES:
            for order_name, reorder in ARRIVAL_ORDERS.items():
                items = gen(size, rng)
                items = [max(0.01, min(0.99, x)) for x in items]

                lb = _lower_bound(items)

                order_rng = random.Random(rng.randint(0, 2**31))
                ordered_items = reorder(items, order_rng)

                try:
                    packer = packer_factory(BIN_CAPACITY)
                    for item in ordered_items:
                        packer.place(item)
                    result = packer.get_bins()
                    bins = [b for b in result if b]
                    bins_used = len(bins)
                except Exception:
                    bins_used = len(items)
                    bins = [[x] for x in items]

                ratio = lb / max(bins_used, 1)
                ratios.append(min(ratio, 1.0))

                # --- Behavioral signature ---
                n_items = max(len(items), 1)
                n_bins = max(bins_used, 1)
                fills = [sum(b) / BIN_CAPACITY for b in bins] if bins else [0.0]

                signature.append(bins_used / n_items)
                signature.append(sum(1 for f in fills if f > 0.95) / n_bins)
                signature.append(sum(1 for f in fills if 0.80 < f <= 0.95) / n_bins)
                signature.append(sum(1 for f in fills if 0.50 < f <= 0.80) / n_bins)
                signature.append(sum(1 for f in fills if f <= 0.50) / n_bins)
                wastes = [1.0 - f for f in fills]
                mean_waste = sum(wastes) / n_bins
                var_waste = sum((w - mean_waste) ** 2 for w in wastes) / n_bins
                signature.append(mean_waste)
                signature.append(math.sqrt(var_waste))
                large_small = sum(1 for b in bins
                                  if any(x > 0.5 for x in b) and any(x < 0.25 for x in b))
                large_only = sum(1 for b in bins
                                 if any(x > 0.5 for x in b) and not any(x < 0.25 for x in b))
                signature.append(large_small / n_bins)
                signature.append(large_only / n_bins)

    geo_mean = exp(sum(log(max(r, 1e-10)) for r in ratios) / len(ratios))
    quality = min(geo_mean, 1.0)

    return quality, ratios, signature


# ---------------------------------------------------------------------------
# Simplicity (same as offline)
# ---------------------------------------------------------------------------

def _max_nesting_depth(node, current=0):
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.If, ast.With,
                              ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)):
            max_depth = max(max_depth, _max_nesting_depth(child, current + 1))
        else:
            max_depth = max(max_depth, _max_nesting_depth(child, current))
    return max_depth


def _cyclomatic_complexity(tree):
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


def simplicity_score(source_code):
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
    if not correctness:
        return 0.0
    qn_score = quality * novelty
    return qn_score * (0.7 + 0.3 * simplicity)


# ---------------------------------------------------------------------------
# Full evaluation pipeline
# ---------------------------------------------------------------------------

def evaluate_candidate(source_code, archive, timeout=180):
    """Full evaluation pipeline for an online packing candidate."""
    from novelty import ast_novelty, behavioral_novelty, novelty_score

    packer_factory = extract_online_packer(source_code)
    if packer_factory is None:
        return {"correctness": False, "reason": "compile_error"}

    if not evaluate_correctness(packer_factory):
        return {"correctness": False, "reason": "incorrect_output"}

    quality, profile, behavioral_sig = evaluate_quality(packer_factory)

    all_sources = archive.get_all_sources()
    all_profiles = archive.get_all_profiles()
    all_signatures = archive.get_all_behavioral_signatures()
    ast_nov = ast_novelty(source_code, all_sources)
    beh_nov = behavioral_novelty(behavioral_sig, all_signatures, profile, all_profiles)
    novelty = novelty_score(ast_nov, beh_nov)

    simpl = simplicity_score(source_code)
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
        "behavioral_signature": behavioral_sig,
    }
