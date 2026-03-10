def create_packer(capacity):
    """Recency-weighted best-fit: like best-fit but bins that were used
    more recently get a bonus. Score = -remaining + recency_bonus.
    This clusters temporally-close items into same bins."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.tick = 0
            self.last_used = {}

        def place(self, item):
            self.tick += 1
            best, best_s = -1, float('inf')
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                age = self.tick - self.last_used.get(k, 0)
                s = rem + age * 0.01
                if s < best_s: best_s = s; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                self.last_used[best] = self.tick; return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}
            self.last_used[b] = self.tick; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
