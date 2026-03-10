def create_packer(capacity):
    """Penalty-based: each bin accumulates a penalty based on how long
    it's been open without being filled. Prefer bins with high penalty
    (urgency) when placing items, weighted against fit quality."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0
            self.tick = 0
            self.created = {}

        def place(self, item):
            self.tick += 1
            best, best_s = -1, -float('inf')
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                age = self.tick - self.created[k]
                fill_after = (v['t'] + item) / capacity
                # Score: fill quality + age urgency
                s = fill_after * 2 + min(age / 50.0, 1.0)
                if rem - item < 0.03 * capacity: s += 100
                if s > best_s: best_s = s; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}
            self.created[b] = self.tick
            return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
