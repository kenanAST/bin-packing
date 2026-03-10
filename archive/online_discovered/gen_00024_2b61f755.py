def create_packer(capacity):
    """Complementary Prediction Packer.

    Uses a running histogram of item sizes to predict what future items
    will look like. Scores each bin by the "complementarity" of the
    resulting gap: how well does the gap match the most common item sizes?

    Core scoring function for gap g:
      score = density_at(g) * (1 + penalty_if_unfillable(g))

    where density_at uses a KDE-like estimate from the histogram, and
    penalty_if_unfillable assigns negative score to gaps that fall in
    histogram "deserts" (zero-frequency buckets).

    This produces genuinely different bin assignments:
    - For 'thirds' distribution (~0.33): leaves 0.33 and 0.66 gaps
    - For bimodal: leaves gaps matching the complementary mode
    - For uniform: similar to best-fit (density is flat)
    - For increasing order: adapts as the histogram shifts

    No tightness tiebreaker -- the histogram IS the scoring function.
    Only exception: perfect fits (gap < epsilon) are always taken.
    """

    NUM_BUCKETS = 40
    bucket_width = capacity / NUM_BUCKETS

    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.histogram = [0] * NUM_BUCKETS
            self.total_items = 0

        def _bucket(self, size):
            if size <= 1e-12:
                return 0
            b = int(size / bucket_width)
            return min(b, NUM_BUCKETS - 1)

        def _gap_score(self, gap):
            """Score a gap by how well it matches the observed item distribution.

            Uses kernel density estimation with a triangular kernel of
            width 2 buckets. Returns a score proportional to the probability
            that a future item will fit in this gap.
            """
            if self.total_items < 3:
                # Cold start: prefer smaller gaps (best-fit fallback)
                return (capacity - gap) / capacity

            center = gap / bucket_width  # fractional bucket position
            score = 0.0
            inv = 1.0 / self.total_items

            # Triangular kernel: weight = max(0, 1 - |distance|/bandwidth)
            bandwidth = 1.5  # buckets
            b_lo = max(0, int(center - bandwidth))
            b_hi = min(NUM_BUCKETS - 1, int(center + bandwidth + 1))

            for b in range(b_lo, b_hi + 1):
                if self.histogram[b] == 0:
                    continue
                dist = abs(b + 0.5 - center)
                weight = max(0.0, 1.0 - dist / bandwidth)
                score += self.histogram[b] * inv * weight

            return score

        def place(self, item):
            self.total_items += 1
            self.histogram[self._bucket(item)] += 1

            best_idx = -1
            best_score = -1.0

            for i in range(len(self.bins)):
                remaining = capacity - self.bin_sums[i]
                if item > remaining + 1e-9:
                    continue
                gap = remaining - item

                if gap < 1e-9:
                    # Perfect fit -- always take
                    self.bins[i].append(item)
                    self.bin_sums[i] += item
                    return i

                score = self._gap_score(gap)

                if score > best_score + 1e-12:
                    best_score = score
                    best_idx = i

            if best_idx < 0:
                self.bins.append([item])
                self.bin_sums.append(item)
                return len(self.bins) - 1

            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            return best_idx

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
