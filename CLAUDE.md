# bin-packing: Claude Code Orchestration

## What This Is

An autonomous system that discovers novel bin packing heuristics. **You (Claude Code) are the brain.** You generate candidate packing heuristics, and Python scripts evaluate them for correctness, quality (bin efficiency), novelty, and simplicity.

### Why Bin Packing?

Unlike sorting (which is theoretically solved), online bin packing has **open gaps**. The best known competitive ratio is ~1.73, with a lower bound of ~1.54. FunSearch (DeepMind) already proved LLM-evolved heuristics can beat classical approaches here. This is a domain where genuine algorithmic breakthroughs are possible.

## Quick Start

```bash
# Check archive status
uv run python harness.py status

# Get a strategy + parents for this generation
uv run python harness.py select-strategy

# Write a candidate to candidates/candidate_<gen>.py
# (YOU write the packing heuristic — that's the whole point)

# Evaluate it
uv run python harness.py evaluate candidates/candidate_001.py

# If correct, attempt archive admission
uv run python harness.py admit candidates/candidate_001.py \
  --strategy anomaly_hunt --generation 1 --parents "best_fit+first_fit"

# Analyze best heuristic's weaknesses
uv run python harness.py red-team

# Backfill behavioral signatures (run after code changes)
uv run python harness.py backfill
```

## The Loop

Each generation:

1. **Run** `uv run python harness.py select-strategy` — returns JSON with strategy name, parent source code, archive summary, **creativity prompt**, and **anti-convergence warnings**
2. **Read the creativity prompt** — it contains research-backed techniques to avoid mode collapse
3. **Think** — use the strategy AND the creativity prompt to design a genuinely novel heuristic
4. **Write** the heuristic to `candidates/candidate_<gen>.py`
5. **Run** `uv run python harness.py evaluate candidates/candidate_<gen>.py`
6. **If correct**, run `uv run python harness.py admit candidates/candidate_<gen>.py --strategy <name> --generation <N> --parents "<parent1>+<parent2>"`
7. **Repeat** — pick up the next generation

### Using Red-Team Analysis

Before designing new candidates, run `uv run python harness.py red-team` to see exactly WHERE and WHY the current best heuristic fails. This gives you specific distributions, arrival orders, bin counts, and fill patterns to target.

### Parallel Generation with Subagents

For throughput, spawn **3 subagents in parallel** per generation batch, each with a different strategy. Give each subagent:
- The strategy name, creativity prompt, and anti-convergence warnings
- Parent heuristic source code (from select-strategy)
- The archive summary
- Instructions to write their candidate to a unique file

Then evaluate all candidates sequentially (evaluation modifies archive state).

## Online Heuristic Requirements

Every online candidate MUST:
- Define `def create_packer(capacity):` that returns an object with:
  - `place(item) -> int` — assign an item to a bin, return the bin index
  - `get_bins() -> list[list[float]]` — return all bins with their contents
- Items arrive one at a time via `place()` — NO lookahead, NO reordering
- No bin's total may exceed capacity (with float tolerance)
- Handle edge cases: no items placed, single item, item equal to capacity
- `place()` must return an integer bin index for each item

### Example Online Heuristic

```python
def create_packer(capacity):
    """Example: Best Fit — place item in fullest bin that still fits."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []

        def place(self, item):
            best_idx = -1
            best_remaining = capacity + 1
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item <= remaining + 1e-9 and remaining < best_remaining:
                    best_remaining = remaining
                    best_idx = i
            if best_idx >= 0:
                self.bins[best_idx].append(item)
                self.bin_sums[best_idx] += item
                return best_idx
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
```

## Creativity Strategies

When `select-strategy` returns a strategy, use these approaches. **The `creativity_prompt` field in the JSON output contains specific research-backed instructions — follow them.**

### standard_mutation
Take the parent heuristic and modify it — change the bin selection rule, the data structures, or any other aspect. **Verbalized sampling**: before coding, list 5 possible mutations with probability estimates. Develop the one you rate lowest probability.

### anomaly_hunt
Look at the parent's performance profile table. Some distributions show very different efficiency. Ask: WHY does it waste bins on that distribution? **Use 5-Whys root cause analysis**: don't stop at "it wastes space" — ask WHY five times.

### cross_domain
You get TWO parent heuristics with very different strategies. **Analogical mapping**: identify the ABSTRACT PRINCIPLE behind each parent (not its code). Synthesize a new principle that neither parent embodies alone.

### first_principles
Ignore all known packing heuristics. Reason from fundamentals. **Constraint relaxation**: list 5 implicit assumptions ALL bin packing heuristics make. Violate at least 2. What algorithm emerges?

### constraint_inject
Design a heuristic under an artificial constraint (e.g., max 3 open bins, no floating point, single pass). The constraint forces discovery of structures unconstrained algorithms would never find.

### distribution_aware
Design heuristics that detect properties of the item stream and adapt. **Prediction-driven**: don't just detect the distribution — predict what items will arrive next.

### outsider_perspective
**Research shows ordinary personas beat celebrity personas for creativity.** Think as a specific non-expert: a kindergarten teacher, a Tetris speedrunner, a postal worker who's sorted mail for 30 years.

### novelty_search
Your ONLY goal is maximum structural AND behavioral difference from everything in the archive. Use programming constructs nobody has tried.

## Anti-Convergence Rules

**CRITICAL: Read these before every generation.**

1. If the archive has > 5 members with quality > 0.90, DO NOT generate another simple Best Fit/First Fit variant
2. If your candidate is structurally similar to existing archive members, focus on behavioral novelty
3. Quality 0.88 with genuine behavioral novelty is MORE VALUABLE than quality 0.92 without any
4. The `select-strategy` output includes an `anti_convergence` field listing over-represented patterns. AVOID these patterns.
5. Before coding, ask: "Would a CS professor look at this and say 'that's obvious'?" If yes, make it weirder.

## Scoring

- **Correctness**: Must pack all items into valid bins across 200+ test cases. Binary gate — fail this and nothing else matters.
- **Quality**: Ratio of lower_bound / bins_used across distributions × sizes (× arrival orders for online). Score 0-1.
- **Novelty**: Combines AST structural distance and behavioral distance. Behavioral distance uses a rich 864-element signature capturing bin fill distributions, waste patterns, and item co-location.
- **Simplicity**: Based on LOC, cyclomatic complexity, nesting depth. Score 0-1.
- **Combined**: quality × novelty × (0.7 + 0.3 × simplicity). This determines admission.

## Archive Admission

A candidate gets in if ANY of these hold:
1. **Pareto improvement** — not dominated on quality/novelty/simplicity by any existing member, AND dominates at least one
2. **Behavioral niche** — behavioral signature is sufficiently different (Euclidean distance > 0.05). This measures HOW you pack, not just how well.
3. **Structural niche** — AST structure is sufficiently different (edit distance > 0.3)

## Online Evaluation Details

Online heuristics are tested across:
- **8 distributions**: uniform_small, uniform_medium, uniform_large, uniform_full, bimodal, trimodal, heavy_tail, thirds
- **4 arrival orders**: random, increasing, decreasing, oscillating
- **3 sizes**: 50, 200, 1000 items

Total: 96 test cases per evaluation. Arrival order matters hugely — a heuristic that excels on decreasing order may fail badly on increasing.

### Key Online Challenges

- **No sorting**: You can't sort items — they arrive in whatever order
- **Increasing order** is the hardest: small items arrive first, get packed suboptimally, then large items can't pair with them
- **Oscillating order** alternates large/small — tests whether you can pair them in real-time
- **State management**: What statistics do you track about items seen so far?
- **Reservation**: Should you keep bins partially filled hoping for a good complement?

### Competitive Ratio Targets

- Next Fit: ~2.0 (worst canonical, easiest to beat)
- First Fit / Best Fit: ~1.7 (strong baselines)
- Harmonic: ~1.69 (theoretical near-optimal for worst case)
- **Target**: Find heuristics that beat Best Fit on average across distributions while maintaining correctness

## Distributions Tested

| Distribution | Description | What makes it hard? |
|---|---|---|
| uniform_small | Items in [0.01, 0.30] | Many items fit per bin — packing order matters a lot |
| uniform_medium | Items in [0.10, 0.60] | Mix of sizes, pairing opportunities |
| uniform_large | Items in [0.30, 0.90] | Few items per bin, wasted space |
| uniform_full | Items in [0.01, 0.99] | Full range, must handle all sizes |
| bimodal | Small (0.05-0.20) or large (0.60-0.90) | Pairing small+large is critical |
| trimodal | Three clusters | Complex pairing across three groups |
| heavy_tail | Pareto-distributed | Rare huge items, many tiny ones |
| thirds | Items all ~0.30 | Exactly 3 fit per bin — precision matters |

## Tips for Generating Good Online Candidates

- **Track running statistics**: mean, variance, distribution shape of items seen so far
- **Reservation strategy**: keep some bins partially filled waiting for good complements
- **Size classes**: handle items > 0.5 specially (they can never share a bin with another > 0.5)
- **Adaptive thresholds**: change behavior based on how many items you've seen
- **The increasing distribution** is where most heuristics struggle — design for this case
- **Pair complementary items**: if you see a 0.3, anticipate a 0.7 coming later
- **Run red-team analysis** before designing to know exactly where to aim
