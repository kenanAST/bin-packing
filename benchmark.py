#!/usr/bin/env python3
"""
Benchmark discovered heuristics against standard OR-Library instances.

Downloads Falkenauer bin packing instances (binpack1-8, 160 problems total)
and evaluates all archive heuristics + any specified candidates.

Usage:
    uv run python benchmark.py                    # benchmark all archive members
    uv run python benchmark.py candidates/c.py    # also benchmark a specific candidate
    uv run python benchmark.py --quick             # only binpack1 (20 problems, fast)
    uv run python benchmark.py --dataset or1       # specific dataset
    uv run python benchmark.py --json              # machine-readable output

OR-Library datasets:
    or1 (binpack1): 20 problems, 120 items, uniform(20,100), capacity 150
    or2 (binpack2): 20 problems, 250 items, uniform(20,100), capacity 150
    or3 (binpack3): 20 problems, 500 items, uniform(20,100), capacity 150
    or4 (binpack4): 20 problems, 1000 items, uniform(20,100), capacity 150
    or5 (binpack5): 20 problems, 60 items, triplets(25,50), capacity 100
    or6 (binpack6): 20 problems, 120 items, triplets(25,50), capacity 100
    or7 (binpack7): 20 problems, 249 items, triplets(25,50), capacity 100
    or8 (binpack8): 20 problems, 501 items, triplets(25,50), capacity 100
"""

import argparse
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

from archive import Archive
from evaluate import extract_and_compile


# ---------------------------------------------------------------------------
# OR-Library instance management
# ---------------------------------------------------------------------------

CACHE_DIR = Path("bench_data")
OR_BASE_URL = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files"

DATASETS = {
    "or1": "binpack1.txt",
    "or2": "binpack2.txt",
    "or3": "binpack3.txt",
    "or4": "binpack4.txt",
    "or5": "binpack5.txt",
    "or6": "binpack6.txt",
    "or7": "binpack7.txt",
    "or8": "binpack8.txt",
}

ALL_UNIFORM = ["or1", "or2", "or3", "or4"]
ALL_TRIPLET = ["or5", "or6", "or7", "or8"]


def download_dataset(name):
    """Download an OR-Library dataset if not cached."""
    CACHE_DIR.mkdir(exist_ok=True)
    filename = DATASETS[name]
    cache_path = CACHE_DIR / filename

    if cache_path.exists():
        return cache_path

    url = f"{OR_BASE_URL}/{filename}"
    print(f"  Downloading {url} ...", file=sys.stderr)
    urllib.request.urlretrieve(url, cache_path)
    return cache_path


def parse_or_library(filepath):
    """
    Parse an OR-Library bin packing file.

    Returns list of dicts:
        {"name": str, "capacity": int, "items": list[int], "optimal": int}
    """
    with open(filepath) as f:
        lines = [line.strip() for line in f if line.strip()]

    idx = 0
    num_problems = int(lines[idx]); idx += 1

    problems = []
    for _ in range(num_problems):
        name = lines[idx].strip(); idx += 1
        parts = lines[idx].split(); idx += 1
        capacity = int(float(parts[0]))
        num_items = int(float(parts[1]))
        optimal = int(float(parts[2]))

        items = []
        for _ in range(num_items):
            items.append(int(float(lines[idx]))); idx += 1

        problems.append({
            "name": name,
            "capacity": capacity,
            "items": items,
            "optimal": optimal,
        })

    return problems


# ---------------------------------------------------------------------------
# Lower bound (L2)
# ---------------------------------------------------------------------------

def l2_lower_bound(items, capacity):
    """L2 lower bound for bin packing."""
    total = sum(items)
    lb_sum = math.ceil(total / capacity)
    lb_large = sum(1 for x in items if x > capacity / 2)
    return max(lb_sum, lb_large, 1)


# ---------------------------------------------------------------------------
# Run a heuristic on a problem
# ---------------------------------------------------------------------------

def run_heuristic(pack_fn, items, capacity):
    """
    Run a packing heuristic on integer items.
    Normalizes items to (0, 1] floats, runs the heuristic, returns bin count.
    """
    if not items:
        return 0

    # Normalize items to fractions of capacity
    float_items = [item / capacity for item in items]

    try:
        result = pack_fn(float_items, 1.0)
    except Exception as e:
        return len(items)  # worst case

    if not isinstance(result, list):
        return len(items)

    # Validate
    bins_used = len([b for b in result if b])

    # Verify all items are packed (by count)
    total_packed = sum(len(b) for b in result)
    if total_packed != len(items):
        return -1  # signal invalid

    # Verify no bin overflows
    for b in result:
        if sum(b) > 1.0 + 1e-6:
            return -1  # signal invalid

    return bins_used


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark_heuristics(heuristics, dataset_names, verbose=True):
    """
    Run all heuristics on all problems in the specified datasets.

    Returns dict: {heuristic_name: {dataset: {problems, total_bins, total_optimal,
                                               total_lb, excess_pct, failures}}}
    """
    results = {name: {} for name in heuristics}

    for ds_name in dataset_names:
        filepath = download_dataset(ds_name)
        problems = parse_or_library(filepath)

        if verbose:
            n_items = problems[0]["items"].__len__() if problems else 0
            print(f"\n{'='*70}", file=sys.stderr)
            print(f"Dataset: {ds_name} ({DATASETS[ds_name]}) — "
                  f"{len(problems)} problems, ~{n_items} items each", file=sys.stderr)
            print(f"{'='*70}", file=sys.stderr)

        for h_name, pack_fn in heuristics.items():
            total_bins = 0
            total_optimal = 0
            total_lb = 0
            failures = 0

            for prob in problems:
                bins = run_heuristic(pack_fn, prob["items"], prob["capacity"])
                lb = l2_lower_bound(prob["items"], prob["capacity"])
                opt = prob["optimal"]

                if bins < 0:
                    failures += 1
                    bins = len(prob["items"])

                total_bins += bins
                total_optimal += opt
                total_lb += lb

            excess_vs_opt = (total_bins - total_optimal) / total_optimal * 100
            excess_vs_lb = (total_bins - total_lb) / total_lb * 100

            results[h_name][ds_name] = {
                "problems": len(problems),
                "total_bins": total_bins,
                "total_optimal": total_optimal,
                "total_lb": total_lb,
                "excess_vs_optimal_pct": round(excess_vs_opt, 2),
                "excess_vs_lb_pct": round(excess_vs_lb, 2),
                "failures": failures,
            }

    return results


def print_results(results, dataset_names):
    """Print results in a readable table."""
    # Header
    h_names = list(results.keys())
    col_width = max(22, max(len(n) for n in h_names) + 2)

    print(f"\n{'':=<{col_width + 2}}", end="")
    for ds in dataset_names:
        print(f"{'':=<16}", end="")
    print()

    header = f"{'Heuristic':<{col_width}}"
    for ds in dataset_names:
        header += f"  {ds:>12}"
    print(header)
    print(f"{'(excess % vs optimal)':<{col_width}}", end="")
    for ds in dataset_names:
        print(f"  {'':>12}", end="")
    print()

    print(f"{'':-<{col_width}}", end="")
    for ds in dataset_names:
        print(f"  {'':->12}", end="")
    print()

    # Sort by average excess
    def avg_excess(h_name):
        vals = [results[h_name][ds]["excess_vs_optimal_pct"]
                for ds in dataset_names if ds in results[h_name]]
        return sum(vals) / len(vals) if vals else 999

    for h_name in sorted(h_names, key=avg_excess):
        row = f"{h_name:<{col_width}}"
        for ds in dataset_names:
            if ds in results[h_name]:
                r = results[h_name][ds]
                excess = r["excess_vs_optimal_pct"]
                fail_mark = "*" if r["failures"] > 0 else ""
                row += f"  {excess:>10.2f}%{fail_mark}"
            else:
                row += f"  {'N/A':>12}"
        print(row)

    # Summary row
    print(f"{'':-<{col_width}}", end="")
    for ds in dataset_names:
        print(f"  {'':->12}", end="")
    print()

    row = f"{'AVG EXCESS':<{col_width}}"
    for ds in dataset_names:
        vals = [results[h][ds]["excess_vs_optimal_pct"]
                for h in h_names if ds in results[h]]
        avg = sum(vals) / len(vals) if vals else 0
        row += f"  {avg:>10.2f}%"
    print(row)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Benchmark bin packing heuristics on OR-Library instances")
    parser.add_argument("candidates", nargs="*", help="Additional candidate .py files to benchmark")
    parser.add_argument("--quick", action="store_true", help="Only benchmark on OR1 (fast)")
    parser.add_argument("--uniform", action="store_true", help="Only uniform instances (OR1-4)")
    parser.add_argument("--triplet", action="store_true", help="Only triplet instances (OR5-8)")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()), action="append",
                        help="Specific dataset(s) to benchmark")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--no-archive", action="store_true", help="Skip archive members, only benchmark candidates")

    args = parser.parse_args()

    # Determine which datasets to use
    if args.dataset:
        dataset_names = args.dataset
    elif args.quick:
        dataset_names = ["or1"]
    elif args.uniform:
        dataset_names = ALL_UNIFORM
    elif args.triplet:
        dataset_names = ALL_TRIPLET
    else:
        dataset_names = list(DATASETS.keys())

    # Collect heuristics to benchmark
    heuristics = {}

    # Load archive members
    if not args.no_archive:
        archive = Archive.load_or_create("archive/")
        if not archive.has_canonical():
            archive.seed_canonical("archive/canonical/")
            archive.save("archive/")

        for entry in archive.get_all_entries():
            pack_fn = extract_and_compile(entry.source)
            if pack_fn:
                heuristics[entry.name] = pack_fn

    # Load additional candidates
    for cand_path in args.candidates:
        if not os.path.exists(cand_path):
            print(f"Warning: {cand_path} not found, skipping", file=sys.stderr)
            continue
        with open(cand_path) as f:
            source = f.read()
        pack_fn = extract_and_compile(source)
        if pack_fn:
            name = Path(cand_path).stem
            heuristics[f">> {name}"] = pack_fn
        else:
            print(f"Warning: {cand_path} failed to compile, skipping", file=sys.stderr)

    if not heuristics:
        print("No heuristics to benchmark!", file=sys.stderr)
        sys.exit(1)

    print(f"Benchmarking {len(heuristics)} heuristics on {len(dataset_names)} datasets "
          f"({sum(20 for _ in dataset_names)} total problems)...", file=sys.stderr)

    results = benchmark_heuristics(heuristics, dataset_names, verbose=not args.json)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results, dataset_names)


if __name__ == "__main__":
    main()
