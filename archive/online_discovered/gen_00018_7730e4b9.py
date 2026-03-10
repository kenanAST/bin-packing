def create_packer(capacity):
    """Adaptive-batch: batch size starts at 4 and grows as we learn the
    distribution. Higher variance -> larger batch for better sorting."""
    import math

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0
            self.batch = []; self.batch_size = 4
            self.n = 0; self.sx = 0; self.sx2 = 0

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
            self.n += 1; self.sx += item; self.sx2 += item * item
            if self.n >= 10 and self.n % 10 == 0:
                mean = self.sx / self.n
                var = max(0, self.sx2 / self.n - mean * mean)
                cv = (var**0.5) / mean if mean > 0.01 else 0
                self.batch_size = max(4, min(50, int(4 + cv * 40)))

            self.batch.append(item)
            if len(self.batch) >= self.batch_size:
                self._ffd(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0

        def get_bins(self):
            if self.batch: self._ffd(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
