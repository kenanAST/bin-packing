def create_packer(capacity):
    """First Principles: Violate two common assumptions:
    1. 'Every bin is a candidate for every item' - instead, bins have target fill ranges
    2. 'Selection is based on current state only' - instead, use exponential moving average
       of item sizes to predict future items and reserve appropriate space.

    Uses a target-fill-zone system: bins are assigned a target zone based on
    what complement size we expect next. If we've been seeing small items,
    keep bins with space for large items."""

    class Packer:
        def __init__(self):
            self.bins = {}  # id -> {'items': [], 'total': float, 'target_fill': float}
            self.next_id = 0
            self.ema_size = 0.5  # exponential moving average of item sizes
            self.ema_alpha = 0.15
            self.items_seen = 0

        def place(self, item):
            self.items_seen += 1
            self.ema_size = self.ema_alpha * item + (1 - self.ema_alpha) * self.ema_size

            # Predict likely complement: if items are trending small, expect large later
            predicted_next = self.ema_size
            ideal_complement = capacity - predicted_next  # leave room for predicted item

            ratio = item / capacity

            # Score bins: prefer bins where adding this item leaves room close to predicted_next
            best_id = -1
            best_score = float('inf')

            for bid, info in self.bins.items():
                remaining = capacity - info['total']
                if item > remaining + 1e-9:
                    continue

                after_remaining = remaining - item

                if after_remaining < 0.02 * capacity:
                    # Nearly fills bin - excellent
                    score = -1000 + after_remaining
                else:
                    # How close is the remaining space to what we predict we'll need?
                    gap_from_predicted = abs(after_remaining - predicted_next)
                    # Penalty for leaving awkward remaining space (not useful for predicted items)
                    score = gap_from_predicted
                    # Bonus for bins that are already fairly full
                    score -= info['total'] / capacity * 0.3

                if score < best_score:
                    best_score = score
                    best_id = bid

            if best_id >= 0:
                self.bins[best_id]['items'].append(item)
                self.bins[best_id]['total'] += item
                return best_id

            # Open new bin
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(info['items']) for info in self.bins.values()]

    return Packer()
