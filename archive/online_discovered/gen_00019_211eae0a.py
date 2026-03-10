def create_packer(capacity):
    """Batch-sort v4: batch of 50 items."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []

        def _ffd(self, items):
            for it in sorted(items, reverse=True):
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = k
                if best >= 0:
                    self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else:
                    b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}

        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= 50:
                self._ffd(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0

        def get_bins(self):
            if self.batch: self._ffd(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
