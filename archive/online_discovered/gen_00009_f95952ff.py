def create_packer(capacity):
    """Bin Age + Fill Urgency scoring. Novel scoring: each bin gets a score
    that combines how full it is with how long it's been open (age).
    Old, partially-filled bins are 'urgent' and get priority.

    Score = fill_ratio * (1 + age_factor) where age_factor grows with
    the number of items since the bin was last modified.

    Also: bins that are >90% full are 'frozen' and skipped in searches
    to reduce scan time and create behavioral differences."""

    class Packer:
        def __init__(self):
            self.active = {}   # bid -> {'items', 'total', 'last_touch'}
            self.frozen = {}   # bid -> {'items', 'total'}
            self.next_id = 0
            self.clock = 0

        def place(self, item):
            self.clock += 1

            best_bid = -1
            best_score = -1

            for bid, info in self.active.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue

                waste_after = rem - item
                fill_after = (info['total'] + item) / capacity
                age = self.clock - info['last_touch']

                if waste_after < 0.03 * capacity:
                    score = 10000  # nearly fills - always best
                else:
                    # Urgency increases with age
                    age_factor = min(2.0, age / 20.0)
                    # Fill quality
                    fill_score = fill_after
                    # Tightness
                    tight_score = 1.0 - waste_after / capacity

                    score = (fill_score + tight_score) * (1 + age_factor)

                if score > best_score:
                    best_score = score
                    best_bid = bid

            if best_bid >= 0:
                self.active[best_bid]['items'].append(item)
                self.active[best_bid]['total'] += item
                self.active[best_bid]['last_touch'] = self.clock

                # Freeze if very full
                if capacity - self.active[best_bid]['total'] < 0.05 * capacity:
                    info = self.active.pop(best_bid)
                    self.frozen[best_bid] = {'items': info['items'], 'total': info['total']}

                return best_bid

            # Try frozen bins as last resort (rare - only if item is very small)
            for bid, info in self.frozen.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9:
                    info['items'].append(item)
                    info['total'] += item
                    return bid

            bid = self.next_id
            self.next_id += 1
            self.active[bid] = {'items': [item], 'total': item, 'last_touch': self.clock}
            return bid

        def get_bins(self):
            all_b = {}
            for bid, info in self.active.items():
                all_b[bid] = info['items']
            for bid, info in self.frozen.items():
                all_b[bid] = info['items']
            return [list(all_b[bid]) for bid in sorted(all_b)]

    return Packer()
