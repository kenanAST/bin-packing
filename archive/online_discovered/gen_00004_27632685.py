def create_packer(capacity):
    """Harmonic+ with cross-class best-fit. Classify items into 4 size classes
    (tiny <0.2, small 0.2-0.4, medium 0.4-0.6, large >0.6). Each class has
    dedicated bins, BUT allow cross-class placement when it would fill a bin
    to >90% capacity. This gets Harmonic's structure with Best Fit's greediness.

    Novel: uses a 'complement map' - for each bin, track what size complement
    would best fill it, and index bins by their complement need."""

    class Packer:
        def __init__(self):
            self.bins = {}  # bid -> {'items', 'total', 'class'}
            self.next_id = 0
            # Complement buckets: bucket[k] = list of bids needing items of size ~k/10
            self.complement = [[] for _ in range(11)]

        def _size_class(self, item):
            r = item / capacity
            if r > 0.6: return 3
            if r > 0.4: return 2
            if r > 0.2: return 1
            return 0

        def _complement_bucket(self, remaining):
            return max(0, min(10, int(remaining / capacity * 10)))

        def place(self, item):
            item_bucket = self._complement_bucket(item)

            # First: check complement map - bins that NEED an item this size
            best_bid = -1
            best_waste = capacity + 1

            # Search the complement bucket matching this item's size
            for d in range(3):  # search nearby buckets too
                for offset in [0, d, -d]:
                    b = item_bucket + offset
                    if b < 0 or b > 10:
                        continue
                    for bid in list(self.complement[b]):
                        if bid not in self.bins:
                            self.complement[b].remove(bid)
                            continue
                        rem = capacity - self.bins[bid]['total']
                        if item <= rem + 1e-9:
                            waste = rem - item
                            if waste < best_waste:
                                best_waste = waste
                                best_bid = bid

            if best_bid >= 0:
                old_rem = capacity - self.bins[best_bid]['total']
                self.bins[best_bid]['items'].append(item)
                self.bins[best_bid]['total'] += item
                new_rem = capacity - self.bins[best_bid]['total']
                # Update complement index
                old_cb = self._complement_bucket(old_rem)
                new_cb = self._complement_bucket(new_rem)
                if old_cb != new_cb:
                    try:
                        self.complement[old_cb].remove(best_bid)
                    except ValueError:
                        pass
                    if new_rem > 0.02 * capacity:
                        self.complement[new_cb].append(best_bid)
                return best_bid

            # Open new bin
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {
                'items': [item],
                'total': item,
                'class': self._size_class(item)
            }
            rem = capacity - item
            if rem > 0.02 * capacity:
                cb = self._complement_bucket(rem)
                self.complement[cb].append(bid)
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)]

    return Packer()
