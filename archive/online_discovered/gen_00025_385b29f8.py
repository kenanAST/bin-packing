def create_packer(capacity):
    """Layered Fill Packer: drives all open bins toward the same target
    fill level, then advances the target.

    Maintains a global "target_fill" that starts at 0.30 and increases
    by 0.15 each time most open bins exceed it. For each item:
    - Among bins where item fits: prefer the bin whose fill-after is
      closest to (but not exceeding) target_fill
    - If no bin can stay below target_fill: advance target and retry
    - This creates "waves" of uniform fill across many bins

    The key difference from best-fit: items are placed to EQUALIZE fill
    levels rather than to close individual bins. Bins fill uniformly
    in layers (30% → 45% → 60% → 75% → 90% → 100%).

    For increasing order: small items spread across bins at 30%, then
    larger items advance them to 60%, then large items close them.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.target = 0.30
            self.n = 0
            self.step = 0.15

        def place(self, item):
            self.n += 1
            cap = capacity
            target_sum = self.target * cap

            # Try to find a bin where fill-after is closest to target
            # but doesn't overshoot by too much
            best_idx = -1
            best_diff = 1e18  # |fill_after - target|, lower is better

            for i in range(len(self.bins)):
                rem = cap - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                fill_after = self.bin_sums[i] + item
                diff = abs(fill_after - target_sum)
                if diff < best_diff:
                    best_diff = diff
                    best_idx = i

            # If best option overshoots target significantly, check if
            # we should advance target
            if best_idx >= 0:
                fill_after = self.bin_sums[best_idx] + item
                if fill_after > target_sum + 0.2 * cap:
                    # Most bins might be past target — check
                    above = sum(1 for s in self.bin_sums if s >= target_sum * 0.9)
                    if above > len(self.bins) * 0.6 and self.target < 0.95:
                        self.target = min(self.target + self.step, 0.99)
                        target_sum = self.target * cap
                        # Re-evaluate with new target
                        best_idx2 = -1
                        best_diff2 = 1e18
                        for i in range(len(self.bins)):
                            rem = cap - self.bin_sums[i]
                            if item > rem + 1e-9:
                                continue
                            fill_after2 = self.bin_sums[i] + item
                            diff2 = abs(fill_after2 - target_sum)
                            if diff2 < best_diff2:
                                best_diff2 = diff2
                                best_idx2 = i
                        if best_idx2 >= 0:
                            best_idx = best_idx2

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
