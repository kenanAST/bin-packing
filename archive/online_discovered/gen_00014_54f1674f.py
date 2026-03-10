def create_packer(capacity):
    """Tiered-threshold: 4 tiers of bins by fill level. An item can only
    be placed in a bin if it would push the bin to the NEXT tier.
    Tier thresholds: 0.25, 0.5, 0.75, 1.0. This prevents bins from
    lingering at intermediate fills."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0
            self.thresholds = [0.25, 0.5, 0.75, 1.0]

        def _next_threshold(self, fill):
            for t in self.thresholds:
                if fill < t - 1e-9: return t
            return 1.0

        def place(self, item):
            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                new_fill = (v['t'] + item) / capacity
                current_tier = self._next_threshold(v['t'] / capacity)
                # Prefer placements that cross a threshold
                if new_fill >= current_tier - 0.02:
                    if rem < best_r: best_r = rem; best = k

            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best

            # Fallback: regular best fit
            best, best_r = -1, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best

            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
