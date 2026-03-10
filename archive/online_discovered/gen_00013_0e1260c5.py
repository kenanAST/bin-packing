def create_packer(capacity):
    """Tightest-pair: for each incoming item, find the bin where the
    remaining space after placement is closest to the AVERAGE item size.
    This maximizes the probability that the next item fills the bin."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0
            self.total = 0.0
            self.n = 0

        def place(self, item):
            self.total += item; self.n += 1
            avg = self.total / self.n

            best, best_s = -1, float('inf')
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                after = rem - item
                if after < 0.02 * capacity:
                    s = -1000
                else:
                    s = abs(after - avg)
                if s < best_s: best_s = s; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
