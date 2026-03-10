def create_packer(capacity):
    """Constraint-injected heuristic: bins have a 'target fill profile' and items
    are matched to whichever bin's target they best complete.

    CONSTRAINT: Each bin is assigned a target fill level when created, cycling
    through [0.95, 0.85, 0.75, 0.65]. The bin selection criterion is: pick the
    bin where adding this item brings the fill closest to (but not exceeding)
    the bin's target. This creates heterogeneous bin management -- some bins are
    meant to be packed tight, others left looser as reservoirs.

    Data structure: a ring buffer of target levels, and bins stored as dicts
    in a deque-like structure keyed by target class.
    """
    from collections import defaultdict

    TARGETS = [0.98, 0.90, 0.80, 0.70]
    target_idx = [0]  # mutable counter

    class Packer:
        def __init__(self):
            # Bins grouped by their target class
            self.target_bins = defaultdict(list)  # target_float -> [bin_dict, ...]
            self.all_bins_ordered = []
            self.items_seen = 0
            self.running_mean = 0.0

        def _new_bin(self, item):
            t = TARGETS[target_idx[0] % len(TARGETS)]
            target_idx[0] += 1
            b = {'items': [item], 'fill': item, 'target': t}
            self.target_bins[t].append(b)
            self.all_bins_ordered.append(b)
            return len(self.all_bins_ordered) - 1

        def place(self, item):
            self.items_seen += 1
            self.running_mean = self.running_mean + (item - self.running_mean) / self.items_seen

            best_score = float('inf')
            best_bin = None
            best_target_key = None
            best_bin_idx = -1

            # Score each open bin: how close does adding item bring fill to target?
            # Lower score = better match
            idx = 0
            for t, bins in self.target_bins.items():
                for b in bins:
                    remaining = capacity - b['fill']
                    if item > remaining + 1e-9:
                        idx += 1
                        continue
                    new_fill_ratio = (b['fill'] + item) / capacity
                    # Distance from target, but penalize overshooting target heavily
                    if new_fill_ratio <= b['target'] + 0.01:
                        score = abs(b['target'] - new_fill_ratio)
                    else:
                        score = 2.0 + (new_fill_ratio - b['target'])

                    if score < best_score:
                        best_score = score
                        best_bin = b
                        best_target_key = t
                    idx += 1

            if best_bin is not None:
                best_bin['items'].append(item)
                best_bin['fill'] += item
                return self.all_bins_ordered.index(best_bin)

            return self._new_bin(item)

        def get_bins(self):
            return [b['items'][:] for b in self.all_bins_ordered]

    return Packer()
