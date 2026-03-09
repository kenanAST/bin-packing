"""
Novelty measurement for bin packing heuristic candidates.

Two dimensions:
  - AST structural novelty (how different is the code?)
  - Behavioral novelty (how different is the performance profile?)
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
# Behavioral novelty (performance profile distance)
# ---------------------------------------------------------------------------

def _cosine_distance(vec_a, vec_b):
    """Cosine distance between two vectors. Returns float in [0, 1]."""
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


def behavioral_novelty(candidate_profile, archive_profiles):
    """
    How different does this heuristic behave from everything in the archive?
    Returns float in [0, 1]. Higher = more novel.
    """
    if not archive_profiles:
        return 1.0

    distances = []
    for arch_profile in archive_profiles:
        dist = _cosine_distance(candidate_profile, arch_profile)
        distances.append(dist)

    return min(distances)


# ---------------------------------------------------------------------------
# Combined novelty
# ---------------------------------------------------------------------------

def novelty_score(ast_nov, behavioral_nov):
    """Novelty requires BOTH structural AND behavioral difference."""
    return (ast_nov * behavioral_nov) ** 0.5
