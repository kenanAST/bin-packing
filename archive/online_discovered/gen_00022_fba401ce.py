def create_packer(capacity):
    """Batch 30 with alternating FFD/BFD: even batches use first-fit-decreasing,
    odd batches use best-fit-decreasing. Creates mixed patterns."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []; self.batch_num = 0
        def _ffd(self, items):
            for it in sorted(items, reverse=True):
                placed = False
                for k, v in self.bins.items():
                    if it <= capacity - v['t'] + 1e-9:
                        v['i'].append(it); v['t'] += it; placed = True; break
                if not placed:
                    b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def _bfd(self, items):
            for it in sorted(items, reverse=True):
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
                if best >= 0: self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else: b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= 30:
                if self.batch_num % 2 == 0: self._ffd(self.batch)
                else: self._bfd(self.batch)
                self.batch = []; self.batch_num += 1
            return max(self.bins.keys()) if self.bins else 0
        def get_bins(self):
            if self.batch: self._bfd(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
