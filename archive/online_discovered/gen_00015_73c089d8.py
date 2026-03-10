def create_packer(capacity):
    """Dual-fit: compute both best-fit and worst-fit choices. If best-fit
    would leave remaining < 0.1*cap (near-complete), use it. Otherwise
    use worst-fit. Hybrid that should perform differently from either."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0

        def place(self, item):
            bf, bf_r = -1, capacity + 1
            wf, wf_r = -1, -1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                if rem < bf_r: bf_r = rem; bf = k
                if rem > wf_r: wf_r = rem; wf = k

            if bf >= 0 and bf_r - item < 0.1 * capacity:
                self.bins[bf]['i'].append(item); self.bins[bf]['t'] += item; return bf
            if wf >= 0:
                self.bins[wf]['i'].append(item); self.bins[wf]['t'] += item; return wf
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
