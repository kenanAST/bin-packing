def create_packer(capacity):
    """Entropy-Minimizing Packer: places items to minimize the entropy
    (disorder) of the bin fill-level distribution.

    Instead of greedily minimizing remaining per bin (best-fit), this
    packer evaluates which placement would make the overall distribution
    of bin fill levels MOST concentrated (lowest Shannon entropy).

    The intuition: a set of bins all at 95% fill has low entropy and
    low waste. A set with bins scattered at 30%, 50%, 70% has high
    entropy and high waste. By minimizing entropy, we drive bins toward
    uniform high fill.

    Uses 10 fill-level buckets. After hypothetical placement, computes
    the entropy of the fill distribution. Picks the placement with
    lowest entropy.
    """

    from math import log

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.nbins = 0
            # Track fill level distribution: 10 buckets [0-10%, 10-20%, ..., 90-100%]
            self.fill_hist = [0] * 10

        def _bucket(self, fill_frac):
            b = int(fill_frac * 10)
            return max(0, min(b, 9))

        def _entropy(self, hist, total):
            if total <= 1:
                return 0.0
            e = 0.0
            for c in hist:
                if c > 0:
                    p = c / total
                    e -= p * log(p + 1e-15)
            return e

        def place(self, item):
            best_idx = -1
            best_entropy = 1e18
            best_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                new_fill = (self.bin_sums[i] + item) / capacity
                old_fill = self.bin_sums[i] / capacity
                old_b = self._bucket(old_fill)
                new_b = self._bucket(new_fill)

                # Simulate histogram change
                if old_b != new_b:
                    self.fill_hist[old_b] -= 1
                    self.fill_hist[new_b] += 1
                    ent = self._entropy(self.fill_hist, self.nbins)
                    self.fill_hist[old_b] += 1
                    self.fill_hist[new_b] -= 1
                else:
                    ent = self._entropy(self.fill_hist, self.nbins)

                new_rem = rem - item
                if ent < best_entropy - 1e-9 or \
                   (abs(ent - best_entropy) < 1e-9 and new_rem < best_rem):
                    best_entropy = ent
                    best_idx = i
                    best_rem = new_rem

            # Consider new bin
            new_fill = item / capacity
            new_b = self._bucket(new_fill)
            self.fill_hist[new_b] += 1
            new_ent = self._entropy(self.fill_hist, self.nbins + 1)
            self.fill_hist[new_b] -= 1

            if best_idx < 0 or new_ent < best_entropy - 1e-9:
                return self._new_bin(item)

            # Apply placement
            old_fill = self.bin_sums[best_idx] / capacity
            old_b = self._bucket(old_fill)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            new_fill = self.bin_sums[best_idx] / capacity
            new_b = self._bucket(new_fill)
            if old_b != new_b:
                self.fill_hist[old_b] -= 1
                self.fill_hist[new_b] += 1
            return best_idx

        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            new_b = self._bucket(item / capacity)
            self.fill_hist[new_b] += 1
            self.nbins += 1
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
