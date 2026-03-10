def create_packer(capacity):
    """Phase-Shift Packer: changes bin selection strategy in discrete phases
    based on accumulated distribution knowledge.

    Phase 1 (first 10% of observed items): Pure first-fit, learning distribution
    Phase 2 (ongoing): Uses empirical CDF to compute "fillability score" —
    the probability that a bin's remaining gap can be filled in exactly K items.

    For each bin, score = P(gap filled in 1 item) * 3 + P(gap filled in 2 items) * 1
    where probabilities come from the empirical item distribution.

    This is NOT a scoring variant of best-fit — it can prefer LARGER gaps
    over smaller ones if those gaps are more likely to be exactly filled.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            # Histogram: 25 buckets for item sizes
            self.nbuckets = 25
            self.hist = [0] * self.nbuckets
            self.total = 0

        def _bucket(self, val):
            b = int(val * self.nbuckets / capacity)
            if b >= self.nbuckets:
                b = self.nbuckets - 1
            if b < 0:
                b = 0
            return b

        def _prob_in_range(self, lo, hi):
            """Probability an item falls in [lo, hi] based on histogram."""
            if self.total == 0 or lo > hi:
                return 0.0
            b_lo = self._bucket(lo)
            b_hi = self._bucket(hi)
            count = 0
            for b in range(b_lo, b_hi + 1):
                count += self.hist[b]
            return count / self.total

        def _fillability(self, gap):
            """Score: how easily can this gap be filled by future items?"""
            if gap < 1e-9:
                return 10.0  # perfectly full — best possible

            bw = capacity / self.nbuckets
            # P(filled in 1 item): item in [gap - tolerance, gap + tolerance]
            tol = bw * 0.6
            p1 = self._prob_in_range(gap - tol, gap + tol)

            # P(filled in 2 items): any pair summing to gap
            # Approximate: item1 in [gap/2 - tol, gap/2 + tol] squared
            p2_half = self._prob_in_range(gap / 2 - tol, gap / 2 + tol)
            p2 = p2_half * p2_half

            # P(filled in 3 items): item in [gap/3 ± tol] cubed
            p3_third = self._prob_in_range(gap / 3 - tol, gap / 3 + tol)
            p3 = p3_third * p3_third * p3_third

            return p1 * 5.0 + p2 * 2.0 + p3 * 1.0

        def place(self, item):
            self.n += 1
            self.hist[self._bucket(item)] += 1
            self.total += 1

            # Phase 1: learning (first 15 items) — use best-fit
            if self.n <= 15:
                return self._best_fit(item)

            # Phase 2: fillability-guided placement
            best_idx = -1
            best_score = -1.0
            best_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                new_rem = rem - item
                score = self._fillability(new_rem)
                # Tiebreak: prefer tighter fit (like best-fit)
                if score > best_score + 0.01 or (abs(score - best_score) <= 0.01 and new_rem < best_rem):
                    best_score = score
                    best_idx = i
                    best_rem = new_rem

            # Consider new bin
            new_rem = capacity - item
            new_score = self._fillability(new_rem)
            if new_score > best_score + 0.01 or (best_idx < 0):
                return self._new_bin(item)

            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            return best_idx

        def _best_fit(self, item):
            best_idx = -1
            best_rem = capacity + 1
            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best_idx = i
            if best_idx >= 0:
                self.bins[best_idx].append(item)
                self.bin_sums[best_idx] += item
                return best_idx
            return self._new_bin(item)

        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
