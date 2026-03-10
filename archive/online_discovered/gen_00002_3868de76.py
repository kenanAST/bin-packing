def create_packer(capacity):
    """Anomaly Hunt: Next Fit's worst case is uniform_medium/large with increasing order.
    Root cause: when small items come first, NF closes bins too early.
    Fix: Use a "lookahead buffer" of K recent bins that can still receive items.
    Essentially Next-K-Fit with adaptive K based on observed item variance.
    Uses a deque-based sliding window instead of parallel sum lists."""
    from collections import deque

    class Packer:
        def __init__(self):
            self.closed_bins = []  # fully closed
            self.window = deque()  # (bin_items_list, bin_total) - active window
            self.window_size = 3
            self.items_seen = 0
            self.sum_items = 0.0
            self.sum_sq = 0.0
            self.global_index = 0  # tracks total bins created

        def _adapt_window(self):
            if self.items_seen < 5:
                return
            mean = self.sum_items / self.items_seen
            var = self.sum_sq / self.items_seen - mean * mean
            std = max(var, 0) ** 0.5
            cv = std / mean if mean > 0.01 else 0
            # High variance -> larger window (more pairing opportunities)
            # Low variance -> smaller window (items are similar, less benefit)
            self.window_size = max(2, min(8, int(2 + cv * 10)))

        def place(self, item):
            self.items_seen += 1
            self.sum_items += item
            self.sum_sq += item * item
            if self.items_seen % 15 == 0:
                self._adapt_window()

            # Try to fit in existing window bins (best fit within window)
            best_idx = -1
            best_remaining = capacity + 1
            for i, (items, total) in enumerate(self.window):
                remaining = capacity - total
                if item <= remaining + 1e-9 and remaining < best_remaining:
                    best_remaining = remaining
                    best_idx = i

            if best_idx >= 0:
                items, total = self.window[best_idx]
                items.append(item)
                self.window[best_idx] = (items, total + item)
                # If bin is nearly full, close it
                if capacity - (total + item) < 0.05 * capacity:
                    closed = self.window[best_idx]
                    del self.window[best_idx]
                    self.closed_bins.append(closed[0])
                bid = self.global_index - len(self.window) + best_idx
                # Approximate bin index
                return sum(1 for _ in range(best_idx))  # position in window

            # Evict oldest if window full
            while len(self.window) >= self.window_size:
                old = self.window.popleft()
                self.closed_bins.append(old[0])

            # Open new bin
            self.window.append(([item], item))
            self.global_index += 1
            return self.global_index - 1

        def get_bins(self):
            result = [list(b) for b in self.closed_bins]
            for items, total in self.window:
                result.append(list(items))
            return result

    return Packer()
