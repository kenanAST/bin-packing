def create_packer(capacity):
    """Active-Bin-Limited Packer.

    Limits the number of "active" bins at any time. Bins that haven't received
    an item for K placements become "inactive" and can only receive items that
    would fill them above 85% capacity. This forces the packer to fill a small
    number of bins well before opening new ones, creating a conveyor-belt effect.
    """
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.last_used = []  # placement number when bin last received an item
            self.placement_count = 0

        def _max_idle(self):
            n_bins = len(self.bins)
            return max(5, n_bins // 3)

        def place(self, item):
            self.placement_count += 1
            max_idle = self._max_idle()
            threshold = self.placement_count - max_idle

            # Phase 1: Best-fit among ACTIVE bins
            best_active_idx = -1
            best_active_remaining = capacity + 1

            # Phase 2 candidate: best inactive bin that would fill to > 85%
            best_inactive_idx = -1
            best_inactive_remaining = capacity + 1
            close_out_threshold = capacity * 0.85

            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item > remaining + 1e-9:
                    continue  # item doesn't fit

                is_active = self.last_used[i] >= threshold

                if is_active:
                    if remaining < best_active_remaining:
                        best_active_remaining = remaining
                        best_active_idx = i
                else:
                    # Inactive bin: only consider if adding item fills to > 85%
                    new_sum = self.bin_sums[i] + item
                    if new_sum >= close_out_threshold and remaining < best_inactive_remaining:
                        best_inactive_remaining = remaining
                        best_inactive_idx = i

            # Decision: prefer active bin, then inactive close-out, then new bin
            if best_active_idx >= 0:
                chosen = best_active_idx
            elif best_inactive_idx >= 0:
                chosen = best_inactive_idx
            else:
                # Open a new bin
                self.bins.append([])
                self.bin_sums.append(0.0)
                self.last_used.append(0)
                chosen = len(self.bins) - 1

            self.bins[chosen].append(item)
            self.bin_sums[chosen] += item
            self.last_used[chosen] = self.placement_count
            return chosen

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
