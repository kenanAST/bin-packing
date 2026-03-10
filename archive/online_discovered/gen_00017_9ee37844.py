def create_packer(capacity):
    """Target-fill: each bin gets a target fill (0.95*capacity). Score bins
    by how close adding item gets to target. Different from best-fit because
    underfull bins are penalized equally to overfull ones."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0
            self.target = 0.95 * capacity

        def place(self, item):
            best, best_s = -1, float('inf')
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                new_fill = v['t'] + item
                s = abs(new_fill - self.target)
                if s < best_s: best_s = s; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item; return best
            b = self.nid; self.nid += 1; self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
