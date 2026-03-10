def create_packer(capacity):
    """Offline: collect all, sort desc, pack with best-fit but give a bonus
    to bins that already have items from a different size class. Encourages
    cross-class mixing for better fill."""
    class Packer:
        def __init__(self):
            self.all_items = []; self.n = 0
        def place(self, item):
            self.all_items.append(item); self.n += 1; return self.n - 1
        def get_bins(self):
            bins = []; totals = []; classes = []
            for it in sorted(self.all_items, reverse=True):
                cl = 0 if it > capacity * 0.5 else (1 if it > capacity * 0.25 else 2)
                best, best_s = -1, float('inf')
                for i, t in enumerate(totals):
                    rem = capacity - t
                    if it > rem + 1e-9: continue
                    waste = rem - it
                    bonus = -0.1 * capacity if cl not in classes[i] else 0
                    s = waste + bonus
                    if s < best_s: best_s = s; best = i
                if best >= 0:
                    bins[best].append(it); totals[best] += it; classes[best].add(cl)
                else:
                    bins.append([it]); totals.append(it); classes.append({cl})
            return bins
    return Packer()
