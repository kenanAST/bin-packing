def create_packer(capacity):
    """Almost-Best-Fit: like best fit, but skip the tightest-fitting bin
    and pick the second-tightest instead. The idea is that the tightest bin
    is about to be completed anyway by a future item — leaving it open
    creates better pairing opportunities."""

    class Packer:
        def __init__(self):
            self.bins = {}
            self.next_id = 0

        def place(self, item):
            first_best = -1
            first_rem = capacity + 1
            second_best = -1
            second_rem = capacity + 1

            for bid, info in self.bins.items():
                rem = capacity - info['t']
                if item > rem + 1e-9:
                    continue
                if rem < first_rem:
                    second_best = first_best
                    second_rem = first_rem
                    first_best = bid
                    first_rem = rem
                elif rem < second_rem:
                    second_best = bid
                    second_rem = rem

            # Use second-best if available and first isn't a near-perfect fit
            if second_best >= 0 and first_rem > 0.05 * capacity:
                self.bins[second_best]['i'].append(item)
                self.bins[second_best]['t'] += item
                return second_best

            if first_best >= 0:
                self.bins[first_best]['i'].append(item)
                self.bins[first_best]['t'] += item
                return first_best

            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = {'i': [item], 't': item}
            return bid

        def get_bins(self):
            return [list(self.bins[b]['i']) for b in sorted(self.bins)]

    return Packer()
