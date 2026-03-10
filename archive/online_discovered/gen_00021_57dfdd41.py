def create_packer(capacity):
    """Hybrid online/batch: use online best-fit for items >0.5*cap (immediate),
    buffer items <=0.5*cap. When buffer hits 50, sort desc and FFD them.
    Large items need immediate placement; small items benefit from batching."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []
        def _ffd(self, items):
            for it in sorted(items, reverse=True):
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
                if best >= 0: self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else: b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def _bf(self, item):
            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
            if best >= 0: self.bins[best]['i'].append(item); self.bins[best]['t'] += item; return best
            b = self.nid; self.nid += 1; self.bins[b] = {'i': [item], 't': item}; return b
        def place(self, item):
            if item > capacity * 0.5:
                return self._bf(item)
            self.batch.append(item)
            if len(self.batch) >= 50: self._ffd(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0
        def get_bins(self):
            if self.batch: self._ffd(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
