def create_packer(capacity):
    """Lazy-close: best-fit, but when a bin reaches 80% full, mark it
    'closing'. Closing bins are only used for items that fill them to >95%.
    Otherwise new items go to non-closing bins. Forces items to accumulate
    in open bins before closing efficiently."""

    class Packer:
        def __init__(self):
            self.open = {}; self.closing = {}; self.nid = 0

        def place(self, item):
            # Try closing bins first (only if near-perfect fill)
            for k, v in self.closing.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem - item < 0.05 * capacity:
                    v['i'].append(item); v['t'] += item; return k

            # Try open bins (best fit)
            best, best_r = -1, capacity + 1
            for k, v in self.open.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best = k
            if best >= 0:
                self.open[best]['i'].append(item); self.open[best]['t'] += item
                if self.open[best]['t'] > 0.8 * capacity:
                    self.closing[best] = self.open.pop(best)
                return best

            # Try any closing bin (relax constraint)
            best, best_r = -1, capacity + 1
            for k, v in self.closing.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best = k
            if best >= 0:
                self.closing[best]['i'].append(item); self.closing[best]['t'] += item
                return best

            b = self.nid; self.nid += 1
            self.open[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            a = {}; a.update(self.open); a.update(self.closing)
            return [list(a[b]['i']) for b in sorted(a)]
    return Packer()
