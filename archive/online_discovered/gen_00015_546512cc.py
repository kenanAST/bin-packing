def create_packer(capacity):
    """Youngest-bin-first: among fitting bins, prefer the most recently
    created bin. Creates temporal clustering of items."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0

        def place(self, item):
            best, best_id = -1, -1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and k > best_id:
                    best_id = k; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
