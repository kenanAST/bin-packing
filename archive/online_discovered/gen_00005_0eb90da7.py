def create_packer(capacity):
    """Temperature-Based Packing: Bins have a 'temperature' that decays over time.
    Hot bins (recently created/modified) are preferred for similar-sized items.
    Cold bins are preferred for complementary items.

    This creates temporal locality: recent items cluster, but old bins
    attract complements. Mimics simulated annealing's acceptance probability."""
    import math

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.clock = 0
            self.last_modified = {}  # bid -> clock tick

        def place(self, item):
            self.clock += 1

            best_bid = -1
            best_score = float('inf')

            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue

                age = self.clock - self.last_modified[bid]
                temperature = math.exp(-age / 10.0)  # decays over ~10 items

                waste = rem - item
                fill_after = (info['total'] + item) / capacity

                if waste < 0.03 * capacity:
                    score = -1000  # nearly fills
                else:
                    # Hot bins: prefer tight fit (similar items cluster)
                    # Cold bins: any fit is good (they need attention)
                    tight_score = waste / capacity
                    urgency = 1.0 - temperature  # cold bins are more urgent

                    score = tight_score * temperature + (1.0 - fill_after) * urgency

                if score < best_score:
                    best_score = score
                    best_bid = bid

            if best_bid >= 0:
                self.bins[best_bid]['items'].append(item)
                self.bins[best_bid]['total'] += item
                self.last_modified[best_bid] = self.clock
                return best_bid

            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            self.last_modified[bid] = self.clock
            return bid

        def get_bins(self):
            return [list(self.bins[bid]['items']) for bid in sorted(self.bins)]

    return Packer()
