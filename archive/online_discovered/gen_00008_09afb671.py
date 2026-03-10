def create_packer(capacity):
    """Exponential Backoff Packing: When an item can't find a good fit
    (waste > threshold), don't just take the best available — instead,
    sometimes deliberately open a new bin. The probability of opening
    a new bin follows exponential backoff: starts high and decreases
    as more items are placed.

    Uses a deterministic pseudo-random sequence based on item count
    to avoid actual randomness while still varying behavior."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.n = 0

        def _should_open_new(self, waste_ratio):
            """Deterministic but varying decision: open new bin?"""
            # Threshold decreases over time (less willing to open new bins later)
            threshold = 0.4 / (1 + self.n / 50.0)

            # If waste ratio is above threshold, open new bin
            # This means early items with poor fits get new bins (spreading)
            # Late items accept worse fits (packing)
            return waste_ratio > threshold and waste_ratio > 0.15

        def place(self, item):
            self.n += 1

            best_bid = -1
            best_rem = capacity + 1

            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best_bid = bid

            if best_bid >= 0:
                waste_ratio = (best_rem - item) / capacity

                if waste_ratio < 0.03:
                    # Great fit - always take it
                    self.bins[best_bid]['items'].append(item)
                    self.bins[best_bid]['total'] += item
                    return best_bid

                if self._should_open_new(waste_ratio):
                    # Poor fit - open new bin instead
                    return self._new_bin(item)

                # Acceptable fit
                self.bins[best_bid]['items'].append(item)
                self.bins[best_bid]['total'] += item
                return best_bid

            return self._new_bin(item)

        def _new_bin(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)]

    return Packer()
