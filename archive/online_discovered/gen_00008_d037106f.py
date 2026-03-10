def create_packer(capacity):
    """Layered Packing: Organize bins into 'layers' by their creation epoch.
    Each layer holds bins created during a phase of N items.
    New items first try to complete bins in older layers (best fit),
    then try current layer (worst fit to spread evenly).

    This naturally handles increasing order: early small-item bins sit in
    old layers, and later large items complete them via cross-layer best fit."""

    class Packer:
        def __init__(self):
            self.layers = [[]]  # list of layers, each layer = list of bin dicts
            self.layer_size = 0
            self.items_per_layer = 25
            self.n = 0
            self.all_bins = {}  # flat lookup bid -> info
            self.next_id = 0

        def place(self, item):
            self.n += 1
            self.layer_size += 1

            # Start new layer periodically
            if self.layer_size > self.items_per_layer and len(self.layers[-1]) > 0:
                self.layers.append([])
                self.layer_size = 0

            # Phase 1: Try to COMPLETE bins in older layers (best fit)
            best_bid = -1
            best_rem = capacity + 1
            for layer in self.layers[:-1]:
                for bid in layer:
                    info = self.all_bins[bid]
                    rem = capacity - info['total']
                    if item <= rem + 1e-9 and rem < best_rem:
                        best_rem = rem
                        best_bid = bid

            if best_bid >= 0 and best_rem < 0.4 * capacity:
                # Good fit in older layer
                self.all_bins[best_bid]['items'].append(item)
                self.all_bins[best_bid]['total'] += item
                return best_bid

            # Phase 2: Try current layer (worst fit to spread)
            current = self.layers[-1]
            worst_bid = -1
            worst_rem = -1
            for bid in current:
                info = self.all_bins[bid]
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem > worst_rem:
                    worst_rem = rem
                    worst_bid = bid

            if worst_bid >= 0:
                self.all_bins[worst_bid]['items'].append(item)
                self.all_bins[worst_bid]['total'] += item
                return worst_bid

            # Phase 3: If old layers had a fit (even loose), use it
            if best_bid >= 0:
                self.all_bins[best_bid]['items'].append(item)
                self.all_bins[best_bid]['total'] += item
                return best_bid

            # New bin in current layer
            bid = self.next_id
            self.next_id += 1
            self.all_bins[bid] = {'items': [item], 'total': item}
            self.layers[-1].append(bid)
            return bid

        def get_bins(self):
            return [list(self.all_bins[bid]['items']) for bid in sorted(self.all_bins)]

    return Packer()
