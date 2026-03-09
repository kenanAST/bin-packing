# bin-packing: Claude Code Orchestration

## What This Is

An autonomous system that discovers novel online bin packing heuristics. **You (Claude Code) are the brain.** You generate candidate packing heuristics, and Python scripts evaluate them for correctness, quality (bin efficiency), novelty, and simplicity.

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
  --strategy anomaly_hunt --generation 1 --parents "best_fit+first_fit_decreasing"
```

## The Loop

Each generation:

1. **Run** `uv run python harness.py select-strategy` — returns JSON with strategy name, parent heuristic source code, and archive summary
2. **Think** — use the strategy (see below) to design a genuinely novel packing heuristic
3. **Write** the heuristic to `candidates/candidate_<gen>.py` — must define `def pack(items, capacity):` that returns a list of bins
4. **Run** `uv run python harness.py evaluate candidates/candidate_<gen>.py` — returns correctness, quality, novelty, simplicity scores
5. **If correct**, run `uv run python harness.py admit candidates/candidate_<gen>.py --strategy <name> --generation <N> --parents "<parent1>+<parent2>"`
6. **Repeat** — pick up the next generation

### Parallel Generation with Subagents

For throughput, spawn **3 subagents in parallel** per generation batch, each with a different strategy. Give each subagent:
- The strategy name and description
- Parent heuristic source code (from select-strategy)
- The archive summary
- Instructions to write their candidate to a unique file

Then evaluate all candidates sequentially (evaluation modifies archive state).

## Heuristic Requirements

Every candidate MUST:
- Define `def pack(items, capacity):` as the entry point
- Accept a list of floats (item sizes in (0, 1]) and a float capacity (1.0)
- Return a list of bins, where each bin is a list of floats (the items in that bin)
- Every item must appear in exactly one bin
- No bin's total may exceed capacity (with float tolerance)
- Handle edge cases: empty list, single item, item equal to capacity
- NOT use Python's built-in `sorted()` or `list.sort()` for the core packing decision (using them to pre-process items is fine)
- Include any helper functions before or nested inside `pack()`

### Example Output Format

```python
# Input: items = [0.5, 0.3, 0.8, 0.2], capacity = 1.0
# Valid output: [[0.5, 0.3, 0.2], [0.8]]
# (two bins: first has 1.0 total, second has 0.8)
```

## Creativity Strategies

When `select-strategy` returns a strategy, use these approaches:

### standard_mutation
Take the parent heuristic and modify it — change the bin selection rule, the ordering, the data structures, or any other aspect. Make it pack more efficiently or handle certain distributions better.

### anomaly_hunt
Look at the parent's performance profile table. Some distributions show very different efficiency. Ask: WHY does it waste bins on that distribution? What structural property of those items causes poor packing? Design a NEW heuristic that exploits whatever you discover.

### cross_domain
You get TWO parent heuristics with very different strategies. Find the deeper idea in each and merge them into a single unified approach. Do NOT simply run one then the other — create a genuinely hybrid mechanism.

### first_principles
Ignore all known packing heuristics. Reason from fundamentals:
- You have items with sizes in (0, 1]
- You need to assign each to a bin so no bin exceeds capacity 1.0
- You want to minimize the number of bins
- The sum of items / capacity gives a hard lower bound
- Items that pair well (sum close to 1.0) should share bins
Think about what mathematical properties of item distributions are unexploited.

### constraint_inject
Design a packing heuristic under an artificial constraint:
- No sorting of items allowed (pure online)
- O(1) extra space — can only track fixed number of open bins
- No floating point comparisons (only integer arithmetic after scaling)
- Items must be processed in a single pass with no lookahead
- Maximum 3 open bins at any time
- No explicit bin tracking — use mathematical placement rules

Pick one constraint, or use the one provided by select-strategy.

### distribution_aware
Design heuristics that detect properties of the item stream and adapt:
- Measure the distribution of item sizes seen so far
- Track statistics (mean, variance, histogram buckets)
- Switch between sub-strategies based on detected distribution type
- Use prediction of future items based on past items
This is where real-world competitive advantage lives.

### outsider_perspective
Think as a non-CS practitioner:
- WAREHOUSE MANAGER: spatial intuition, heavy things first, fill gaps
- TETRIS PLAYER: look for complementary shapes, avoid creating gaps
- CHEF: group ingredients by recipe, fill containers to the brim
- POSTAL WORKER: weight limits per bag, heavy parcels first, fill with letters
- ACCOUNTANT: maximize utilization rate per bin, track waste percentage

### novelty_search
Your ONLY goal is maximum structural difference from everything in the archive. It doesn't need to be efficient — just CORRECT and DIFFERENT. Use data structures, control flow, or mathematical properties nobody has tried.

## Scoring

- **Correctness**: Must pack all items into valid bins across 200+ test cases. Binary gate — fail this and nothing else matters.
- **Quality**: Ratio of lower_bound / bins_used across 10 distributions × 3 sizes. Score 0-1 (1.0 = matches optimal packing).
- **Novelty**: AST structural distance × behavioral distance vs all archive members. Score 0-1.
- **Simplicity**: Based on LOC, cyclomatic complexity, nesting depth. Score 0-1.
- **Combined**: quality × novelty × (0.7 + 0.3 × simplicity). This determines admission.

## Archive Admission

A candidate gets in if ANY of these hold:
1. **Pareto improvement** — not dominated on quality/novelty/simplicity by any existing member, AND dominates at least one
2. **Behavioral niche** — performance profile is sufficiently different from all existing members (cosine distance > 0.15)
3. **Structural niche** — AST structure is sufficiently different from all existing members (edit distance > 0.3)

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
| decreasing | 0.99 down to 0.01 | Arrival order matches FFD's ideal |
| increasing | 0.01 up to 0.99 | Worst case for greedy — small items arrive first, waste space |
| thirds | Items all ~0.30 | Exactly 3 fit per bin — precision matters |

## Tips for Generating Good Candidates

- Think about **item pairing**: which items sum close to capacity? How can you find good pairs efficiently?
- Think about **reservation**: should you keep some bins partially filled waiting for a good complement?
- Think about **thresholds**: items > 0.5 can never share a bin — handle them specially
- Think about **lookahead**: if you can see all items, how does that change the strategy?
- The **increasing** distribution is where most heuristics struggle — small items arrive first and get packed suboptimally
- **Adaptive** approaches that detect the distribution tend to score well on quality
- Very simple heuristics that find a behavioral niche tend to get admitted even if suboptimal
- Check the archive summary — if everything is greedy, try a mathematical/statistical approach
