def create_packer(capacity):
    """Reservation Strategy targeting uniform_large increasing order.
    Key insight: when items are large (0.3-0.9) and arrive small-first,
    don't pack small items tightly. Instead, spread them across bins
    leaving room for the large items that come later.

    Uses a 'reservation threshold' that adapts: early items are spread
    (worst-fit-like), later items are packed tightly (best-fit-like).
    The transition point is estimated from observed item sizes."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.n = 0
            self.sum_x = 0.0
            self.max_seen = 0.0
            self.min_seen = capacity
            self.trend = 0.0  # positive = items getting larger
            self.last_item = None

        def place(self, item):
            self.n += 1
            self.sum_x += item
            self.max_seen = max(self.max_seen, item)
            self.min_seen = min(self.min_seen, item)
            if self.last_item is not None:
                self.trend = 0.9 * self.trend + 0.1 * (item - self.last_item)
            self.last_item = item

            ratio = item / capacity
            mean = self.sum_x / self.n

            # Detect increasing trend: spread early items
            if self.trend > 0.01 and ratio < 0.5:
                # Items getting larger - reserve space
                return self._spread_fit(item)
            elif ratio > 0.5:
                # Large item: find tightest fit
                return self._best_fit(item)
            elif self.n > 20 and mean > 0.4 * capacity:
                # We're in a large-item distribution - be strategic
                return self._complement_fit(item)
            else:
                return self._best_fit(item)

        def _spread_fit(self, item):
            """Place in bin with MOST remaining space (worst fit),
            but only if the remaining space after placement can still
            accommodate the expected complement."""
            mean = self.sum_x / self.n
            expected_large = min(capacity, mean + (self.max_seen - mean) * 0.5)

            best_id = -1
            best_rem = -1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue
                after = rem - item
                # Only place here if remaining space can fit expected large item
                if after >= expected_large - 1e-9 or after < 0.05 * capacity:
                    if rem > best_rem:
                        best_rem = rem
                        best_id = bid

            if best_id >= 0:
                self.bins[best_id]['items'].append(item)
                self.bins[best_id]['total'] += item
                return best_id
            return self._new_bin(item)

        def _complement_fit(self, item):
            """Find bin where item + existing ≈ capacity."""
            best_id = -1
            best_waste = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue
                waste = rem - item
                if waste < best_waste:
                    best_waste = waste
                    best_id = bid
            if best_id >= 0:
                self.bins[best_id]['items'].append(item)
                self.bins[best_id]['total'] += item
                return best_id
            return self._new_bin(item)

        def _best_fit(self, item):
            best_id = -1
            best_rem = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best_id = bid
            if best_id >= 0:
                self.bins[best_id]['items'].append(item)
                self.bins[best_id]['total'] += item
                return best_id
            return self._new_bin(item)

        def _new_bin(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(info['items']) for info in self.bins.values()]

    return Packer()
