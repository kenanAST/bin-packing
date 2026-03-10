def create_packer(capacity):
    """Batch 100 with bin-centric FFD: for each batch, try to fill existing
    bins first (sorted by most remaining), then open new ones."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0; self.batch = []
        def _pack(self, items):
            items_sorted = sorted(items, reverse=True)
            remaining_items = list(items_sorted)
            # Fill existing bins first, greediest remaining
            bin_order = sorted(self.bins.keys(), key=lambda k: capacity - self.bins[k]['t'], reverse=True)
            for bid in bin_order:
                v = self.bins[bid]
                rem = capacity - v['t']
                still = []
                for it in remaining_items:
                    if it <= rem + 1e-9:
                        v['i'].append(it); v['t'] += it; rem -= it
                    else: still.append(it)
                remaining_items = still
            # Open new bins for remainder
            for it in remaining_items:
                best, best_r = -1, capacity + 1
                for k, v in self.bins.items():
                    rem = capacity - v['t']
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = k
                if best >= 0: self.bins[best]['i'].append(it); self.bins[best]['t'] += it
                else: b = self.nid; self.nid += 1; self.bins[b] = {'i': [it], 't': it}
        def place(self, item):
            self.batch.append(item)
            if len(self.batch) >= 100: self._pack(self.batch); self.batch = []
            return max(self.bins.keys()) if self.bins else 0
        def get_bins(self):
            if self.batch: self._pack(self.batch); self.batch = []
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
