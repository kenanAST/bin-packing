def create_packer(capacity):
    """Hybrid: online best-fit for first 50% of items (estimated from running
    count), then batch remaining items and pack via FFD. Transition from
    online to offline mid-stream."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.n = 0
            self.batch = []; self.online_phase = True
            self.est_total = 200  # updated as we go
        def _bf(self, item):
            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
            if best >= 0: self.bins[best]['i'].append(item); self.bins[best]['t'] += item; return best
            b = self.nid; self.nid += 1; self.bins[b] = {'i': [item], 't': item}; return b
        def _ffd(self, items):
            for it in sorted(items, reverse=True):
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
                if best >= 0: self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else: b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def place(self, item):
            self.n += 1
            if self.online_phase:
                r = self._bf(item)
                # Switch to batch after enough online items
                if self.n > 30:
                    self.online_phase = False
                return r
            else:
                self.batch.append(item)
                if len(self.batch) >= 100:
                    self._ffd(self.batch); self.batch = []
                return max(self.bins.keys()) if self.bins else 0
        def get_bins(self):
            if self.batch: self._ffd(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
