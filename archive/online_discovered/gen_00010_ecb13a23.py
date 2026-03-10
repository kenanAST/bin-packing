def create_packer(capacity):
    """Mutation of Next Fit: instead of 1 open bin, keep the last 3.
    When item doesn't fit current bin, try the previous 2 before opening new.
    Simpler than full best-fit scan but captures recent pairing opportunities."""

    class Packer:
        def __init__(self):
            self.bins = []
            self.totals = []

        def place(self, item):
            # Try last 3 bins, newest first
            for offset in range(min(3, len(self.bins))):
                idx = len(self.bins) - 1 - offset
                if self.totals[idx] + item <= capacity + 1e-9:
                    self.bins[idx].append(item)
                    self.totals[idx] += item
                    return idx
            self.bins.append([item])
            self.totals.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
