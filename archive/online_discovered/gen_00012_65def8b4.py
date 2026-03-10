def create_packer(capacity):
    """First-Fit-Decreasing-Online: maintain a sorted insertion point.
    Keep open bins sorted by remaining capacity descending. Place in
    first bin that fits (scanning from most-remaining). Different from
    worst-fit because we take the FIRST fit, not the WORST."""

    class Packer:
        def __init__(self):
            self.bins = []  # list of {'i','t'}, kept sorted by remaining desc

        def place(self, item):
            for idx, b in enumerate(self.bins):
                if item <= capacity - b['t'] + 1e-9:
                    b['i'].append(item)
                    b['t'] += item
                    # Re-sort by remaining descending
                    while idx > 0 and (capacity - self.bins[idx]['t']) > (capacity - self.bins[idx-1]['t']):
                        self.bins[idx], self.bins[idx-1] = self.bins[idx-1], self.bins[idx]
                        idx -= 1
                    while idx < len(self.bins)-1 and (capacity - self.bins[idx]['t']) < (capacity - self.bins[idx+1]['t']):
                        self.bins[idx], self.bins[idx+1] = self.bins[idx+1], self.bins[idx]
                        idx += 1
                    return idx
            self.bins.insert(0, {'i': [item], 't': item})
            return 0

        def get_bins(self):
            return [list(b['i']) for b in self.bins]

    return Packer()
