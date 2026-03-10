def create_packer(capacity):
    """Batch-pair-match: collect batch of 12, then greedily pair items
    that sum closest to capacity. Pairs go into bins together.
    Unpaired items use best-fit."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []

        def _pair_and_pack(self, items):
            items = sorted(items, reverse=True)
            used = [False] * len(items)
            pairs = []
            singles = []

            for i in range(len(items)):
                if used[i]: continue
                best_j, best_sum = -1, 0
                for j in range(i+1, len(items)):
                    if used[j]: continue
                    s = items[i] + items[j]
                    if s <= capacity + 1e-9 and s > best_sum:
                        best_sum = s; best_j = j
                if best_j >= 0:
                    pairs.append((items[i], items[best_j]))
                    used[i] = used[best_j] = True
                else:
                    singles.append(items[i]); used[i] = True

            # Place pairs in bins
            for a, b in pairs:
                # Try existing bin
                placed = False
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if a + b <= rem + 1e-9:
                        v['i'].extend([a, b]); v['t'] += a + b; placed = True; break
                if not placed:
                    bid = self.nid; self.nid += 1
                    self.bins[bid] = {'i': [a, b], 't': a + b}

            # Place singles with best-fit
            for it in singles:
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = k
                if best >= 0:
                    self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else:
                    bid = self.nid; self.nid += 1
                    self.bins[bid] = {'i': [it], 't': it}

        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= 12:
                self._pair_and_pack(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0

        def get_bins(self):
            if self.batch: self._pair_and_pack(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
