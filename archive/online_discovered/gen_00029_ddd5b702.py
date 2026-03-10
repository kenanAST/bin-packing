def create_packer(capacity):
    """Layered Fill with Count-Penalized Spreading.
    Bins split into filling (< 90% full) and completing (>= 90%).
    Completing: best-fit. Filling: worst-fit penalized by item count.
    Tracks per-bin count; bins at k-1 items promoted to completing.
    Items discretized to 0.01 for threshold computation."""

    class Packer:
        def __init__(self):
            self.bins = []
            self.sums = []
            self.counts = []
            self.filling = set()
            self.completing = set()
            self.n = 0
            self.sx = 0.0
            self.k = 0

        def _est_k(self):
            m = self.sx / self.n
            if m > 0.01:
                self.k = max(2, round(capacity / m))

        def _is_completing(self, i):
            if self.sums[i] > 0.90 * capacity:
                return True
            if self.k >= 2 and self.counts[i] >= self.k - 1:
                return True
            return False

        def place(self, item):
            self.n += 1
            self.sx += item
            if self.n == 15:
                self._est_k()

            # Step 1: best-fit among completing bins
            bi, br = -1, capacity + 1.0
            for i in list(self.completing):
                r = capacity - self.sums[i]
                if item <= r + 1e-9 and r < br:
                    br = r
                    bi = i
            if bi >= 0:
                return self._put(bi, item)

            # Step 2: count-penalized worst-fit among filling bins
            bi, bs = -1, -1e9
            mean = self.sx / self.n if self.n else 0.5
            pen = mean * 0.3
            for i in list(self.filling):
                r = capacity - self.sums[i]
                if item <= r + 1e-9:
                    s = r - pen * self.counts[i]
                    if s > bs:
                        bs = s
                        bi = i
            if bi >= 0:
                return self._put(bi, item)

            return self._new(item)

        def _put(self, i, item):
            self.filling.discard(i)
            self.completing.discard(i)
            self.bins[i].append(item)
            self.sums[i] += item
            self.counts[i] += 1
            if capacity - self.sums[i] >= 0.005:
                if self._is_completing(i):
                    self.completing.add(i)
                else:
                    self.filling.add(i)
            return i

        def _new(self, item):
            i = len(self.bins)
            self.bins.append([item])
            self.sums.append(item)
            self.counts.append(1)
            if capacity - item >= 0.005:
                if self._is_completing(i):
                    self.completing.add(i)
                else:
                    self.filling.add(i)
            return i

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
