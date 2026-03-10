def create_packer(capacity):
    """Hybrid Best-Fit with Increasing-Order Mitigation.
    Core insight: best_fit's weakness is increasing order where small items
    fill bins to ~50% then large items can't pair. Solution:

    Track trend direction. When items are increasing:
    - Small items (<0.4*cap): use WORST fit (spread across bins, leave room)
    - Large items (>0.4*cap): use BEST fit (pack tightly)

    When items are decreasing or random: pure best fit.

    This should beat best_fit on increasing while matching it elsewhere."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.n = 0
            self.trend_ema = 0.0
            self.last_item = None

        def place(self, item):
            self.n += 1
            if self.last_item is not None:
                delta = item - self.last_item
                self.trend_ema = 0.85 * self.trend_ema + 0.15 * delta
            self.last_item = item

            ratio = item / capacity
            increasing = self.trend_ema > 0.005  # items getting larger

            if increasing and ratio < 0.4:
                # Spread small items when more large items are coming
                return self._worst_fit(item)
            else:
                return self._best_fit(item)

        def _best_fit(self, item):
            best = -1
            best_rem = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best = bid
            if best >= 0:
                self.bins[best]['items'].append(item)
                self.bins[best]['total'] += item
                return best
            return self._new_bin(item)

        def _worst_fit(self, item):
            best = -1
            best_rem = -1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem > best_rem:
                    best_rem = rem
                    best = bid
            if best >= 0:
                self.bins[best]['items'].append(item)
                self.bins[best]['total'] += item
                return best
            return self._new_bin(item)

        def _new_bin(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)]

    return Packer()
