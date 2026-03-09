"""
Novelty measurement for bin packing heuristic candidates.

Two dimensions:
  - AST structural novelty (how different is the code?)
  - Behavioral novelty (how different is the packing behavior?)

Behavioral novelty uses a rich 270-element signature capturing bin fill
distributions, waste patterns, and item co-location — not just quality ratios.
"""

import ast
import math


# ---------------------------------------------------------------------------
# AST normalization and distance
# ---------------------------------------------------------------------------

def _normalize_ast(tree):
    """
    Strip variable names, string constants, and numeric literals
    to compare pure structure. Returns a list of (node_type, depth) tuples.
    """
    tokens = []

    def walk(node, depth=0):
        tokens.append((type(node).__name__, depth))
        for child in ast.iter_child_nodes(node):
            walk(child, depth + 1)

    walk(tree)
    return tokens


def _sequence_edit_distance(seq_a, seq_b, max_ops=500):
    """
    Compute edit distance between two sequences of (node_type, depth) tuples.
    Uses a bounded DP approach for efficiency.
    """
    n, m = len(seq_a), len(seq_b)

    if n > max_ops:
        step = n // max_ops
        seq_a = seq_a[::step]
        n = len(seq_a)
    if m > max_ops:
        step = m // max_ops
        seq_b = seq_b[::step]
        m = len(seq_b)

    prev = list(range(m + 1))
    curr = [0] * (m + 1)

    for i in range(1, n + 1):
        curr[0] = i
        for j in range(1, m + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev, curr = curr, prev

    max_dist = max(n, m)
    if max_dist == 0:
        return 0.0
    return prev[m] / max_dist


def ast_novelty(candidate_source, archive_sources):
    """
    How structurally different is this code from everything in the archive?
    Returns float in [0, 1]. Higher = more novel.
    """
    if not archive_sources:
        return 1.0

    try:
        candidate_tree = ast.parse(candidate_source)
        candidate_tokens = _normalize_ast(candidate_tree)
    except SyntaxError:
        return 0.0

    distances = []
    for arch_source in archive_sources:
        try:
            arch_tree = ast.parse(arch_source)
            arch_tokens = _normalize_ast(arch_tree)
            dist = _sequence_edit_distance(candidate_tokens, arch_tokens)
            distances.append(dist)
        except SyntaxError:
            continue

    if not distances:
        return 1.0

    return min(distances) if len(distances) == 1 else sorted(distances)[0]


# ---------------------------------------------------------------------------
# Behavioral novelty (rich behavioral signature distance)
# ---------------------------------------------------------------------------

def _cosine_distance(vec_a, vec_b):
    """Cosine distance between two vectors. Returns float in [0, 1].
    Legacy metric — kept for backward compatibility with old profiles."""
    if len(vec_a) != len(vec_b) or len(vec_a) == 0:
        return 1.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a < 1e-10 or norm_b < 1e-10:
        return 1.0

    similarity = dot / (norm_a * norm_b)
    similarity = max(-1.0, min(1.0, similarity))
    return (1.0 - similarity) / 2.0


def _euclidean_distance(sig_a, sig_b):
    """Euclidean distance on behavioral signatures, normalized to [0, 1].

    Unlike cosine distance on near-unit quality ratio vectors, Euclidean
    distance on rich behavioral signatures (bin fill distributions, waste
    patterns, co-location ratios) captures genuine behavioral differences.
    """
    if len(sig_a) != len(sig_b) or len(sig_a) == 0:
        return 1.0

    sq_sum = sum((a - b) ** 2 for a, b in zip(sig_a, sig_b))
    # Normalize: sqrt(mean squared diff). Each element is in [0, 1],
    # so max possible distance is 1.0 (all elements differ maximally).
    raw = math.sqrt(sq_sum / len(sig_a))
    return min(raw, 1.0)


def behavioral_novelty(candidate_sig, archive_sigs, candidate_profile=None, archive_profiles=None):
    """
    How different does this heuristic behave from everything in the archive?
    Returns float in [0, 1]. Higher = more novel.

    Uses rich behavioral signatures (Euclidean distance) as primary metric.
    Falls back to legacy cosine distance on quality profiles if signatures
    are not available.
    """
    # Primary: Euclidean distance on rich behavioral signatures
    if candidate_sig and archive_sigs:
        valid_sigs = [s for s in archive_sigs if s and len(s) == len(candidate_sig)]
        if valid_sigs:
            distances = [_euclidean_distance(candidate_sig, s) for s in valid_sigs]
            return min(distances)

    # Fallback: cosine distance on quality ratio profiles (legacy)
    if candidate_profile and archive_profiles:
        distances = [_cosine_distance(candidate_profile, p) for p in archive_profiles]
        return min(distances)

    return 1.0


# ---------------------------------------------------------------------------
# Combined novelty
# ---------------------------------------------------------------------------

def novelty_score(ast_nov, behavioral_nov):
    """Novelty combines structural AND behavioral difference.

    Uses max(geometric_mean, behavioral) so that high behavioral novelty
    alone can contribute, rather than being zeroed out by the product.
    """
    geo = (ast_nov * behavioral_nov) ** 0.5
    # Give behavioral novelty a floor proportional to AST novelty,
    # so structurally unique code that behaves slightly differently still scores
    return max(geo, behavioral_nov * 0.8)
