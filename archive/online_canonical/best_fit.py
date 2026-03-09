def create_packer(capacity):
    """Best Fit: place item in the bin with least remaining space that still fits."""

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []

        def place(self, item):
            best_idx = -1
            best_remaining = capacity + 1
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item <= remaining + 1e-9 and remaining < best_remaining:
                    best_remaining = remaining
                    best_idx = i
            if best_idx >= 0:
                self.bins[best_idx].append(item)
                self.bin_sums[best_idx] += item
                return best_idx
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
