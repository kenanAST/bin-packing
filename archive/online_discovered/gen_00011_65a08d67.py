def create_packer(capacity):
    """Alternating fit: alternate between best-fit and worst-fit on every
    other item. Creates mixed packing pattern."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0
            self.count = 0

        def place(self, item):
            self.count += 1
            if self.count % 2 == 0:
                return self._worst(item)
            return self._best(item)

        def _best(self, item):
            b, r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < r:
                    r = rem; b = k
            if b >= 0:
                self.bins[b]['i'].append(item); self.bins[b]['t'] += item; return b
            return self._mk(item)

        def _worst(self, item):
            b, r = -1, -1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem > r:
                    r = rem; b = k
            if b >= 0:
                self.bins[b]['i'].append(item); self.bins[b]['t'] += item; return b
            return self._mk(item)

        def _mk(self, item):
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
