def create_packer(capacity):
    """Close-First Entropy Packer: hybrid of best-fit and entropy minimization.

    For each placement:
    1. If any bin would be nearly full after placement (remaining < 12%),
       use best-fit among those (close bins aggressively — like best-fit)
    2. Otherwise, use entropy minimization of fill-level distribution
       among remaining bins (drives bins toward uniform fill — novel behavior)

    This preserves best-fit's efficiency at closing bins while making
    fundamentally different choices for open bins.
    """

    from math import log

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.fill_hist = [0] * 10

        def _bucket(self, fill_frac):
            return max(0, min(int(fill_frac * 10), 9))

        def _entropy_delta(self, old_fill, new_fill):
            """Approximate entropy change from moving one bin from old to new bucket."""
            ob = self._bucket(old_fill)
            nb = self._bucket(new_fill)
            if ob == nb:
                return 0.0
            # Compute full entropy is expensive; use proxy:
            # Prefer moving into more populated buckets (reduces spread)
            return -(self.fill_hist[nb] - self.fill_hist[ob])

        def place(self, item):
            close_thresh = 0.12 * capacity

            # Pass 1: find close-out candidates and best entropy candidates
            best_close = -1
            best_close_rem = capacity + 1
            best_ent = -1
            best_ent_delta = -1e18
            best_ent_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                new_rem = rem - item
                if new_rem < close_thresh:
                    if new_rem < best_close_rem:
                        best_close_rem = new_rem
                        best_close = i
                else:
                    old_fill = self.bin_sums[i] / capacity
                    new_fill = (self.bin_sums[i] + item) / capacity
                    delta = self._entropy_delta(old_fill, new_fill)
                    if delta > best_ent_delta + 0.5 or \
                       (abs(delta - best_ent_delta) <= 0.5 and new_rem < best_ent_rem):
                        best_ent_delta = delta
                        best_ent_rem = new_rem
                        best_ent = i

            # New bin entropy consideration
            new_fill = item / capacity
            new_b = self._bucket(new_fill)
            new_ent_delta = self.fill_hist[new_b]  # joining a populated bucket = good

            # Decision
            if best_close >= 0:
                idx = best_close
            elif best_ent >= 0:
                # Compare best existing entropy move vs new bin
                if new_ent_delta > best_ent_delta + 2:
                    return self._new_bin(item)
                idx = best_ent
            else:
                return self._new_bin(item)

            old_b = self._bucket(self.bin_sums[idx] / capacity)
            self.bins[idx].append(item)
            self.bin_sums[idx] += item
            new_b_actual = self._bucket(self.bin_sums[idx] / capacity)
            if old_b != new_b_actual:
                self.fill_hist[old_b] -= 1
                self.fill_hist[new_b_actual] += 1
            return idx

        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            b = self._bucket(item / capacity)
            self.fill_hist[b] += 1
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
