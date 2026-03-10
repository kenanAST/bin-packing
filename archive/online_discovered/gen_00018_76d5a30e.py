def create_packer(capacity):
    """Random-restart: best-fit, but every 50 items, close all bins
    under 60% full and reopen them (items redistributed via FFD).
    Periodic consolidation of poorly-packed bins."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.n = 0

        def place(self, item):
            self.n += 1

            if self.n % 50 == 0 and self.n > 0:
                self._consolidate()

            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item; return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def _consolidate(self):
            # Collect items from under-filled bins
            items = []
            to_remove = []
            for k, v in self.bins.items():
                if v['t'] < 0.6 * capacity:
                    items.extend(v['i'])
                    to_remove.append(k)
            for k in to_remove: del self.bins[k]
            # Re-pack with FFD
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

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
