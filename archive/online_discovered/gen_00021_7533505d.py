def create_packer(capacity):
    """Batch interleave: batch of 100, sort, then interleave (largest, smallest,
    2nd largest, 2nd smallest, ...). Pack this interleaved order via best-fit.
    Creates natural large+small pairing."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []
        def _interleave_pack(self, items):
            s = sorted(items)
            interleaved = []
            lo, hi = 0, len(s) - 1
            while lo <= hi:
                interleaved.append(s[hi]); hi -= 1
                if lo <= hi: interleaved.append(s[lo]); lo += 1
            for it in interleaved:
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
                if best >= 0: self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else: b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= 100: self._interleave_pack(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0
        def get_bins(self):
            if self.batch: self._interleave_pack(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
