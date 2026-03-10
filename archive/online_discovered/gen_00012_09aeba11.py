def create_packer(capacity):
    """Item-count-fit: prefer bins with fewer items. Among bins that fit,
    pick the one with the fewest items (ties broken by tightest fit).
    Forces items to spread across bins more evenly by count."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.nid = 0

        def place(self, item):
            best, best_cnt, best_rem = -1, 999999, capacity + 1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                cnt = len(v['i'])
                if cnt < best_cnt or (cnt == best_cnt and rem < best_rem):
                    best_cnt = cnt; best_rem = rem; best = k
            if best >= 0:
                self.bins[best]['i'].append(item); self.bins[best]['t'] += item
                return best
            b = self.nid; self.nid += 1
            self.bins[b] = {'i': [item], 't': item}; return b

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
