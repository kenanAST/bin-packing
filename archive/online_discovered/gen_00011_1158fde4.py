def create_packer(capacity):
    """Bin-count limiter: never have more than sqrt(n) open bins.
    When limit reached, close the fullest bin. Best-fit among open bins."""
    import math

    class Packer:
        def __init__(self):
            self.open = {}
            self.closed = {}
            self.nid = 0
            self.n = 0

        def place(self, item):
            self.n += 1
            limit = max(3, int(math.sqrt(self.n)) + 1)

            b, r = -1, capacity + 1
            for k, v in self.open.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < r:
                    r = rem; b = k
            if b >= 0:
                self.open[b]['i'].append(item)
                self.open[b]['t'] += item
                if capacity - self.open[b]['t'] < 0.02 * capacity:
                    self.closed[b] = self.open.pop(b)
                return b

            while len(self.open) >= limit:
                fullest = max(self.open, key=lambda k: self.open[k]['t'])
                self.closed[fullest] = self.open.pop(fullest)

            b = self.nid; self.nid += 1
            self.open[b] = {'i': [item], 't': item}
            return b

        def get_bins(self):
            a = {}; a.update(self.open); a.update(self.closed)
            return [list(a[b]['i']) for b in sorted(a)]

    return Packer()
