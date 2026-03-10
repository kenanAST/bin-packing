def create_packer(capacity):
    """Increasing-Order Specialist: Quota-Limited Capped Spread.

    Phase-based strategy switching for monotonically increasing streams:

    Phase SPREAD (first 200 items when increasing and items < 0.35*cap):
    Fill cap = 0.35*cap per bin. Small items accumulate to ~0.35,
    creating prepared bins with 0.65 room for future large items.

    Phase PACK (after 200 spread items OR items >= 0.35*cap):
    Best-fit across all bins. Large items pair with prepared bins.

    The 200-item quota bounds spreading damage on narrow-range
    distributions while allowing significant spreading on wide-range ones.

    Models future gap fillability: bins capped at 0.35 are designed to
    accept one large item (0.60-0.90) plus possibly one more small item,
    reaching 0.95+ fill. This is optimal for bimodal distributions.

    For non-increasing streams: standard best-fit.
    """

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.prev_item = None
            self.inc_run = 0
            self.dec_count = 0
            self.is_increasing = False
            self.phase_pack = False
            self.spread_items = 0

        def _update(self, item):
            self.n += 1
            if self.prev_item is not None:
                if item >= self.prev_item - 1e-9:
                    self.inc_run += 1
                else:
                    self.inc_run = 0
                    self.dec_count += 1
            self.prev_item = item

            if self.n >= 5 and self.dec_count == 0 and self.inc_run >= 4:
                self.is_increasing = True
            elif self.dec_count > 1:
                self.is_increasing = False

            if item >= 0.35 * capacity:
                self.phase_pack = True

            # Quota: only spread first 200 items
            if self.spread_items >= 200:
                self.phase_pack = True

        def place(self, item):
            self._update(item)

            if self.is_increasing and not self.phase_pack:
                return self._capped_spread(item)
            else:
                return self._best_fit(item)

        def _capped_spread(self, item):
            self.spread_items += 1
            fill_cap = 0.35 * capacity

            # Best-fit within cap
            best_idx = -1
            best_fill = -1
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item > remaining + 1e-9:
                    continue
                fill_after = self.bin_sums[i] + item
                if fill_after <= fill_cap + 1e-9:
                    if fill_after > best_fill:
                        best_fill = fill_after
                        best_idx = i

            if best_idx >= 0:
                self.bins[best_idx].append(item)
                self.bin_sums[best_idx] += item
                return best_idx

            # Near-close
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item > remaining + 1e-9:
                    continue
                if remaining - item < 0.03 * capacity:
                    self.bins[i].append(item)
                    self.bin_sums[i] += item
                    return i

            return self._new_bin(item)

        def _best_fit(self, item):
            best_idx = -1
            best_remaining = capacity + 1
            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item <= remaining + 1e-9 and remaining < best_remaining:
                    best_remaining = remaining
                    best_idx = i
            if best_idx >= 0:
                self.bins[best_idx].append(item)
                self.bin_sums[best_idx] += item
                return best_idx
            return self._new_bin(item)

        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
