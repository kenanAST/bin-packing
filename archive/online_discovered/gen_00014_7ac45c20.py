def create_packer(capacity):
    """Skip-list-inspired: scan bins in chunks. Check every 3rd bin for fit.
    If found, refine search in that neighborhood. Approximate best-fit with
    different access patterns creating different behavioral signature."""

    class Packer:
        def __init__(self):
            self.bins = []

        def place(self, item):
            n = len(self.bins)
            if n == 0:
                self.bins.append({'i': [item], 't': item})
                return 0

            step = max(1, n // 10)
            best, best_r = -1, capacity + 1

            # Coarse scan
            candidates = []
            for idx in range(0, n, step):
                rem = capacity - self.bins[idx]['t']
                if item <= rem + 1e-9:
                    candidates.append(idx)

            # Fine scan around candidates
            for c in candidates:
                for offset in range(-step, step + 1):
                    idx = c + offset
                    if idx < 0 or idx >= n: continue
                    rem = capacity - self.bins[idx]['t']
                    if item <= rem + 1e-9 and rem < best_r:
                        best_r = rem; best = idx

            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best

            self.bins.append({'i': [item], 't': item})
            return len(self.bins) - 1

        def get_bins(self):
            return [list(b['i']) for b in self.bins]

    return Packer()
