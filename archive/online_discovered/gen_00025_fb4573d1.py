def create_packer(capacity):
    """Multi-Queue Stream Packer: maintains K parallel bin queues, each
    targeting a different fill level. Items are routed to the queue
    whose target best matches the resulting fill.

    Queue targets: 0.33, 0.55, 0.75, 0.90, 0.99
    Each queue has one "active" bin. When an item is routed to a queue:
    - If the active bin can hold the item: place it
    - If not: seal the active bin, open a new one, place item

    When routing, compute which queue's target is closest to the fill
    level AFTER placing the item. This means:
    - Small items in empty bins → queue 0.33 (low fill, waiting for more)
    - Items that would bring a bin to 0.90 → queue 0.90 (nearly done)
    - Items that perfectly fill → queue 0.99

    This creates a pipeline effect: bins progress through queues as
    they fill up, with items routed to maintain target fill levels.

    CROSS-QUEUE SEARCH: before opening a new bin in any queue, search
    ALL queues' active bins for the one where placement is closest to
    that bin's queue target.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.targets = [0.33, 0.55, 0.75, 0.90, 0.99]
            self.K = len(self.targets)
            # Each queue holds the index of its active bin (-1 = none)
            self.queues = [-1] * self.K

        def place(self, item):
            best_idx = -1
            best_score = 1e18  # lower = better (distance to target)

            # Search all active bins across all queues
            for q in range(self.K):
                bi = self.queues[q]
                if bi < 0:
                    continue
                rem = capacity - self.bin_sums[bi]
                if item > rem + 1e-9:
                    continue
                new_fill = (self.bin_sums[bi] + item) / capacity
                # How close is new_fill to THIS queue's target?
                dist = abs(new_fill - self.targets[q])
                if dist < best_score:
                    best_score = dist
                    best_idx = bi

            # Also consider opening a new bin in the best-matching queue
            new_fill = item / capacity
            best_new_q = -1
            best_new_dist = 1e18
            for q in range(self.K):
                dist = abs(new_fill - self.targets[q])
                if dist < best_new_dist:
                    best_new_dist = dist
                    best_new_q = q

            # If new bin matches target better than any existing bin
            if best_idx < 0 or best_new_dist < best_score * 0.5:
                # Open new bin in the best-matching queue
                idx = len(self.bins)
                self.bins.append([item])
                self.bin_sums.append(item)
                # If queue already has an active bin, it's now sealed
                self.queues[best_new_q] = idx
                return idx

            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item

            # If this bin is now very full, seal it (remove from queue)
            if capacity - self.bin_sums[best_idx] < 0.02 * capacity:
                for q in range(self.K):
                    if self.queues[q] == best_idx:
                        self.queues[q] = -1
                        break

            return best_idx

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
