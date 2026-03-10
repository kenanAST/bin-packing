def create_packer(capacity):
    """Fibonacci Spacing: Instead of greedy bin selection, maintain bins at
    Fibonacci-ratio fill levels. When placing an item, prefer bins whose
    fill ratio after placement would be closest to a Fibonacci ratio
    (0.618, 0.382, 0.236, etc). This creates a natural spacing that
    leaves room for complementary items.

    Completely novel scoring function based on golden ratio."""

    FIB_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.764, 0.854, 0.927, 0.972, 1.0]

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0

        def _fib_score(self, fill_ratio):
            """How close is this fill ratio to a Fibonacci level?"""
            return min(abs(fill_ratio - f) for f in FIB_RATIOS)

        def place(self, item):
            best_bid = -1
            best_score = float('inf')

            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue

                new_fill = (info['total'] + item) / capacity

                if new_fill > 0.97:
                    # Nearly full - always prefer this
                    score = -1000 + (1.0 - new_fill)
                else:
                    # Score: closeness to Fibonacci ratio (lower = better)
                    fib_dist = self._fib_score(new_fill)
                    # Also factor in how full the bin is (prefer fuller bins)
                    score = fib_dist - new_fill * 0.3

                if score < best_score:
                    best_score = score
                    best_bid = bid

            if best_bid >= 0:
                self.bins[best_bid]['items'].append(item)
                self.bins[best_bid]['total'] += item
                return best_bid

            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)]

    return Packer()
