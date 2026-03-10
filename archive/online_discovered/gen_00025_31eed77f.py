def create_packer(capacity):
    """Exponential-Decay Aging Packer.

    Each bin has an "age" based on when it was last used. Selection score is:
        score(bin) = fill_fraction(bin) * decay_factor^(current_time - last_used_time[bin])

    This creates temporal locality: recently-used bins are preferred, old bins
    fade unless they're very full. Every 50 items, the oldest bin gets a
    freshness boost to prevent permanent abandonment.
    """
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.last_used = []   # global timestamp of last use per bin
            self.time = 0         # global item counter
            self.decay = 0.95     # decay factor per time step

        def place(self, item):
            self.time += 1

            # Every 50 items, revive the oldest bin (reset its last_used_time)
            if self.time % 50 == 0 and len(self.bins) > 0:
                oldest_idx = -1
                oldest_time = self.time + 1
                for i in range(len(self.bins)):
                    remaining = capacity - self.bin_sums[i]
                    # Only revive if the bin can still accept something
                    if remaining > 1e-9 and self.last_used[i] < oldest_time:
                        oldest_time = self.last_used[i]
                        oldest_idx = i
                if oldest_idx >= 0:
                    self.last_used[oldest_idx] = self.time

            best_idx = -1
            best_score = -1.0

            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item > remaining + 1e-9:
                    continue

                fill_frac = self.bin_sums[i] / capacity if capacity > 0 else 0.0
                age = self.time - self.last_used[i]
                decay_weight = self.decay ** age
                score = fill_frac * decay_weight

                if score > best_score:
                    best_score = score
                    best_idx = i

            if best_idx >= 0:
                self.bins[best_idx].append(item)
                self.bin_sums[best_idx] += item
                self.last_used[best_idx] = self.time
                return best_idx

            # No existing bin fits — open a new one
            self.bins.append([item])
            self.bin_sums.append(item)
            self.last_used.append(self.time)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
