def create_packer(capacity):
    """Round-Robin with Overflow: Radically simple. Maintain K bins in rotation.
    Place each item in the next bin in round-robin order IF it fits.
    If it doesn't fit, try the next one, etc. If none fit, open a new set of K bins.

    This is intentionally different from any greedy approach and should
    produce very different behavioral signatures."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.k = 4  # round-robin pool size
            self.pool = []  # current active pool of bin IDs
            self.cursor = 0

        def place(self, item):
            if not self.pool:
                return self._new_pool(item)

            # Try round-robin starting from cursor
            for attempt in range(len(self.pool)):
                idx = (self.cursor + attempt) % len(self.pool)
                bid = self.pool[idx]
                rem = capacity - self.bins[bid]['total']
                if item <= rem + 1e-9:
                    self.bins[bid]['items'].append(item)
                    self.bins[bid]['total'] += item
                    self.cursor = (idx + 1) % len(self.pool)

                    # Remove from pool if nearly full
                    if capacity - self.bins[bid]['total'] < 0.05 * capacity:
                        self.pool.pop(idx)
                        if self.pool:
                            self.cursor = self.cursor % len(self.pool)
                    return bid

            # No bin in pool fits - start new pool
            return self._new_pool(item)

        def _new_pool(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            self.pool = [bid]
            # Pre-create empty bins for the pool
            for _ in range(self.k - 1):
                new_bid = self.next_id
                self.next_id += 1
                self.bins[new_bid] = {'items': [], 'total': 0.0}
                self.pool.append(new_bid)
            self.cursor = 1
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)
                    if self.bins[bid]['items']]

    return Packer()
