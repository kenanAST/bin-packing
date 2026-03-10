def create_packer(capacity):
    """Batch 100 with random shuffle before FFD. Different ordering creates
    different packing than pure descending sort."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []
            self.seed = 42
        def _shuffle(self, items):
            # Simple deterministic shuffle
            n = len(items)
            result = list(items)
            s = self.seed
            for i in range(n - 1, 0, -1):
                s = (s * 1103515245 + 12345) & 0x7fffffff
                j = s % (i + 1)
                result[i], result[j] = result[j], result[i]
            self.seed = s
            return result
        def _pack(self, items):
            shuffled = self._shuffle(items)
            for it in shuffled:
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
                if best >= 0: self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else: b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= 100: self._pack(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0
        def get_bins(self):
            if self.batch: self._pack(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
