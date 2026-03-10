def create_packer(capacity):
    """Fillability-Tiebreak Packer: best-fit primary, fillability secondary.

    Groups candidate bins into "tight" (remaining < 20% cap) and "loose".
    Within tight group: pure best-fit (close bins out).
    Within loose group: rank by fillability score (how likely is the
    remaining gap to be filled by future items based on empirical histogram).

    This preserves best-fit's quality on random/decreasing order while
    making smarter choices for bins that still have significant capacity.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.nbuckets = 20
            self.hist = [0] * self.nbuckets
            self.total = 0

        def _bucket(self, val):
            b = int(val * self.nbuckets / capacity)
            return max(0, min(b, self.nbuckets - 1))

        def _fillability(self, gap):
            if gap < 1e-9:
                return 100.0
            if self.total < 5:
                return 0.0
            bw = capacity / self.nbuckets
            tol = bw * 0.7
            # P(1 item fills gap)
            lo = max(0, self._bucket(gap - tol))
            hi = min(self.nbuckets - 1, self._bucket(gap + tol))
            c1 = sum(self.hist[lo:hi + 1])
            p1 = c1 / self.total
            # P(2 items fill gap)
            half = gap / 2
            lo2 = max(0, self._bucket(half - tol))
            hi2 = min(self.nbuckets - 1, self._bucket(half + tol))
            c2 = sum(self.hist[lo2:hi2 + 1])
            p2 = (c2 / self.total) ** 2
            return p1 * 3.0 + p2

        def place(self, item):
            self.n += 1
            self.hist[self._bucket(item)] += 1
            self.total += 1

            tight_thresh = 0.18 * capacity

            best_tight = -1
            best_tight_rem = capacity + 1
            best_loose = -1
            best_loose_score = -1.0
            best_loose_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                new_rem = rem - item
                if new_rem < tight_thresh:
                    # Tight: pure best-fit
                    if new_rem < best_tight_rem:
                        best_tight_rem = new_rem
                        best_tight = i
                else:
                    # Loose: fillability score
                    score = self._fillability(new_rem)
                    if score > best_loose_score + 0.005 or \
                       (abs(score - best_loose_score) <= 0.005 and new_rem < best_loose_rem):
                        best_loose_score = score
                        best_loose_rem = new_rem
                        best_loose = i

            # New bin option
            new_rem = capacity - item
            new_fill = self._fillability(new_rem) if new_rem >= tight_thresh else 0.0

            # Priority: tight (close bins) > best loose/new by fillability
            if best_tight >= 0:
                idx = best_tight
            elif best_loose >= 0:
                if new_fill > best_loose_score + 0.005:
                    return self._new_bin(item)
                idx = best_loose
            else:
                return self._new_bin(item)

            self.bins[idx].append(item)
            self.bin_sums[idx] += item
            return idx

        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
