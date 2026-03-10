def create_packer(capacity):
    """Threshold Cascade: Use multiple threshold levels. Items are placed based
    on a cascade of conditions, each with different bin selection logic:
    1. If item > 0.7*cap: open new bin (will be hard to pair)
    2. If item > 0.5*cap: find bin with remaining in [item, item+0.15*cap]
    3. If item > 0.3*cap: find bin with remaining in [item, item+0.3*cap]
    4. If item <= 0.3*cap: find bin with remaining closest to item (tight fill)

    This cascading structure creates distinct packing behavior for each
    size class and avoids the single-rule approach of best/worst fit."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0

        def _find_in_range(self, item, min_rem, max_rem):
            """Find bin with remaining capacity in [min_rem, max_rem], closest to min_rem."""
            best = -1
            best_rem = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if rem >= min_rem - 1e-9 and rem <= max_rem + 1e-9:
                    if item <= rem + 1e-9 and rem < best_rem:
                        best_rem = rem
                        best = bid
            return best

        def _find_closest(self, item):
            """Find bin with remaining capacity closest to item (tight fill)."""
            best = -1
            best_diff = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9:
                    diff = rem - item
                    if diff < best_diff:
                        best_diff = diff
                        best = bid
            return best

        def place(self, item):
            ratio = item / capacity

            if ratio > 0.7:
                # Very large: own bin (pairing unlikely)
                return self._new_bin(item)

            elif ratio > 0.5:
                # Large: find narrow fit range
                bid = self._find_in_range(item, item, item + 0.15 * capacity)
                if bid < 0:
                    bid = self._find_closest(item)
                if bid >= 0:
                    self.bins[bid]['items'].append(item)
                    self.bins[bid]['total'] += item
                    return bid
                return self._new_bin(item)

            elif ratio > 0.3:
                # Medium: wider fit range
                bid = self._find_in_range(item, item, item + 0.3 * capacity)
                if bid < 0:
                    bid = self._find_closest(item)
                if bid >= 0:
                    self.bins[bid]['items'].append(item)
                    self.bins[bid]['total'] += item
                    return bid
                return self._new_bin(item)

            else:
                # Small: tight fill
                bid = self._find_closest(item)
                if bid >= 0:
                    self.bins[bid]['items'].append(item)
                    self.bins[bid]['total'] += item
                    return bid
                return self._new_bin(item)

        def _new_bin(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)]

    return Packer()
