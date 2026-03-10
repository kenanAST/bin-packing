def create_packer(capacity):
    """Gap-Variance Minimizer: places items to minimize variance of
    remaining capacities across open bins.

    Key insight: if all open bins have similar remaining capacity,
    any future item is equally likely to pair well with any bin.
    High variance means some bins are nearly empty (wasted space reserved)
    and some nearly full (hard to fill further).

    Uses Welford's online algorithm for O(1) variance updates.
    Picks placement that minimizes gap variance, with best-fit tiebreak.
    Bins with remaining < 5% are considered "closed" and excluded.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            # Welford's for remaining capacities of "open" bins
            self.open_count = 0
            self.open_mean = 0.0
            self.open_m2 = 0.0
            self.is_open = []  # True if bin has remaining >= close_thresh

        def _add_to_stats(self, val):
            self.open_count += 1
            delta = val - self.open_mean
            self.open_mean += delta / self.open_count
            delta2 = val - self.open_mean
            self.open_m2 += delta * delta2

        def _remove_from_stats(self, val):
            if self.open_count <= 1:
                self.open_count = 0
                self.open_mean = 0.0
                self.open_m2 = 0.0
                return
            old_mean = self.open_mean
            self.open_count -= 1
            self.open_mean = (old_mean * (self.open_count + 1) - val) / self.open_count
            # Reconstruct M2
            delta = val - old_mean
            delta2 = val - self.open_mean
            self.open_m2 -= delta * delta2
            if self.open_m2 < 0:
                self.open_m2 = 0.0

        def _variance(self):
            if self.open_count < 2:
                return 0.0
            return self.open_m2 / self.open_count

        def place(self, item):
            close_thresh = 0.05 * capacity
            best_idx = -1
            best_var = 1e18
            best_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                new_rem = rem - item
                was_open = self.is_open[i]
                now_open = new_rem >= close_thresh

                # Simulate stats change
                if was_open:
                    self._remove_from_stats(rem)
                if now_open:
                    self._add_to_stats(new_rem)

                var = self._variance()

                # Undo simulation
                if now_open:
                    self._remove_from_stats(new_rem)
                if was_open:
                    self._add_to_stats(rem)

                if var < best_var - 1e-12 or \
                   (abs(var - best_var) < 1e-12 and new_rem < best_rem):
                    best_var = var
                    best_idx = i
                    best_rem = new_rem

            # Consider new bin
            new_rem = capacity - item
            new_open = new_rem >= close_thresh
            if new_open:
                self._add_to_stats(new_rem)
            new_var = self._variance()
            if new_open:
                self._remove_from_stats(new_rem)

            if best_idx < 0 or new_var < best_var - 1e-12:
                return self._new_bin(item, new_rem, new_open)

            # Apply
            old_rem = capacity - self.bin_sums[best_idx]
            was_open = self.is_open[best_idx]
            if was_open:
                self._remove_from_stats(old_rem)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            new_rem_actual = capacity - self.bin_sums[best_idx]
            now_open = new_rem_actual >= close_thresh
            self.is_open[best_idx] = now_open
            if now_open:
                self._add_to_stats(new_rem_actual)
            return best_idx

        def _new_bin(self, item, new_rem, is_open):
            self.bins.append([item])
            self.bin_sums.append(item)
            self.is_open.append(is_open)
            if is_open:
                self._add_to_stats(new_rem)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
