def create_packer(capacity):
    """Cross-domain: Combine adaptive window (from candidate_004) with
    prediction-based scoring (from candidate_005). Use a bounded pool of
    active bins with a scoring function that considers both tightness of fit
    AND predicted future utility of remaining space.

    Novel element: 'regret minimization' - estimate how much we'd regret
    placing this item here vs opening a new bin, based on observed statistics."""

    class Packer:
        def __init__(self):
            self.active = {}   # bid -> {'items', 'total'}
            self.closed = {}   # bid -> {'items', 'total'}
            self.next_id = 0
            self.max_active = 20
            self.ema = 0.5
            self.ema2 = 0.25  # EMA of squared sizes
            self.alpha = 0.1
            self.n = 0

        def _predicted_std(self):
            var = max(0, self.ema2 - self.ema * self.ema)
            return var ** 0.5

        def place(self, item):
            self.n += 1
            self.ema = self.alpha * item + (1 - self.alpha) * self.ema
            self.ema2 = self.alpha * item * item + (1 - self.alpha) * self.ema2

            predicted_mean = self.ema
            predicted_std = self._predicted_std()

            best_bid = -1
            best_score = float('inf')

            for bid, info in self.active.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue

                after = rem - item

                # Score 1: completion bonus (filling bin is always good)
                if after < 0.03 * capacity:
                    score = -10000
                else:
                    # Regret: how likely can we fill 'after' with future items?
                    # P(future item ≈ after) ~ closeness to predicted_mean ± std
                    dist_to_mean = abs(after - predicted_mean)
                    fillability = max(0.01, 1.0 - dist_to_mean / (predicted_std + 0.1))

                    # Also consider: can 2 future items fill 'after'?
                    dist_to_2mean = abs(after - 2 * predicted_mean)
                    fillability_2 = max(0.01, 1.0 - dist_to_2mean / (2 * predicted_std + 0.2))

                    fillability = max(fillability, fillability_2 * 0.8)

                    # Lower score = better. High fillability = low regret
                    score = -fillability * 100 + after * 0.1

                if score < best_score:
                    best_score = score
                    best_bid = bid

            if best_bid >= 0:
                self.active[best_bid]['items'].append(item)
                self.active[best_bid]['total'] += item
                # Close nearly-full bins
                if capacity - self.active[best_bid]['total'] < 0.03 * capacity:
                    self.closed[best_bid] = self.active.pop(best_bid)
                return best_bid

            # Evict least-useful active bin if at capacity
            if len(self.active) >= self.max_active:
                # Close the fullest bin (least useful for future items)
                fullest = max(self.active, key=lambda b: self.active[b]['total'])
                self.closed[fullest] = self.active.pop(fullest)

            bid = self.next_id
            self.next_id += 1
            self.active[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            all_b = {}
            all_b.update(self.active)
            all_b.update(self.closed)
            return [list(all_b[bid]['items']) for bid in sorted(all_b)]

    return Packer()
