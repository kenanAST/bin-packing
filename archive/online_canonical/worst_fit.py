def create_packer(capacity):
    """Worst Fit: place item in the bin with most remaining space."""

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []

        def place(self, item):
            worst_idx = -1
            worst_remaining = -1
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item <= remaining + 1e-9 and remaining > worst_remaining:
                    worst_remaining = remaining
                    worst_idx = i
            if worst_idx >= 0:
                self.bins[worst_idx].append(item)
                self.bin_sums[worst_idx] += item
                return worst_idx
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
