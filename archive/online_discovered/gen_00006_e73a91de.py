def create_packer(capacity):
    """Hash-Based Packing: Items are assigned to bins based on a hash of their
    quantized size. This creates deterministic size-class affinity without
    explicit classification. Like a hash table where the 'key' is item size
    and 'value' is a bin.

    Completely different control flow from any greedy approach."""

    class Packer:
        def __init__(self):
            self.slots = {}  # hash_key -> list of (bid, bin_info)
            self.all_bins = {}
            self.next_id = 0
            self.num_slots = 7  # prime number of hash slots

        def _hash_key(self, item):
            # Quantize to num_slots levels
            return int(item / capacity * self.num_slots) % self.num_slots

        def place(self, item):
            key = self._hash_key(item)

            # Also compute complement key
            complement = capacity - item
            comp_key = self._hash_key(complement) if complement > 0.05 * capacity else key

            # Search order: complement slot first (for pairing), then own slot
            for search_key in [comp_key, key]:
                if search_key not in self.slots:
                    continue
                best_bid = -1
                best_rem = capacity + 1
                for bid in self.slots[search_key]:
                    info = self.all_bins[bid]
                    rem = capacity - info['total']
                    if item <= rem + 1e-9 and rem < best_rem:
                        best_rem = rem
                        best_bid = bid

                if best_bid >= 0:
                    self.all_bins[best_bid]['items'].append(item)
                    self.all_bins[best_bid]['total'] += item
                    return best_bid

            # Fallback: search all slots
            best_bid = -1
            best_rem = capacity + 1
            for info_bid, info in self.all_bins.items():
                rem = capacity - info['total']
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best_bid = info_bid

            if best_bid >= 0:
                self.all_bins[best_bid]['items'].append(item)
                self.all_bins[best_bid]['total'] += item
                return best_bid

            # New bin in own slot
            bid = self.next_id
            self.next_id += 1
            self.all_bins[bid] = {'items': [item], 'total': item}
            if key not in self.slots:
                self.slots[key] = []
            self.slots[key].append(bid)
            return bid

        def get_bins(self):
            return [list(self.all_bins[bid]['items']) for bid in sorted(self.all_bins)]

    return Packer()
