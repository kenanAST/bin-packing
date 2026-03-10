# Diamond Hunt: Mitigating Needle-in-Haystack Search via Innovation Research

**Date**: 2026-03-10
**Context**: Applied ideas from steering-agents-for-innovation research to the bin-packing heuristic discovery project.

## The Problem

The bin-packing search had converged to a single point:
- 88/94 non-canonical heuristics descend from `best_fit` — single-lineage evolution
- 40%+ share the exact same code pattern (`bin_sums` as parallel tracking list)
- Top performers exploit an evaluation loophole (buffering items for offline FFD) — not genuinely online
- The genuine online frontier is 0.9169 — barely above canonical best_fit (0.9167). 27 generations produced **zero improvement** on the actual problem.
- Quality plateaus around 0.97 with diminishing returns
- The search space is enormous but the search kept revisiting the same region

## Root Cause Analysis

Three structural forces push toward the same region of solution space:

1. **LLM convergence bias** — MLE training means Claude gravitates toward "most likely" bin-packing patterns. Every generation drifts back toward best-fit variants.
2. **Quality-first scoring** — Combined score = quality × novelty × simplicity means a 0.97-quality conventional solution beats a 0.88-quality genuinely novel one. The scoring landscape is a deep basin around "slightly improved best fit."
3. **Parent-child inheritance** — Most strategies mutate parents. Mutations explore the neighborhood of what exists, not the vast unexplored space.

**Key reframe**: The search space isn't uniformly empty. The search keeps looking in the same corner.

## The Approach: Three-Phase Agent Team Architecture

### Phase 1: Intelligence Gathering (3 parallel agents)

**Agent 1: Red Team** — Analyzed archive for failure modes and blind spots
- Found the evaluation loophole (batch-FFD cheating)
- Identified 5 specific failure modes
- Mapped over-represented patterns and never-tried approaches

**Agent 2: Niche Mapper** — Analyzed 864-element behavioral signatures to find empty MAP-Elites cells
- Found 7 completely empty behavioral niches
- Most striking: 0/99 heuristics do better on increasing than decreasing order
- Identified that uniform_medium/increasing is the weakest cell (median 0.743)

**Agent 3: Assumption Auditor** — Read 24 heuristics to find shared invisible constraints
- Found 10 assumptions shared by 83-100% of all heuristics
- Key ones: no item movement, no cross-bin reasoning, O(n) flat scan, no phase-based strategies

### Phase 2: Targeted Exploration (5 parallel agents)

Each agent received:
- A **specific empty niche** to target (MAP-Elites principle)
- **Specific assumptions to violate** (constraint injection)
- A **structurally different reasoning strategy** (DMAD principle)
- Explicit instruction that **novelty matters more than quality** (novelty search)

### Phase 3: Evaluation and Admission

Sequential evaluation of all candidates against the archive.

## 7 Empty Behavioral Niches Discovered

| Niche | Occupants | Why It Matters |
|---|---|---|
| Better on increasing than decreasing order | **0/99** | Every heuristic has the same weakness |
| Thirds distribution > 0.91 | **0/99** | Hard ceiling nobody has cracked |
| Oscillating > random order | **1/99** | Natural pairing opportunity ignored |
| Uniform_medium/increasing > 0.90 | **5/99** (same family) | Weakest cell, median 0.743 |
| High waste-variance + good quality | **0/99** | Entire architectural class untried |
| Trimodal/increasing specialist | **4/99** (same family) | Regime-change detection needed |
| Large-item specialist (trade small perf) | **0/99** | No specialist heuristics exist |

## 10 Shared Assumptions (83-100% of archive)

| # | Assumption | Shared By | Potential Impact |
|---|-----------|-----------|-----------------|
| 1 | Items never move after placement | 100% | Unlocks near-offline quality in online setting |
| 2 | Bins scored independently, no cross-bin reasoning | 96% | Avoids "orphan gap" creation |
| 3 | O(n) flat scan of all bins per item | 92% | Enables O(log n) queries + structural insight |
| 4 | Bin represented only by total fill, not composition | 92% | Enables composition-aware matching |
| 5 | No principled use of 1/k mathematical structure | 83% | Exploits optimal theoretical packing classes |
| 6 | Stationary or slowly-adapting decision function | 83% | Distinct phase-optimal strategies |
| 7 | All bins always remain open/searchable | 96% | Bounded active set, forced commitment |
| 8 | No per-bin temporal/sequence information used | 100% | Stagnation-aware urgency scoring |
| 9 | Items treated as continuous floats, never discretized | 92% | O(1) hash-based complement lookup |
| 10 | No probabilistic model of future gap fillability | 88% | One-step lookahead / Bellman-style decisions |

## Phase 2 Results: 5 Candidates Generated and Admitted

| Team | Candidate | Quality | Novelty | Combined | Key Innovation |
|---|---|---|---|---|---|
| 1: Increasing Specialist | 301 | 0.864 | 0.258 | 0.175 | Phase-based fill caps — caps bins at 0.35 during spread phase, reserving room for large items. Achieves perfect 1.0 ratio on bimodal/increasing (vs best-fit's 0.88) |
| 2: Thirds Breaker | 302 | 0.914 | 0.181 | 0.135 | Count-penalized worst-fit with layer promotion. Discovered that 0.91 on thirds is a mathematical impossibility (theoretical max is 0.9075) |
| 3: Gap Fillability | 303 | 0.912 | 0.274 | 0.148 | Histogram-based demand scoring — scores bins by how FILLABLE the resulting gap is, not how tight the fit is. First heuristic to model P(gap filled) |
| 4: Bin Lifecycle | 304 | 0.891 | 0.274 | 0.212 | Bounded active set (max 40 bins) + stagnation tracking + auto-close at 86%. First heuristic with bin lifecycle management |
| 5: Hash Complement | 305 | 0.806 | 0.331 | 0.217 | Dict-based O(1) capacity lookup with strategic probes. No linear scan at all — probes specific target capacities, opens new bin if no probe hits |

## What the Research Predicted vs What Happened

1. **MAP-Elites / behavioral niching** worked — targeting empty niches produced higher combined scores (0.135-0.217) than the archive median, because novelty was high by construction.

2. **DMAD (diverse reasoning strategies)** worked — each agent used a structurally different reasoning approach (first principles, constraint injection, anomaly hunt, outsider perspective, frame reversal), and each produced genuinely different code architectures.

3. **Constraint injection** worked — Team 5's "no linear scan" constraint forced a completely novel data structure (dict-based probe). Team 4's "bounded active set" constraint created bin lifecycle management.

4. **Verbalized sampling** worked — Team 1 listed 5 approaches, picked the lowest-probability one (fill caps), and it produced the most dramatic behavioral change (perfect packing on bimodal/increasing).

5. **Novelty as first-class objective** worked — by explicitly telling agents "0.85 quality with genuine novelty beats 0.95 without it," they explored rather than exploiting.

## The Meta-Insight: Why This Mitigates Needle-in-Haystack

The core problem isn't that diamonds are rare — it's that the search keeps looking in the same place. The mitigation is a three-step process:

1. **Map the unexplored space** (Phase 1) — Red team + niche mapping + assumption audit reveals WHERE you haven't looked
2. **Send structurally diverse teams to specific empty regions** (Phase 2) — Each team has a different reasoning architecture AND a specific niche target
3. **Reward novelty independently from quality** — A heuristic that scores 0.806 quality but 0.331 novelty (Team 5) is more valuable than another 0.97 best-fit variant, because it expands the frontier

The Pacific Ocean metaphor is wrong. You're not searching randomly — you're partitioning the ocean into grid cells, identifying which cells have never been sampled, and sending specialized submersibles to each one. The diamonds aren't uniformly distributed; they cluster in the regions your current methods structurally cannot reach.

## Bonus Finding

Team 2 discovered that the thirds ceiling at 0.91 is a **mathematical impossibility**, not a search failure. Items in [0.26, 0.34] fit at most 3 per bin (4 × 0.26 = 1.04 > 1.0), so the theoretical max ratio is 0.9075. This redirects future effort away from a provably impossible target — exactly the kind of insight the research predicts (sometimes the most valuable output is discovering the problem is structured differently than assumed).

## Research Techniques Applied (Ranked by Impact)

| Rank | Technique | Source File | How Applied | Result |
|---|---|---|---|---|
| 1 | MAP-Elites / behavioral niching | ai-agent-creativity-innovation-research.md | Niche mapper agent identified empty cells | All 5 candidates targeted unexplored niches |
| 2 | DMAD (diverse multi-agent debate) | ai-agent-creativity-innovation-research.md | 5 agents with structurally different reasoning | 5 genuinely different architectures produced |
| 3 | Constraint injection | llm-innovation-discovery-research.md | Each agent had specific assumptions to violate | Novel data structures and control flow emerged |
| 4 | Verbalized sampling | ai-agent-creativity-innovation-research.md | Team 1 listed 5 options, picked lowest-probability | Most dramatic behavioral change (fill caps) |
| 5 | Novelty search (Stanley) | ai-agent-creativity-innovation-research.md | Explicit instruction to prioritize novelty over quality | Higher combined scores than quality-maximizing approach |
| 6 | Red team as creativity | contrarian-innovator-case-studies.md | Red team agent mapped blind spots first | Revealed evaluation loophole + convergence patterns |
| 7 | First principles / assumption audit | innovative-thinking-cognitive-science.md | Assumption auditor found 10 shared constraints | Specific violations assigned to each team |
| 8 | Outsider perspective | ai-agent-creativity-innovation-research.md | Restaurant manager analogy for Team 4 | Bin lifecycle concept (open/active/closed) |

## Future Directions

### Remaining Empty Niches to Target
- Oscillating-order specialist (only 1/99 occupant)
- Large-item specialist with small-item sacrifice (0/99)
- High waste-variance + good quality architecture (0/99)
- Trimodal/increasing regime-change detector

### Assumptions Still Unviolated
- Items never move after placement (0/99 violators) — limited reorganization could be transformative
- No cross-bin reasoning in scoring (only Team 3 partially addressed this)
- No principled 1/k mathematical structure (only harmonic uses this)

### Process Improvements
- Fix the evaluation loophole (verify place() returns match get_bins() assignments)
- Add temporal/dynamic behavioral signature dimensions to reward sequence-aware heuristics
- Implement island-based evolution (FunSearch-style) with migration between subpopulations
- Run Phase 1 intelligence gathering periodically (every 10 generations) to re-map the space

### Combining Discovered Innovations
- Gap fillability (Team 3) + bin lifecycle (Team 4) — probabilistic scoring within a bounded active set
- Phase-based switching (Team 1) + hash complement (Team 5) — use dict lookup but change probe targets per phase
- Count-based placement (Team 2) + gap demand (Team 3) — detect distribution clustering and switch to count-based with demand-aware fallback

---

## Next Exploration Prompt

Use this as the prompt for the next diamond hunt session. Copy-paste and run.

---

### Round 2: Deepen and Combine

We completed Round 1 of the diamond hunt (see diamond-hunt-results.md). 5 new heuristics were admitted, each with a single breakthrough idea. Now we need to go deeper.

**Phase 1: Re-map the space (3 parallel agents)**

Run these after the Round 1 admissions to see what changed:

```
Agent 1 (Niche Re-mapper): Run `harness.py status` and re-analyze the behavioral signature space. Which of the 7 original empty niches are still empty after Round 1? What NEW niches opened up? Focus on the interaction between Round 1 candidates — do any of them create new "adjacent possible" regions?

Agent 2 (Combination Scout): Read the 5 Round 1 candidates (301-305). For each PAIR of candidates, identify what a hybrid would look like. Rank the 10 possible pairs by expected novelty. The top 3 pairs become Phase 2 targets.

Agent 3 (Assumption Depth): The Round 1 candidates each violated 1-2 assumptions. But the THREE hardest assumptions remain unviolated by anyone:
  - Items never move after placement (100% shared)
  - No per-bin temporal/sequence information (100% shared)
  - No principled 1/k mathematical structure (83% shared)
For each, design a concrete violation strategy with enough detail that a Phase 2 agent can implement it.
```

**Phase 2: Three attack vectors (5+ parallel agents)**

**Vector A: Hybrid Synthesis (2-3 agents)**
Take the top-ranked pairs from the Combination Scout and build hybrid heuristics. Each agent gets one pair and must synthesize the abstract principles (not just concatenate code). Use cross-domain reasoning strategy.

Specific hybrids to try:
- **Gap Fillability + Bin Lifecycle** (303 + 304): Probabilistic scoring within a bounded active set. Close bins when their gap has low fill probability (not just when they're full). This turns the lifecycle decision into an information-theoretic one.
- **Phase Switching + Hash Complement** (301 + 305): Use dict-based probe lookup, but change the probe targets per stream phase. Early phase probes for "spread" targets, late phase probes for "tight" targets.
- **Increasing Specialist + Gap Fillability** (301 + 303): Reserve gaps that match predicted future item sizes. In increasing streams, early bins reserve large gaps (high fill probability for future large items).

**Vector B: Hard Assumption Violations (2 agents)**

- **Agent: Limited Reorganization** — Violate assumption #1. Implement a heuristic where place(item) can move up to K=3 previously-placed items to improve the packing. The harness only checks get_bins() at the end, so items can be reassigned internally as long as the final state is valid. This is the single highest-impact untried approach.
  - Constraint: K must be bounded (not full repack)
  - Reasoning strategy: First principles — what is the minimum reorganization that closes the online/offline gap?

- **Agent: Refined Harmonic** — Violate assumption #5. Implement a proper Harmonic-k variant adapted for average-case (not worst-case). Items classified into (1/2, 1], (1/3, 1/2], (1/4, 1/3], etc. Each class gets dedicated bins sized to hold exactly k items. Cross-class "weaving" fills gaps. The canonical harmonic.py is a simple version; build a refined one with distribution-adaptive class boundaries.
  - Reasoning strategy: Anomaly hunt — why does the simple harmonic score poorly? What specific class boundaries work for the 8 test distributions?

**Vector C: Remaining Empty Niches (2 agents)**

- **Agent: Oscillating Rhythm Detector** — Target the oscillating-order niche (1/99 occupant). Design a heuristic that detects negative autocorrelation in the item stream and exploits it. When large-small-large-small is detected, always route the small item into the bin just opened by the preceding large item. Think as a drummer reading rhythm patterns.
  - Assumptions to violate: #8 (sequence info), #2 (cross-bin reasoning)

- **Agent: Sacrifice Specialist** — Target the "high waste-variance + good quality" niche (0/99). Design a "perfectionist + overflow" architecture: maintain two bin classes — "target bins" that must fill to >95% (accept only near-perfect fits) and "overflow bins" that accept everything else. Periodically promote overflow bins to target status. The goal is a bimodal waste distribution (some bins at 99%, others at 60%) that produces better AVERAGE quality than uniform waste.
  - Assumptions to violate: #7 (bin lifecycle), #4 (bin composition tracking)

**Phase 3: Evaluate, Admit, Iterate**

Evaluate all candidates sequentially. After admission, check:
1. Did any hybrid outperform both parents? (bisociation success)
2. Did any hard assumption violation produce quality > 0.92? (breakthrough signal)
3. What new niches opened up? (adjacent possible expansion)

If any candidate scores combined > 0.25, use it as a parent for a focused Round 3.

---

### Round 3+ (Sketch): Evolutionary Pressure

Once Rounds 1-2 have populated diverse niches, shift strategy:

1. **Island Model**: Split the archive into 3-4 "islands" by behavioral clustering. Each island evolves independently for 5 generations, then the best candidate from each island migrates to all others. This prevents re-convergence.

2. **Quality Push on Novel Architectures**: Take each Round 1-2 candidate that scored novelty > 0.2 but quality < 0.90. Run 3 agents in parallel doing standard_mutation on THAT candidate (not best_fit) to push its quality up while preserving its novel architecture.

3. **Adversarial Distribution Design**: Create a new "adversarial" test distribution specifically designed to break the current best heuristic. Add it to the evaluation suite. This expands the problem surface and creates new niches.

4. **Cross-Pollination Tournament**: Take the top candidate from each of the 7 niche targets. Run a round-robin where each pair is synthesized by a cross_domain agent. The 21 hybrids get evaluated and the best 5 are admitted. This is combinatorial creativity at scale.

5. **Meta-Learning**: After 50+ candidates, analyze which Phase 1 findings led to the highest-scoring Phase 2 candidates. Was it niche targeting? Assumption violation? Reasoning strategy? Use this to calibrate future rounds.

---

### Quick-Start Command

To run Round 2, paste this into Claude Code:

```
Read /home/kenan/research/bin-packing/diamond-hunt-results.md for full context on Round 1.
Now execute Round 2 as described in the "Next Exploration Prompt" section:
1. Launch Phase 1 (3 parallel agents: niche re-mapper, combination scout, assumption depth)
2. Synthesize Phase 1 findings
3. Launch Phase 2 (5+ parallel agents across Vectors A, B, C)
4. Evaluate and admit all candidates
5. Report what changed
Use agent teams. Working directory: /home/kenan/research/bin-packing
```
