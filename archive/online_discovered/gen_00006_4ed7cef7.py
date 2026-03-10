def create_packer(capacity):
    """Gradient Descent Packer: Each bin has a 'desirability' score that
    gets updated after each placement. The score is based on how well
    the bin's remaining space matches the running distribution of items.

    Bins with remaining space that matches common item sizes get higher
    desirability. Place items in the most desirable bin.

    Novel: uses a continuous score that evolves, unlike static greedy rules."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.desirability = {}  # bid -> score
            # Track distribution of item sizes in 20 buckets
            self.size_hist = [0.0] * 20
            self.n = 0

        def _bucket(self, val):
            return max(0, min(19, int(val / capacity * 20)))

        def _update_hist(self, item):
            self.n += 1
            b = self._bucket(item)
            # Exponential decay of old observations
            for i in range(20):
                self.size_hist[i] *= 0.995
            self.size_hist[b] += 1.0

        def _compute_desirability(self, bid):
            """How likely is it that future items will fill this bin well?"""
            rem = capacity - self.bins[bid]['total']
            if rem < 0.02 * capacity:
                return -100  # already full, don't bother

            # How common are items that would fit well in this remaining space?
            rem_bucket = self._bucket(rem)
            # Sum nearby buckets (items close to remaining space)
            score = 0.0
            total_hist = sum(self.size_hist) + 0.001
            for offset in range(-2, 3):
                b = rem_bucket + offset
                if 0 <= b < 20:
                    weight = 1.0 / (1 + abs(offset))
                    score += self.size_hist[b] / total_hist * weight

            # Also: can two common items fill the space?
            half_rem_bucket = self._bucket(rem / 2)
            for offset in range(-1, 2):
                b = half_rem_bucket + offset
                if 0 <= b < 20:
                    score += self.size_hist[b] / total_hist * 0.3

            return score

        def place(self, item):
            self._update_hist(item)

            best_bid = -1
            best_score = -float('inf')

            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue

                after_rem = rem - item

                if after_rem < 0.02 * capacity:
                    # Fills bin - very high score
                    score = 10000
                else:
                    # Score = desirability of remaining space after placement
                    after_bucket = self._bucket(after_rem)
                    total_hist = sum(self.size_hist) + 0.001
                    score = 0.0
                    for offset in range(-2, 3):
                        b = after_bucket + offset
                        if 0 <= b < 20:
                            weight = 1.0 / (1 + abs(offset))
                            score += self.size_hist[b] / total_hist * weight

                    # Bonus for fuller bins
                    score += info['total'] / capacity * 0.5

                if score > best_score:
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
