def create_packer(capacity):
    """Ratio-band: classify bins by fill ratio into bands [0-0.33, 0.33-0.66, 0.66-1].
    Small items go to high-band bins, large items go to low-band bins.
    Forces complementary pairing."""

    class Packer:
        def __init__(self):
            self.bands = {0: {}, 1: {}, 2: {}}
            self.all_bins = {}
            self.nid = 0

        def _band(self, fill):
            if fill > 0.66: return 2
            if fill > 0.33: return 1
            return 0

        def _move(self, bid, old_fill, new_fill):
            ob, nb = self._band(old_fill), self._band(new_fill)
            if ob != nb:
                if bid in self.bands[ob]: del self.bands[ob][bid]
                self.bands[nb][bid] = True

        def _search(self, item, band):
            best, best_r = -1, capacity + 1
            bids = list(self.bands[band].keys())
            for bid in bids:
                if bid not in self.all_bins: continue
                rem = capacity - self.all_bins[bid]['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best = bid
            return best

        def place(self, item):
            ratio = item / capacity
            if ratio > 0.5:
                order = [0, 1, 2]
            elif ratio > 0.25:
                order = [1, 2, 0]
            else:
                order = [2, 1, 0]

            for band in order:
                bid = self._search(item, band)
                if bid >= 0:
                    old_f = self.all_bins[bid]['t'] / capacity
                    self.all_bins[bid]['i'].append(item)
                    self.all_bins[bid]['t'] += item
                    new_f = self.all_bins[bid]['t'] / capacity
                    self._move(bid, old_f, new_f)
                    return bid

            bid = self.nid; self.nid += 1
            self.all_bins[bid] = {'i': [item], 't': item}
            b = self._band(item / capacity)
            self.bands[b][bid] = True
            return bid

        def get_bins(self):
            return [list(self.all_bins[b]['i']) for b in sorted(self.all_bins)]

    return Packer()
