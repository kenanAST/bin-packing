def create_packer(capacity):
    """Majority-size-aware: track the most common item size bucket.
    For items matching the majority size, use worst-fit (spread them).
    For items NOT matching majority, use best-fit (pack them tightly
    into existing bins). This prevents the common case from clustering."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.counts = [0] * 5  # 5 size buckets

        def _bucket(self, item):
            return min(4, int(item / capacity * 5))

        def _majority(self):
            return max(range(5), key=lambda i: self.counts[i])

        def place(self, item):
            b = self._bucket(item)
            self.counts[b] += 1

            if b == self._majority() and sum(self.counts) > 5:
                return self._worst_fit(item)
            return self._best_fit(item)

        def _best_fit(self, item):
            best = -1
            best_rem = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['t']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best = bid
            if best >= 0:
                self.bins[best]['i'].append(item)
                self.bins[best]['t'] += item
                return best
            return self._new(item)

        def _worst_fit(self, item):
            best = -1
            best_rem = -1
            for bid, info in self.bins.items():
                rem = capacity - info['t']
                if item <= rem + 1e-9 and rem > best_rem:
                    best_rem = rem
                    best = bid
            if best >= 0:
                self.bins[best]['i'].append(item)
                self.bins[best]['t'] += item
                return best
            return self._new(item)

        def _new(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'i': [item], 't': item}
            return bid

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
