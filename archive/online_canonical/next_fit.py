def create_packer(capacity):
    """Next Fit: keep one open bin, start a new one when item doesn't fit."""

    class Packer:
        def __init__(self):
            self.bins = [[]]
            self.bin_sums = [0.0]

        def place(self, item):
            if self.bin_sums[-1] + item > capacity + 1e-9:
                self.bins.append([])
                self.bin_sums.append(0.0)
            idx = len(self.bins) - 1
            self.bins[idx].append(item)
            self.bin_sums[idx] += item
            return idx

        def get_bins(self):
            return [list(b) for b in self.bins if b]

    return Packer()
