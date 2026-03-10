def create_packer(capacity):
    """Weighted Multi-Objective: Score bins using a weighted combination of:
    1. Tightness (how well item fills remaining space)
    2. Bin maturity (prefer bins that are already fairly full)
    3. Diversity penalty (avoid placing too many similar items in one bin)

    The weights adapt based on how far through the item stream we are
    (estimated from items seen). Early: spread. Late: pack tight."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.n = 0
            self.sum_sizes = 0.0

        def place(self, item):
            self.n += 1
            self.sum_sizes += item

            # Adaptive weights
            # Early items: emphasize maturity (fill existing bins evenly)
            # Later: emphasize tightness (minimize waste)
            phase = min(1.0, self.n / 200.0)
            w_tight = 0.3 + 0.5 * phase    # 0.3 -> 0.8
            w_mature = 0.5 - 0.3 * phase    # 0.5 -> 0.2
            w_diverse = 0.2 - 0.2 * phase   # 0.2 -> 0.0

            best_bid = -1
            best_score = -float('inf')

            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item > rem + 1e-9:
                    continue

                waste = rem - item
                fill_ratio = info['total'] / capacity

                # Tightness: closer to 0 waste = better
                s_tight = 1.0 - waste / capacity

                # Maturity: fuller bins are better
                s_mature = fill_ratio

                # Diversity: penalize if item is very similar to existing items
                n_items = len(info['items'])
                if n_items > 0:
                    avg_in_bin = info['total'] / n_items
                    similarity = 1.0 - abs(item - avg_in_bin) / capacity
                    s_diverse = 1.0 - similarity  # prefer dissimilar
                else:
                    s_diverse = 0.5

                score = w_tight * s_tight + w_mature * s_mature + w_diverse * s_diverse

                # Big bonus for nearly filling
                if waste < 0.03 * capacity:
                    score += 10

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
