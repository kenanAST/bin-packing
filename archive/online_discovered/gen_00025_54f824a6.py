"""Markov State Packer — switches strategy based on recent item size patterns.

States:
- SMALL_RUN: last 5 items all < 0.3*cap → worst-fit among roomy bins
- LARGE_RUN: last 5 items all > 0.5*cap → best-fit to close bins fast
- MIXED: otherwise → fillability scoring based on empirical distribution

The fillability scoring maintains a 20-bucket histogram of item sizes seen.
For each candidate bin, compute the gap after placement. Score = fraction of
items in the histogram bucket matching that gap. Pick the bin whose gap is
most likely to be filled by a future item. Tiebreak by tighter fit.

SMALL_RUN uses worst-fit ONLY among bins with remaining > 0.65*cap to prevent
small items from filling bins to awkward medium levels.
"""


def create_packer(capacity):
    SMALL_THRESH = 0.3 * capacity
    LARGE_THRESH = 0.5 * capacity
    ROOMY_THRESH = 0.65 * capacity
    WINDOW = 5
    NUM_BUCKETS = 20
    BUCKET_WIDTH = capacity / NUM_BUCKETS
    EPS = 1e-9

    class MarkovStatePacker:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.recent = []          # last WINDOW item sizes
            self.histogram = [0] * NUM_BUCKETS
            self.total_items = 0

        def _bucket_for(self, size):
            b = int(size / BUCKET_WIDTH)
            if b >= NUM_BUCKETS:
                b = NUM_BUCKETS - 1
            if b < 0:
                b = 0
            return b

        def _fillability(self, gap):
            """Probability that a future item matches this gap."""
            if gap < EPS:
                return 0.0
            if self.total_items == 0:
                return 0.0
            # Sum histogram mass for items that would fit in this gap
            # Weight by closeness to the gap (items that fill it tighter score higher)
            score = 0.0
            for b in range(NUM_BUCKETS):
                bucket_center = (b + 0.5) * BUCKET_WIDTH
                if bucket_center <= gap + EPS:
                    # This bucket's items fit in the gap
                    freq = self.histogram[b] / self.total_items
                    # Weight: how much of the gap would be filled (closer to 1.0 = better)
                    fill_ratio = bucket_center / gap if gap > EPS else 0.0
                    score += freq * fill_ratio
            return score

        def _get_state(self):
            if len(self.recent) < WINDOW:
                return 'MIXED'
            if all(s < SMALL_THRESH for s in self.recent):
                return 'SMALL_RUN'
            if all(s > LARGE_THRESH for s in self.recent):
                return 'LARGE_RUN'
            return 'MIXED'

        def _place_small_run(self, item):
            """Worst-fit among bins with remaining > ROOMY_THRESH."""
            worst_idx = -1
            worst_remaining = -1.0
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if remaining >= ROOMY_THRESH and item <= remaining + EPS:
                    if remaining > worst_remaining:
                        worst_remaining = remaining
                        worst_idx = i
            if worst_idx >= 0:
                return worst_idx
            # No roomy bin available — open a new bin
            return -1

        def _place_large_run(self, item):
            """Best-fit: place in tightest-fitting bin."""
            best_idx = -1
            best_remaining = capacity + 1.0
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item <= remaining + EPS and remaining < best_remaining:
                    best_remaining = remaining
                    best_idx = i
            return best_idx

        def _place_mixed(self, item):
            """Fillability scoring: pick bin whose post-placement gap is most
            likely to be filled by a future item."""
            best_idx = -1
            best_score = -1.0
            best_remaining = capacity + 1.0
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item > remaining + EPS:
                    continue
                gap = remaining - item
                score = self._fillability(gap)
                # Tiebreak: tighter fit (smaller remaining after placement)
                if (score > best_score + EPS or
                    (abs(score - best_score) < EPS and gap < best_remaining)):
                    best_score = score
                    best_remaining = gap
                    best_idx = i
            return best_idx

        def place(self, item):
            # Update histogram
            self.histogram[self._bucket_for(item)] += 1
            self.total_items += 1

            # Update recent window
            self.recent.append(item)
            if len(self.recent) > WINDOW:
                self.recent.pop(0)

            # Determine state and dispatch
            state = self._get_state()

            if state == 'SMALL_RUN':
                idx = self._place_small_run(item)
            elif state == 'LARGE_RUN':
                idx = self._place_large_run(item)
            else:
                idx = self._place_mixed(item)

            # If no suitable bin found, open new
            if idx < 0:
                self.bins.append([item])
                self.bin_sums.append(item)
                return len(self.bins) - 1

            self.bins[idx].append(item)
            self.bin_sums[idx] += item
            return idx

        def get_bins(self):
            return [list(b) for b in self.bins]

    return MarkovStatePacker()
