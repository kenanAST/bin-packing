def create_packer(capacity):
    """Median-split: track running median of items. Items below median
    go to one pool (best-fit), items above go to another pool (best-fit).
    Cross-pool placement allowed when it fills bin >85%."""

    class Packer:
        def __init__(self):
            self.lo_bins = {}
            self.hi_bins = {}
            self.nid = 0
            self.items = []
            self.n = 0
            self.median = capacity * 0.5

        def _update_median(self, item):
            self.items.append(item)
            self.n += 1
            if self.n <= 50 or self.n % 10 == 0:
                s = sorted(self.items[-100:])
                self.median = s[len(s)//2]

        def place(self, item):
            self._update_median(item)
            is_hi = item >= self.median
            own = self.hi_bins if is_hi else self.lo_bins
            other = self.lo_bins if is_hi else self.hi_bins

            bid = self._bf(item, own)
            if bid >= 0: return bid

            # Cross-pool only for tight fits
            bid = self._bf_tight(item, other)
            if bid >= 0: return bid

            return self._mk(item, own)

        def _bf(self, item, pool):
            b, r = -1, capacity + 1
            for k, v in pool.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < r:
                    r = rem; b = k
            if b >= 0:
                pool[b]['i'].append(item); pool[b]['t'] += item
            return b

        def _bf_tight(self, item, pool):
            b, r = -1, capacity + 1
            for k, v in pool.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < r and (v['t'] + item) > 0.85 * capacity:
                    r = rem; b = k
            if b >= 0:
                pool[b]['i'].append(item); pool[b]['t'] += item
            return b

        def _mk(self, item, pool):
            b = self.nid; self.nid += 1
            pool[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            a = {}; a.update(self.lo_bins); a.update(self.hi_bins)
            return [list(a[b]['i']) for b in sorted(a)]

    return Packer()
