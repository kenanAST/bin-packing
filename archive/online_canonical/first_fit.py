def create_packer(capacity):
    """First Fit: place each item in the first bin that has room."""

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []

        def place(self, item):
            for i in range(len(self.bins)):
                if self.bin_sums[i] + item <= capacity + 1e-9:
                    self.bins[i].append(item)
                    self.bin_sums[i] += item
                    return i
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
