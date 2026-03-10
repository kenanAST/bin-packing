def create_packer(capacity):
    """Novelty Search: Completely different structure. Use a binary-tree-like
    bin selection. Bins are organized by their remaining capacity in a sorted
    structure (list of lists by decile). Items are matched to the decile of
    their complement (capacity - item) to find the most useful bin.

    Key insight: instead of 'which bin fits this item best', ask
    'which bin would this item COMPLETE best'."""

    class Packer:
        def __init__(self):
            # 10 decile buckets: bucket[k] = bins with remaining in [k/10, (k+1)/10) * capacity
            self.deciles = [[] for _ in range(11)]
            self.bin_data = {}  # bid -> {'items': [], 'total': float}
            self.next_id = 0

        def _decile(self, remaining):
            d = int(remaining / capacity * 10)
            return max(0, min(10, d))

        def _move_bin(self, bid, old_rem, new_rem):
            old_d = self._decile(old_rem)
            new_d = self._decile(new_rem)
            if old_d != new_d:
                try:
                    self.deciles[old_d].remove(bid)
                except ValueError:
                    pass
                self.deciles[new_d].append(bid)

        def place(self, item):
            # Target: find bin where remaining ≈ item (perfect completion)
            target_d = self._decile(item)

            # Search outward from target decile
            best_bid = -1
            best_waste = capacity + 1

            for offset in range(11):
                for d in [target_d + offset, target_d - offset]:
                    if d < 0 or d > 10:
                        continue
                    for bid in self.deciles[d]:
                        rem = capacity - self.bin_data[bid]['total']
                        if item <= rem + 1e-9:
                            waste = rem - item  # how much space wasted after placing
                            if waste < best_waste:
                                best_waste = waste
                                best_bid = bid
                    if best_bid >= 0 and best_waste < 0.1 * capacity:
                        break  # good enough match found
                if best_bid >= 0 and best_waste < 0.1 * capacity:
                    break

            if best_bid >= 0:
                old_rem = capacity - self.bin_data[best_bid]['total']
                self.bin_data[best_bid]['items'].append(item)
                self.bin_data[best_bid]['total'] += item
                new_rem = old_rem - item
                self._move_bin(best_bid, old_rem, new_rem)
                return best_bid

            # New bin
            bid = self.next_id
            self.next_id += 1
            self.bin_data[bid] = {'items': [item], 'total': item}
            d = self._decile(capacity - item)
            self.deciles[d].append(bid)
            return bid

        def get_bins(self):
            return [list(self.bin_data[bid]['items']) for bid in sorted(self.bin_data)]

    return Packer()
