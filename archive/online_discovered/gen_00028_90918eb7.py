def create_packer(capacity):
    """Hash-complement probe packer. Dict maps quantized remaining capacity
    to bin sets. Probes capacity levels in priority order: near-exact fill,
    complement multiples (gap=k*item for k=1..4), and three strategic
    fractions. No full scan — opens new bin on probe miss. Creates fills
    shaped by item-size multiples with distinct co-location patterns."""

    BW = 0.05

    class Packer:
        def __init__(self):
            self.bins, self.sums = [], []
            self.cmap = {}

        def _q(self, v):
            return max(0, int(v / BW))

        def _put(self, i, rem):
            self.cmap.setdefault(self._q(rem), set()).add(i)

        def _pop(self, i, rem):
            b = self._q(rem)
            if b in self.cmap:
                self.cmap[b].discard(i)
                if not self.cmap[b]:
                    del self.cmap[b]

        def _do_place(self, idx, item):
            self._pop(idx, capacity - self.sums[idx])
            self.bins[idx].append(item)
            self.sums[idx] += item
            nr = capacity - self.sums[idx]
            if nr > 1e-9:
                self._put(idx, nr)
            return idx

        def _scan(self, item, tb):
            for b in (tb, tb + 1, tb - 1):
                if b >= 0 and b in self.cmap:
                    for i in self.cmap[b]:
                        if item <= capacity - self.sums[i] + 1e-9:
                            return i
            return -1

        def place(self, item):
            iq = self._q(item)
            maxb = self._q(capacity)

            # Near-exact fill (gap < BW)
            idx = self._scan(item, iq)
            if idx >= 0 and capacity - self.sums[idx] - item < BW:
                return self._do_place(idx, item)

            # Complement multiples: remaining = k*item
            for k in range(2, 6):
                tb = iq * k
                if tb > maxb:
                    break
                idx = self._scan(item, tb)
                if idx >= 0:
                    return self._do_place(idx, item)

            # Strategic fractions
            for frac in (0.50, 0.70, 0.85):
                tb = self._q(frac * capacity)
                if tb >= iq:
                    idx = self._scan(item, tb)
                    if idx >= 0:
                        return self._do_place(idx, item)

            # Retry near-exact
            idx = self._scan(item, iq)
            if idx >= 0:
                return self._do_place(idx, item)

            nid = len(self.bins)
            self.bins.append([item])
            self.sums.append(item)
            nr = capacity - item
            if nr > 1e-9:
                self._put(nid, nr)
            return nid

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
