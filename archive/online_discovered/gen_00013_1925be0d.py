def create_packer(capacity):
    """Wrap-around Next-K: like next fit but cycles through K=6 bins
    continuously. When bin overflows, replace it with empty bin in-place."""

    class Packer:
        def __init__(self):
            self.slots = [None] * 6
            self.all_bins = []
            self.cursor = 0
            self.K = 6

        def place(self, item):
            for attempt in range(self.K):
                idx = (self.cursor + attempt) % self.K
                if self.slots[idx] is not None:
                    b = self.slots[idx]
                    if b['t'] + item <= capacity + 1e-9:
                        b['i'].append(item)
                        b['t'] += item
                        self.cursor = (idx + 1) % self.K
                        return b['id']

            # Replace slot at cursor with new bin
            old = self.slots[self.cursor]
            bid = len(self.all_bins)
            nb = {'i': [item], 't': item, 'id': bid}
            self.all_bins.append(nb)
            self.slots[self.cursor] = nb
            self.cursor = (self.cursor + 1) % self.K
            return bid

        def get_bins(self):
            return [list(b['i']) for b in self.all_bins if b['i']]

    return Packer()
