def create_packer(capacity):
    """Gradient Packer — Target-Fill with Adaptive Target.

    Core idea: maintain an adaptive target fill level per bin based on
    the running mean item size. Place items in the bin whose post-placement
    fill is closest to its per-bin target.

    The target for bin i is:
        target_i = base_target + age_drift_i
    where:
        base_target = clamp(1.0 - mean_item_size, 0.35, 0.92)
        age_drift_i = min(target reaches 0.98, 0.003 * items_since_opened)

    Fresh bins prefer moderate fill (leaving pairing room) while older bins
    drift toward completion as their target rises.

    Fallback: if no bin is within 0.20 of its target after placement,
    fall back to tightest-remaining-space (best-fit) logic. Only open a
    new bin if nothing fits at all.

    Tie-breaking within 0.015 on target distance: prefer tighter remaining.

    Large items (> 0.5 * capacity) skip target logic and use pure best-fit
    since they can never share a bin with another large item.
    """

    class Packer:
        __slots__ = ('cap', 'bins', 'bin_sums', 'bin_birth', 'n', 'item_sum')

        def __init__(self):
            self.cap = capacity
            self.bins = []
            self.bin_sums = []
            self.bin_birth = []
            self.n = 0
            self.item_sum = 0.0

        def place(self, item):
            self.n += 1
            self.item_sum += item
            cap = self.cap
            tol = 1e-9

            mean_item = self.item_sum / self.n
            base_target = 1.0 - mean_item
            if base_target < 0.35:
                base_target = 0.35
            if base_target > 0.92:
                base_target = 0.92

            is_large = item > 0.5 * cap

            best_target_idx = -1
            best_target_score = -1e18
            best_target_rem = cap + 1.0

            bestfit_idx = -1
            bestfit_rem = cap + 1.0

            for i in range(len(self.bins)):
                remaining = cap - self.bin_sums[i]
                if item > remaining + tol:
                    continue

                new_rem = remaining - item

                # Track best-fit fallback
                if new_rem < bestfit_rem:
                    bestfit_rem = new_rem
                    bestfit_idx = i

                if is_large:
                    continue

                new_fill = (self.bin_sums[i] + item) / cap

                # Per-bin target with age drift
                age = self.n - self.bin_birth[i]
                target_i = min(base_target + 0.003 * age, 0.98)
                score = -abs(new_fill - target_i)

                if score < -0.20:
                    continue

                if best_target_idx < 0:
                    best_target_idx = i
                    best_target_score = score
                    best_target_rem = new_rem
                elif score > best_target_score + 0.015:
                    best_target_idx = i
                    best_target_score = score
                    best_target_rem = new_rem
                elif score >= best_target_score - 0.015:
                    if new_rem < best_target_rem:
                        best_target_idx = i
                        best_target_score = score
                        best_target_rem = new_rem

            if is_large:
                chosen = bestfit_idx
            else:
                chosen = best_target_idx if best_target_idx >= 0 else bestfit_idx

            if chosen >= 0:
                self.bins[chosen].append(item)
                self.bin_sums[chosen] += item
                return chosen

            self.bins.append([item])
            self.bin_sums.append(item)
            self.bin_birth.append(self.n)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
