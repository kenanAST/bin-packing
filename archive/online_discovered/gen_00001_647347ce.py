def create_packer(capacity):
    """Constraint: harmonic class routing with graduated seal thresholds.

    Items classified into 3 harmonic size classes. Each class has its own
    bin pool stored as a dict keyed by bin id. Bins seal at class-specific
    thresholds: large-item bins seal at 85%, medium at 92%, small at 96%.
    This creates different fill distributions per class.

    Small items use worst-fit (spreading), others use best-fit.
    Cross-class placement only when same-class can't fit.
    """
    HALF = capacity * 0.5
    THIRD = capacity / 3.0
    SEAL = {0: capacity * 0.85, 1: capacity * 0.92, 2: capacity * 0.96}

    class Packer:
        def __init__(self):
            self.all_bins = []
            self.pools = {0: {}, 1: {}, 2: {}}  # cls -> {bin_id: bin_dict}

        def _mk(self, item, cls):
            bid = len(self.all_bins)
            b = {'i': [item], 'f': item}
            self.all_bins.append(b)
            if b['f'] < SEAL[cls]:
                self.pools[cls][bid] = b
            return bid

        def _fit(self, item, pool, cls, worst):
            best_k = -1
            best_v = -1 if worst else capacity + 1
            for k, b in pool.items():
                rem = capacity - b['f']
                if item > rem + 1e-9:
                    continue
                if worst and rem > best_v:
                    best_v = rem
                    best_k = k
                elif not worst and rem < best_v:
                    best_v = rem
                    best_k = k
            if best_k >= 0:
                b = pool[best_k]
                b['i'].append(item)
                b['f'] += item
                if b['f'] >= SEAL[cls]:
                    del pool[best_k]
                return best_k
            return -1

        def place(self, item):
            cls = 0 if item > HALF else (1 if item > THIRD else 2)
            worst = (cls == 2)

            r = self._fit(item, self.pools[cls], cls, worst)
            if r >= 0:
                return r

            # Cross-class: try others with best-fit, using their seal threshold
            for c in (1, 0, 2) if cls != 1 else (0, 2):
                if c == cls:
                    continue
                r = self._fit(item, self.pools[c], c, False)
                if r >= 0:
                    return r

            return self._mk(item, cls)

        def get_bins(self):
            return [b['i'][:] for b in self.all_bins]

    return Packer()
