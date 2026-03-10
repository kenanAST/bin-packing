def create_packer(capacity):
    """First-fit with random start: scan bins starting from a position
    based on the item size (hash-like). This creates size-dependent
    affinity to certain bins without explicit classification."""

    class Packer:
        def __init__(self):
            self.bins = []

        def place(self, item):
            if not self.bins:
                self.bins.append({'i': [item], 't': item})
                return 0
            # Start position based on item quantized size
            start = int(item / capacity * len(self.bins)) % len(self.bins)
            for offset in range(len(self.bins)):
                idx = (start + offset) % len(self.bins)
                if item <= capacity - self.bins[idx]['t'] + 1e-9:
                    self.bins[idx]['i'].append(item)
                    self.bins[idx]['t'] += item
                    return idx
            self.bins.append({'i': [item], 't': item})
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b['i']) for b in self.bins]

    return Packer()
