def create_packer(capacity):
    """Pure Layered Equalizer: targets uniform fill across all bins,
    advancing in layers. NO best-fit tiebreak — purely minimizes
    distance to target fill level.

    Target starts at 25%, advances by 12% when 80% of bins exceed it.
    Among bins where item fits, picks the one where fill_after is
    closest to target. Period. No secondary criterion.

    For ties (within 1% of each other), picks the bin with MORE
    remaining (worst-fit tiebreak) to spread items across bins.
    This is the OPPOSITE of best-fit's tiebreak.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.target = 0.25
            self.n = 0

        def place(self, item):
            self.n += 1
            cap = capacity
            ts = self.target * cap

            # Advance target when 80% of bins are past it
            if len(self.bins) > 3:
                above = 0
                for s in self.bin_sums:
                    if s >= ts - 0.03 * cap:
                        above += 1
                if above >= len(self.bins) * 0.8 and self.target < 0.97:
                    self.target = min(self.target + 0.12, 0.99)
                    ts = self.target * cap

            best_idx = -1
            best_diff = 1e18
            best_rem = -1  # worst-fit tiebreak: prefer MORE remaining

            for i in range(len(self.bins)):
                rem = cap - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                fill_after = self.bin_sums[i] + item
                diff = abs(fill_after - ts)

                # Pure target minimization with worst-fit tiebreak
                if diff < best_diff - 0.01 * cap:
                    best_diff = diff
                    best_idx = i
                    best_rem = rem - item
                elif abs(diff - best_diff) <= 0.01 * cap and (rem - item) > best_rem:
                    # Worst-fit tiebreak: prefer bin with more remaining
                    best_idx = i
                    best_rem = rem - item

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
