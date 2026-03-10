def create_packer(capacity):
    """Role-Based Bin Packing: bins have roles (nursery, growth, finishing).
    Small items go to nursery bins first (kept partially empty for later large items).
    Large items go to growth bins. Nearly-full bins become finishing bins.
    Uses dict-of-sets data structure, not parallel lists."""

    class Packer:
        def __init__(self):
            self.bins = {}  # bin_id -> list of items
            self.bin_totals = {}  # bin_id -> total
            self.roles = {}  # bin_id -> 'nursery'|'growth'|'finishing'
            self.role_members = {'nursery': set(), 'growth': set(), 'finishing': set()}
            self.next_id = 0
            self.items_seen = 0
            self.running_mean = 0.0

        def _update_role(self, bid):
            """Promote bins based on fill level."""
            fill = self.bin_totals[bid] / capacity
            old_role = self.roles[bid]

            if fill > 0.85:
                new_role = 'finishing'
            elif fill > 0.5:
                new_role = 'growth'
            else:
                new_role = 'nursery'

            if new_role != old_role:
                self.role_members[old_role].discard(bid)
                self.roles[bid] = new_role
                self.role_members[new_role].add(bid)

        def _best_fit_in(self, item, role):
            """Best-fit within a specific role's bins."""
            best_id = -1
            best_rem = capacity + 1
            for bid in self.role_members[role]:
                rem = capacity - self.bin_totals[bid]
                if item <= rem + 1e-9 and rem < best_rem:
                    best_rem = rem
                    best_id = bid
            return best_id

        def place(self, item):
            self.items_seen += 1
            self.running_mean += (item - self.running_mean) / self.items_seen

            ratio = item / capacity

            if ratio > 0.5:
                # Large items: try finishing bins first (tight pack), then nursery
                # (pair with small items), then growth
                search = ['finishing', 'nursery', 'growth']
            elif ratio > 0.25:
                # Medium items: try growth bins, then finishing, then nursery
                search = ['growth', 'finishing', 'nursery']
            else:
                # Small items: try finishing bins (fill gaps), then growth
                # Avoid nursery (don't stack small with small)
                search = ['finishing', 'growth', 'nursery']

            for role in search:
                bid = self._best_fit_in(item, role)
                if bid >= 0:
                    self.bins[bid].append(item)
                    self.bin_totals[bid] += item
                    self._update_role(bid)
                    return bid

            # Open new bin
            bid = self.next_id
            self.next_id += 1
            self.bins[bid] = [item]
            self.bin_totals[bid] = item

            if ratio > 0.5:
                role = 'growth'
            elif ratio > 0.25:
                role = 'growth'
            else:
                role = 'nursery'

            self.roles[bid] = role
            self.role_members[role].add(bid)
            return bid

        def get_bins(self):
            return [list(items) for items in self.bins.values()]

    return Packer()
