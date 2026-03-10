def create_packer(capacity):
    """Weight-class boxing: items >0.5 are 'heavyweights' and get paired
    with 'lightweights' <0.5. Heavyweights never share bins with each other.
    Lightweights can share bins. Best-fit within each constraint."""

    class Packer:
        def __init__(self):
            self.heavy_bins = {}  # bins containing a heavyweight
            self.light_bins = {}  # bins with only lightweights
            self.nid = 0

        def place(self, item):
            if item > capacity * 0.5:
                # Heavyweight: try light bins first (complement), then new bin
                best, best_r = -1, capacity + 1
                for k, v in self.light_bins.items():
                    rem = capacity - v['t']
                    if item <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = k
                if best >= 0:
                    self.light_bins[best]['i'].append(item)
                    self.light_bins[best]['t'] += item
                    # Move to heavy_bins
                    self.heavy_bins[best] = self.light_bins.pop(best)
                    return best
                b = self.nid; self.nid += 1
                self.heavy_bins[b] = {'i': [item], 't': item}
                return b
            else:
                # Lightweight: try heavy bins (fill gaps), then light bins, then new
                best, best_r = -1, capacity + 1
                for k, v in self.heavy_bins.items():
                    rem = capacity - v['t']
                    if item <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = k
                if best >= 0:
                    self.heavy_bins[best]['i'].append(item)
                    self.heavy_bins[best]['t'] += item
                    return best
                for k, v in self.light_bins.items():
                    rem = capacity - v['t']
                    if item <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = k
                if best >= 0:
                    self.light_bins[best]['i'].append(item)
                    self.light_bins[best]['t'] += item
                    return best
                b = self.nid; self.nid += 1
                self.light_bins[b] = {'i': [item], 't': item}
                return b

        def get_bins(self):
            a = {}; a.update(self.heavy_bins); a.update(self.light_bins)
            return [list(a[b]['i']) for b in sorted(a)]

    return Packer()
