def create_packer(capacity):
    """Layered fill: target=0.2, step=0.08, advance_pct=0.85, tiebreak=best."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.target = 0.2
            self.n = 0
        def place(self, item):
            self.n += 1
            cap = capacity
            ts = self.target * cap
            if len(self.bins) > 3:
                above = 0
                for s in self.bin_sums:
                    if s >= ts - 0.04 * cap:
                        above += 1
                if above >= len(self.bins) * 0.85 and self.target < 0.97:
                    self.target = min(self.target + 0.08, 0.99)
                    ts = self.target * cap
            best_idx = -1
            best_diff = 1e18
            best_tb = capacity + 1
            for i in range(len(self.bins)):
                rem = cap - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                fa = self.bin_sums[i] + item
                diff = abs(fa - ts)
                nr = rem - item
                if diff < best_diff - 0.02 * cap:
                    best_diff = diff
                    best_idx = i
                    best_tb = nr
                elif abs(diff - best_diff) <= 0.02 * cap and nr < best_tb:
                    best_idx = i
                    best_tb = nr
            if best_idx < 0:
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
