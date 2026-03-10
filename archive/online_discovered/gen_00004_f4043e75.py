def create_packer(capacity):
    """Constraint: Each bin can hold at most 2 items. This forces pairing
    optimization. Use a waiting pool: when an item arrives, either pair it
    with a waiting item that complements it best, or add it to the pool.
    Pool has max size; when full, force-pair the two best-matching items.

    This is radically different from all archive members."""

    class Packer:
        def __init__(self):
            self.bins = []  # completed bins
            self.pool = {}  # id -> item_size (waiting for a partner)
            self.next_pool_id = 0
            self.max_pool = 15

        def place(self, item):
            # Try to pair with best complement in pool
            best_pid = None
            best_waste = capacity + 1

            for pid, pitem in self.pool.items():
                total = pitem + item
                if total <= capacity + 1e-9:
                    waste = capacity - total
                    if waste < best_waste:
                        best_waste = waste
                        best_pid = pid

            if best_pid is not None and best_waste < 0.3 * capacity:
                # Good pairing found
                partner = self.pool.pop(best_pid)
                self.bins.append([partner, item])
                return len(self.bins) - 1

            # No good pair - add to pool
            pid = self.next_pool_id
            self.next_pool_id += 1
            self.pool[pid] = item

            # If pool overflow, force-pair the two best items
            if len(self.pool) > self.max_pool:
                self._force_pair()

            return len(self.bins) + pid  # temporary index

        def _force_pair(self):
            """Force the best pair out of the pool."""
            items = list(self.pool.items())
            best_pair = None
            best_waste = capacity + 1

            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    total = items[i][1] + items[j][1]
                    if total <= capacity + 1e-9:
                        waste = capacity - total
                        if waste < best_waste:
                            best_waste = waste
                            best_pair = (items[i][0], items[j][0])

            if best_pair is not None:
                a, b = best_pair
                self.bins.append([self.pool.pop(a), self.pool.pop(b)])
            else:
                # Can't pair any two - eject largest as singleton
                largest_pid = max(self.pool, key=lambda p: self.pool[p])
                self.bins.append([self.pool.pop(largest_pid)])

        def get_bins(self):
            result = [list(b) for b in self.bins]
            # Remaining pool items become singleton bins
            for item in self.pool.values():
                result.append([item])
            return result

    return Packer()
