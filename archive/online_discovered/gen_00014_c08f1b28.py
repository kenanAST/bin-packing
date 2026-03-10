def create_packer(capacity):
    """Three-bin juggle: keep exactly 3 active bins at different target fills
    (low ~0.3, mid ~0.6, high ~0.9). Route items to make bins approach
    their targets. When a bin hits >0.95, archive it and open new at target 0."""

    class Packer:
        def __init__(self):
            self.active = [{'i': [], 't': 0.0}, {'i': [], 't': 0.0}, {'i': [], 't': 0.0}]
            self.targets = [0.3, 0.6, 0.9]
            self.archived = []

        def place(self, item):
            best_idx, best_s = -1, float('inf')
            for idx, b in enumerate(self.active):
                rem = capacity - b['t']
                if item > rem + 1e-9: continue
                new_fill = (b['t'] + item) / capacity
                s = abs(new_fill - self.targets[idx])
                if s < best_s: best_s = s; best_idx = idx

            if best_idx < 0:
                # No active bin fits — archive lowest fill, replace
                worst = min(range(3), key=lambda i: self.active[i]['t'])
                if self.active[worst]['i']:
                    self.archived.append(self.active[worst])
                self.active[worst] = {'i': [item], 't': item}
                return len(self.archived) + worst

            self.active[best_idx]['i'].append(item)
            self.active[best_idx]['t'] += item

            if self.active[best_idx]['t'] > 0.95 * capacity:
                self.archived.append(self.active[best_idx])
                self.active[best_idx] = {'i': [], 't': 0.0}

            return len(self.archived) + best_idx - (1 if self.active[best_idx]['t'] == 0.0 else 0)

        def get_bins(self):
            r = [list(b['i']) for b in self.archived]
            for b in self.active:
                if b['i']: r.append(list(b['i']))
            return r

    return Packer()
