def create_packer(capacity):
    """Adaptive Classified Best-Fit: synthesizes Best Fit's greedy optimization
    with Harmonic's classification. Uses dict-based bin registry with adaptive
    tier boundaries that shift based on observed item statistics.
    Cross-tier placement allowed only for very tight fits."""

    class Packer:
        def __init__(self):
            self.bin_registry = {}  # bin_id -> {sum, items, tier}
            self.next_id = 0
            self.tier_bins = {0: [], 1: [], 2: [], 3: []}  # tier -> [bin_ids]
            # Adaptive boundaries start at even quarters
            self.tier_bounds = [0.0, 0.25, 0.5, 0.75, capacity]
            self.item_count = 0
            self.item_sum = 0.0
            self.item_sq_sum = 0.0

        def _get_tier(self, item):
            ratio = item / capacity
            if ratio > 0.75:
                return 3
            elif ratio > 0.5:
                return 2
            elif ratio > 0.25:
                return 1
            else:
                return 0

        def _adapt_boundaries(self):
            if self.item_count < 10:
                return
            mean = self.item_sum / self.item_count
            var = max(0, self.item_sq_sum / self.item_count - mean * mean)
            std = var ** 0.5
            # Shift middle boundary toward mean
            mid = mean / capacity
            self.tier_bounds[2] = max(0.3, min(0.7, mid)) * capacity

        def place(self, item):
            self.item_count += 1
            self.item_sum += item
            self.item_sq_sum += item * item
            if self.item_count % 20 == 0:
                self._adapt_boundaries()

            tier = self._get_tier(item)

            # Strategy: try own tier first (best fit), then adjacent tiers
            best_id = -1
            best_remaining = capacity + 1

            # Search order: own tier, then complementary tiers
            search_order = [tier]
            if tier == 0:
                search_order += [2, 1, 3]  # small items try half-full bins
            elif tier == 1:
                search_order += [0, 2, 3]
            elif tier == 2:
                search_order += [1, 3, 0]
            else:
                search_order += [1, 0, 2]  # large items try bins with small items

            for t in search_order:
                for bid in self.tier_bins.get(t, []):
                    info = self.bin_registry[bid]
                    remaining = capacity - info['sum']
                    if item <= remaining + 1e-9:
                        # For cross-tier, only accept tight fits
                        if t != tier and remaining - item > 0.15 * capacity:
                            continue
                        if remaining < best_remaining:
                            best_remaining = remaining
                            best_id = bid

            if best_id >= 0:
                self.bin_registry[best_id]['items'].append(item)
                self.bin_registry[best_id]['sum'] += item
                return best_id

            # Open new bin
            bid = self.next_id
            self.next_id += 1
            self.bin_registry[bid] = {'sum': item, 'items': [item], 'tier': tier}
            self.tier_bins[tier].append(bid)
            return bid

        def get_bins(self):
            return [list(info['items']) for info in self.bin_registry.values()]

    return Packer()
