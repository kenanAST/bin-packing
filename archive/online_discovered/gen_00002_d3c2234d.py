def create_packer(capacity):
    """Outsider Perspective: Think like a Tetris speedrunner.
    In Tetris, you keep the board flat and leave one column open for the long piece.
    Translation: keep bins at similar fill levels, but always maintain a few
    'slot bins' with specific remaining capacities for common item sizes.

    Track a histogram of item sizes seen, and maintain 'slot' bins whose
    remaining space matches the most common upcoming item sizes."""

    class Packer:
        def __init__(self):
            # Bins stored as dict with fill info
            self.active = {}  # id -> {'items': [], 'total': float}
            self.sealed = {}  # id -> {'items': [], 'total': float}
            self.next_id = 0
            # Histogram: 10 buckets for item sizes
            self.hist = [0] * 10
            self.items_seen = 0

        def _bucket(self, item):
            return min(9, int(item / capacity * 10))

        def _most_common_size(self):
            if self.items_seen < 3:
                return capacity * 0.35
            best_b = max(range(10), key=lambda b: self.hist[b])
            return (best_b + 0.5) / 10 * capacity

        def place(self, item):
            self.items_seen += 1
            self.hist[self._bucket(item)] += 1

            common_size = self._most_common_size()

            best_id = -1
            best_score = float('inf')

            for bid, info in self.active.items():
                remaining = capacity - info['total']
                if item > remaining + 1e-9:
                    continue

                after = remaining - item

                if after < 0.02 * capacity:
                    # Nearly fills - great, score very low
                    score = -2000
                elif abs(after - common_size) < 0.08 * capacity:
                    # Leaves a slot for the most common size - good!
                    score = -1000 + abs(after - common_size)
                elif abs(after - item) < 0.05 * capacity:
                    # Leaves room for another item like this one
                    score = -500
                else:
                    # Best fit as fallback
                    score = remaining

                if score < best_score:
                    best_score = score
                    best_id = bid

            if best_id >= 0:
                self.active[best_id]['items'].append(item)
                self.active[best_id]['total'] += item
                # Seal if nearly full
                if capacity - self.active[best_id]['total'] < 0.02 * capacity:
                    self.sealed[best_id] = self.active.pop(best_id)
                return best_id

            # Open new bin
            bid = self.next_id
            self.next_id += 1
            self.active[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            all_bins = {}
            all_bins.update(self.active)
            all_bins.update(self.sealed)
            return [list(info['items']) for _, info in sorted(all_bins.items())]

    return Packer()
