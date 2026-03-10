def create_packer(capacity):
    """Online almost-worst-fit: like worst-fit but skip the emptiest bin
    and pick the second-emptiest. Avoids creating new near-empty bins."""
    class Packer:
        def __init__(self):
            self.bins = {}; self.nid = 0
        def place(self, item):
            first, first_r = -1, -1
            second, second_r = -1, -1
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem + 1e-9: continue
                if rem > first_r:
                    second = first; second_r = first_r
                    first = k; first_r = rem
                elif rem > second_r:
                    second = k; second_r = rem
            chosen = second if second >= 0 else first
            if chosen >= 0:
                self.bins[chosen]['i'].append(item); self.bins[chosen]['t'] += item; return chosen
            b = self.nid; self.nid += 1; self.bins[b] = {'i': [item], 't': item}; return b
        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]
    return Packer()
