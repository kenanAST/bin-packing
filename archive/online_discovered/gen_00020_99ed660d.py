def create_packer(capacity):
    """Best-fit + periodic repack every 100 items. Pure online best-fit
    but with periodic FFD consolidation of the worst-packed bins."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.n = 0
        def _bf(self, item):
            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
            if best >= 0: self.bins[best]['i'].append(item); self.bins[best]['t'] += item; return best
            b = self.nid; self.nid += 1; self.bins[b] = {'i': [item], 't': item}; return b
        def _repack(self):
            items = []
            rm = [k for k, v in self.bins.items() if v['t'] < 0.65 * capacity]
            for k in rm: items.extend(self.bins[k]['i']); del self.bins[k]
            for it in sorted(items, reverse=True): self._bf(it)
        def place(self, item):
            self.n += 1
            r = self._bf(item)
            if self.n % 100 == 0: self._repack()
            return r
        def get_bins(self):
            self._repack()
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
