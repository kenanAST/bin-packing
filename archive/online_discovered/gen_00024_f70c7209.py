def create_packer(capacity):
    """Distribution-Aware Fillability Packer.

    For each placement, scores bins by how likely their remaining gap
    can be filled by 1-3 future items, based on empirical item histogram.

    Key improvement over naive fillability: gaps smaller than the minimum
    observed item get a huge bonus (they're unfillable → close the bin now).
    This prevents the "stranded nearly-full bins" problem.

    Score = closability_bonus + P(1-fill)*5 + P(2-fill)*2 + P(3-fill)

    Uses 30-bucket histogram for precision. Tiebreak by tighter fit.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.NB = 30
            self.hist = [0] * self.NB
            self.min_seen = capacity

        def _b(self, v):
            return max(0, min(int(v * self.NB / capacity), self.NB - 1))

        def _range_prob(self, lo, hi):
            if lo > hi or self.n < 1:
                return 0.0
            bl = max(0, self._b(lo))
            bh = min(self.NB - 1, self._b(hi))
            c = 0
            for i in range(bl, bh + 1):
                c += self.hist[i]
            return c / self.n

        def _score(self, gap):
            if gap < 1e-9:
                return 50.0  # perfectly full

            # Unfillable gap: smaller than any item we've seen
            if self.n >= 5 and gap < self.min_seen * 0.9:
                return 30.0  # close it, nothing can fill this

            bw = capacity / self.NB
            tol = bw * 0.8

            # P(1 item fills gap)
            p1 = self._range_prob(gap - tol, gap + tol)

            # P(2 items fill gap): items around gap/2
            p2 = self._range_prob(gap / 2 - tol, gap / 2 + tol) ** 2

            # P(3 items fill gap): items around gap/3
            p3 = self._range_prob(gap / 3 - tol, gap / 3 + tol) ** 3

            # P(1 large + small): large in [gap*0.6, gap*0.9], small fills rest
            p_large = self._range_prob(gap * 0.5 - tol, gap * 0.8 + tol)
            p_small = self._range_prob(gap * 0.2 - tol, gap * 0.5 + tol)
            p_pair = p_large * p_small

            return p1 * 6.0 + p2 * 2.5 + p_pair * 2.0 + p3 * 0.5

        def place(self, item):
            self.n += 1
            self.hist[self._b(item)] += 1
            if item < self.min_seen:
                self.min_seen = item

            best_idx = -1
            best_score = -1.0
            best_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                gap = rem - item
                s = self._score(gap)
                if s > best_score + 0.01 or \
                   (abs(s - best_score) <= 0.01 and gap < best_rem):
                    best_score = s
                    best_idx = i
                    best_rem = gap

            # New bin
            new_gap = capacity - item
            new_s = self._score(new_gap)
            if best_idx < 0 or new_s > best_score + 0.01:
                return self._new_bin(item)

            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            return best_idx

        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
