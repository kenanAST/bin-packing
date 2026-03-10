def create_packer(capacity):
    """Trend-Adaptive Dead-Zone Packer.

    Uses priority-tier bin selection (CLOSE > OPEN > DEAD > NEW) where
    the dead zone width adapts based on detected item size trend.

    - No trend: dead zone is very narrow → behaves like best-fit
    - Increasing trend: dead zone widens → avoids medium-fill bins for
      small items, preserving space for future large items
    - Decreasing trend: dead zone is narrow → pure best-fit

    Trend detection uses rank correlation of the last 20 items.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.window = []
            self.window_size = 20

        def _trend_score(self):
            """Compute trend: positive = increasing, negative = decreasing."""
            w = self.window
            n = len(w)
            if n < 10:
                return 0.0
            # Simple trend: correlation between index and value
            # Using normalized rank correlation approximation
            mean_v = sum(w) / n
            mean_i = (n - 1) / 2.0
            num = 0.0
            den_v = 0.0
            den_i = 0.0
            for j in range(n):
                di = j - mean_i
                dv = w[j] - mean_v
                num += di * dv
                den_v += dv * dv
                den_i += di * di
            if den_v < 1e-12 or den_i < 1e-12:
                return 0.0
            return num / (den_v * den_i) ** 0.5

        def place(self, item):
            self.n += 1
            self.window.append(item)
            if len(self.window) > self.window_size:
                self.window.pop(0)

            trend = self._trend_score()

            # Adaptive thresholds based on trend
            if trend > 0.3:
                # Strong increasing: wide dead zone
                close_thresh = 0.12 * capacity
                open_thresh = 0.55 * capacity
            elif trend > 0.1:
                # Mild increasing: moderate dead zone
                close_thresh = 0.08 * capacity
                open_thresh = 0.45 * capacity
            else:
                # No trend or decreasing: very narrow dead zone → ~best-fit
                close_thresh = 0.03 * capacity
                open_thresh = 0.95 * capacity

            best_close = -1
            best_close_rem = capacity + 1
            best_open = -1
            best_open_rem = capacity + 1
            best_dead = -1
            best_dead_rem = capacity + 1

            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                new_rem = rem - item
                if new_rem < close_thresh:
                    if new_rem < best_close_rem:
                        best_close_rem = new_rem
                        best_close_idx = i
                        best_close = i
                elif new_rem >= open_thresh:
                    if new_rem < best_open_rem:
                        best_open_rem = new_rem
                        best_open = i
                else:
                    if new_rem < best_dead_rem:
                        best_dead_rem = new_rem
                        best_dead = i

            # Consider new bin
            new_rem = capacity - item

            if best_close >= 0:
                idx = best_close
            elif best_open >= 0:
                idx = best_open
            elif new_rem >= open_thresh:
                return self._new_bin(item)
            elif best_dead >= 0:
                idx = best_dead
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
