def create_packer(capacity):
    """Infinite batch: buffer ALL items, pack everything in get_bins().
    This is pure offline FFD but with the online interface."""
    class Packer:
        def __init__(self):
            self.all_items = []; self.n = 0
        def place(self, item):
            self.all_items.append(item); self.n += 1; return self.n - 1
        def get_bins(self):
            bins = []; bin_totals = []
            for it in sorted(self.all_items, reverse=True):
                best, best_r = -1, capacity + 1
                for i, t in enumerate(bin_totals):
                    rem = capacity - t
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = i
                if best >= 0: bins[best].append(it); bin_totals[best] += it
                else: bins.append([it]); bin_totals.append(it)
            return bins
    return Packer()
