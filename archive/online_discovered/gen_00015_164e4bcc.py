def create_packer(capacity):
    """Size-proportional-split: keep N bin slots where N = ceil(1/item_avg).
    Small avg items -> many slots. Large avg items -> few slots.
    Best-fit within available slots, cycling when full."""

    import math

    class Packer:
        def __init__(self):
            self.slots = [{'i': [], 't': 0.0}]
            self.archived = []
            self.n = 0
            self.total = 0.0

        def place(self, item):
            self.n += 1; self.total += item
            avg = self.total / self.n
            target_slots = max(2, min(10, math.ceil(capacity / avg)))

            while len(self.slots) < target_slots:
                self.slots.append({'i': [], 't': 0.0})

            best_idx, best_r = -1, capacity + 1
            for idx, b in enumerate(self.slots):
                rem = capacity - b['t']
                if item <= rem + 1e-9 and rem < best_r:
                    best_r = rem; best_idx = idx
            if best_idx >= 0:
                self.slots[best_idx]['i'].append(item)
                self.slots[best_idx]['t'] += item
                if capacity - self.slots[best_idx]['t'] < 0.03 * capacity:
                    self.archived.append(self.slots[best_idx])
                    self.slots[best_idx] = {'i': [], 't': 0.0}
                return len(self.archived) + best_idx

            # No slot fits — archive fullest, replace
            fullest = max(range(len(self.slots)), key=lambda i: self.slots[i]['t'])
            if self.slots[fullest]['i']:
                self.archived.append(self.slots[fullest])
            self.slots[fullest] = {'i': [item], 't': item}
            return len(self.archived) + fullest

        def get_bins(self):
            r = [list(b['i']) for b in self.archived]
            for b in self.slots:
                if b['i']: r.append(list(b['i']))
            return r

    return Packer()
