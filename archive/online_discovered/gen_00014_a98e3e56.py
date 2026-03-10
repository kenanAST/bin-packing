def create_packer(capacity):
    """Max-items-per-bin: limit each bin to at most 4 items. This forces
    bins to close quickly and creates very different fill patterns,
    especially for distributions with many small items."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0

        def place(self, item):
            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                if len(v['i']) >= 4: continue
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
