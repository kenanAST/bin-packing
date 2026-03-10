def create_packer(capacity):
    """Distribution-Aware: Detect the item distribution on-the-fly using a
    reservoir of recent items. Switch between strategies based on detected
    coefficient of variation and skewness. High CV -> use tight-fit for large,
    spread for small. Low CV -> use size-class packing."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0
            self.reservoir = []
            self.max_reservoir = 50
            self.items_seen = 0
            self.sum_x = 0.0
            self.sum_x2 = 0.0
            self.mode = 'balanced'  # 'balanced', 'tight', 'spread'

        def _update_stats(self, item):
            self.items_seen += 1
            self.sum_x += item
            self.sum_x2 += item * item
            if len(self.reservoir) < self.max_reservoir:
                self.reservoir.append(item)
            else:
                # Replace random-ish element
                idx = self.items_seen % self.max_reservoir
                self.reservoir[idx] = item

            if self.items_seen >= 10 and self.items_seen % 10 == 0:
                mean = self.sum_x / self.items_seen
                var = max(0, self.sum_x2 / self.items_seen - mean * mean)
                cv = (var ** 0.5) / mean if mean > 0.01 else 0
                if cv > 0.6:
                    self.mode = 'spread'  # high variance, spread small items
                elif cv < 0.2:
                    self.mode = 'tight'   # low variance, tight packing
                else:
                    self.mode = 'balanced'

        def place(self, item):
            self._update_stats(item)
            ratio = item / capacity

            if self.mode == 'spread' and ratio < 0.3:
                # Spread small items: worst fit
                return self._worst_fit(item)
            elif self.mode == 'tight':
                # Tight: best fit always
                return self._best_fit(item)
            else:
                # Balanced: best fit for large, first fit for small
                if ratio > 0.4:
                    return self._best_fit(item)
                else:
                    return self._first_fit(item)

        def _best_fit(self, item):
            best_id = -1
            best_rem = capacity + 1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best_id = bid
            if best_id >= 0:
                self.bins[best_id]['items'].append(item)
                self.bins[best_id]['total'] += item
                return best_id
            return self._new_bin(item)

        def _worst_fit(self, item):
            best_id = -1
            best_rem = -1
            for bid, info in self.bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem > best_rem:
                    best_rem = rem
                    best_id = bid
            if best_id >= 0:
                self.bins[best_id]['items'].append(item)
                self.bins[best_id]['total'] += item
                return best_id
            return self._new_bin(item)

        def _first_fit(self, item):
            for bid, info in self.bins.items():
                if item <= capacity - info['total'] + 1e-9:
                    info['items'].append(item)
                    info['total'] += item
                    return bid
            return self._new_bin(item)

        def _new_bin(self, item):
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'items': [item], 'total': item}
            return bid

        def get_bins(self):
            return [list(info['items']) for info in self.bins.values()]

    return Packer()
