def create_packer(capacity):
    """Zigzag: alternate between targeting the fullest fitting bin and
    the emptiest fitting bin on consecutive items. Item 1 -> best fit,
    item 2 -> worst fit, item 3 -> best, etc but with a twist:
    the zigzag period adapts based on item size variance."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0
            self.n = 0
            self.sum_sq = 0.0
            self.sum_x = 0.0
            self.period = 2

        def place(self, item):
            self.n += 1
            self.sum_x += item; self.sum_sq += item * item
            if self.n > 5 and self.n % 10 == 0:
                mean = self.sum_x / self.n
                var = max(0, self.sum_sq / self.n - mean * mean)
                cv = (var ** 0.5) / mean if mean > 0.01 else 0
                self.period = max(2, min(6, int(2 + cv * 8)))

            phase = self.n % self.period
            use_worst = phase < self.period // 2

            best, best_r = -1, (-1 if use_worst else capacity + 1)
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                if use_worst and rem > best_r:
                    best_r = rem; best = k
                elif not use_worst and rem < best_r:
                    best_r = rem; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
