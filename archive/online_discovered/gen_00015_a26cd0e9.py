def create_packer(capacity):
    """Min-max-fill: among fitting bins, pick the one whose fill is closest
    to the MEDIAN fill of all bins. This fights outliers — prevents
    some bins from being very full while others are nearly empty."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0

        def place(self, item):
            if not self.bins:
                b = self.nid; self.nid += 1
                self.bins[b] = {'i': [item], 't': item}; return b

            fills = sorted(v['t'] for v in self.bins.values())
            median = fills[len(fills) // 2]

            best, best_s = -1, float('inf')
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                new_fill = v['t'] + item
                if rem - item < 0.03 * capacity:
                    s = -10000
                else:
                    s = abs(new_fill - median)
                if s < best_s: best_s = s; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
