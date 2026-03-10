def create_packer(capacity):
    """Dual-Queue Packer: Maintain two queues of open bins:
    - 'hungry' bins: less than 50% full, want large items
    - 'finishing' bins: more than 50% full, want small items
    Large items go to hungry bins (worst fit among hungry).
    Small items go to finishing bins (best fit among finishing).
    Bins move between queues as they fill."""

    class Packer:
        def __init__(self):
            self.hungry = {}   # bid -> {'items', 'total'}
            self.finishing = {} # bid -> {'items', 'total'}
            self.done = {}     # bid -> {'items', 'total'}
            self.next_id = 0

        def place(self, item):
            ratio = item / capacity

            if ratio > 0.5:
                # Large item: worst fit in hungry (maximize remaining for future)
                bid = self._worst_in(item, self.hungry)
                if bid is None:
                    bid = self._best_in(item, self.finishing)
                if bid is None:
                    return self._new_bin(item)
                self._add_to(bid, item)
                return bid

            elif ratio > 0.25:
                # Medium: best fit in finishing, then hungry
                bid = self._best_in(item, self.finishing)
                if bid is None:
                    bid = self._best_in(item, self.hungry)
                if bid is None:
                    return self._new_bin(item)
                self._add_to(bid, item)
                return bid
            else:
                # Small: best fit in finishing (fill gaps), then hungry
                bid = self._best_in(item, self.finishing)
                if bid is None:
                    bid = self._worst_in(item, self.hungry)
                if bid is None:
                    return self._new_bin(item)
                self._add_to(bid, item)
                return bid

        def _best_in(self, item, pool):
            best = None
            best_rem = capacity + 1
            for bid, info in pool.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best = bid
            return best

        def _worst_in(self, item, pool):
            best = None
            best_rem = -1
            for bid, info in pool.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem > best_rem:
                    best_rem = rem
                    best = bid
            return best

        def _add_to(self, bid, item):
            # Find which pool it's in
            if bid in self.hungry:
                pool = self.hungry
            else:
                pool = self.finishing

            pool[bid]['items'].append(item)
            pool[bid]['total'] += item

            fill = pool[bid]['total'] / capacity

            # Promote/seal
            if fill > 0.95:
                self.done[bid] = pool.pop(bid)
            elif fill > 0.5 and bid in self.hungry:
                self.finishing[bid] = self.hungry.pop(bid)

        def _new_bin(self, item):
            bid = self.next_id
            self.next_id += 1
            info = {'items': [item], 'total': item}
            if item / capacity > 0.5:
                self.finishing[bid] = info
            else:
                self.hungry[bid] = info
            return bid

        def get_bins(self):
            all_b = {}
            all_b.update(self.hungry)
            all_b.update(self.finishing)
            all_b.update(self.done)
            return [list(all_b[bid]['items']) for bid in sorted(all_b)]

    return Packer()
