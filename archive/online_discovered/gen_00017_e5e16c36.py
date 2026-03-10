def create_packer(capacity):
    """Batch-sort-pack: collect items in groups of 8, sort them descending,
    pack each batch using first-fit-decreasing (offline-like). Between
    batches, keep bins open for cross-batch filling."""

    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0
            self.batch = []; self.batch_size = 8

        def _ffd_batch(self, items):
            items_sorted = sorted(items, reverse=True)
            for it in items_sorted:
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = k
                if best >= 0:
                    self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else:
                    b = self.nid; self.nid += 1
                    self.bins[b] = {'i': [it], 't': it}

        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= self.batch_size:
                self._ffd_batch(self.batch)
                self.batch = []
            # Return a bin index (approximate — items go where FFD puts them)
            return max(self.bins.keys()) if self.bins else 0

        def get_bins(self):
            if self.batch:
                self._ffd_batch(self.batch)
                self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
