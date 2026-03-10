def create_packer(capacity):
    """Batch-sort v2: larger batch (16 items), sort descending, FFD.
    Bigger batch gives better local optimization."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0
            self.batch = []; self.batch_size = 16

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
                    b = self.nid; self.nid += 1
                    self.bins[b] = {'i': [it], 't': it}

        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= self.batch_size:
                self._ffd(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0

        def get_bins(self):
            if self.batch: self._ffd(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
