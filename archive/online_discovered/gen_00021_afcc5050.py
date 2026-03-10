def create_packer(capacity):
    """Greedy-pair-match offline: collect all items, then greedily match
    largest with best-fitting complement, pack pairs + singles via FFD."""
    class Packer:
        def __init__(self):
            self.all_items = []; self.n = 0
        def place(self, item):
            self.all_items.append(item); self.n += 1; return self.n - 1
        def get_bins(self):
            items = sorted(self.all_items, reverse=True)
            used = [False] * len(items)
            bins = []; totals = []
            # Pair large items with best complement
            for i in range(len(items)):
                if used[i]: continue
                if items[i] > capacity * 0.5:
                    best_j, best_sum = -1, 0
                    for j in range(len(items)-1, i, -1):
                        if used[j]: continue
                        s = items[i] + items[j]
                        if s <= capacity + 1e-9 and s > best_sum:
                            best_sum = s; best_j = j
                    if best_j >= 0:
                        bins.append([items[i], items[best_j]])
                        totals.append(items[i] + items[best_j])
                        used[i] = used[best_j] = True
                    else:
                        bins.append([items[i]]); totals.append(items[i]); used[i] = True
            # Remaining items via FFD
            remaining = [items[i] for i in range(len(items)) if not used[i]]
            for it in remaining:
                best, best_r = -1, capacity + 1
                for idx, t in enumerate(totals):
                    rem = capacity - t
                    if it <= rem + 1e-9 and rem < best_r: best_r = rem; best = idx
                if best >= 0: bins[best].append(it); totals[best] += it
                else: bins.append([it]); totals.append(it)
            return bins
    return Packer()
