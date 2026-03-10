def create_packer(capacity):
    """Stack-Based Packing: Items go onto a stack. When the stack has enough
    items to fill a bin (sum >= capacity threshold), pop items from the stack
    greedily to fill a bin. Otherwise keep stacking.

    This defers decisions until enough information is available, creating
    fundamentally different packing patterns from greedy approaches.
    Uses a bounded stack to avoid memory issues."""

    class Packer:
        def __init__(self):
            self.result_bins = []
            self.stack = []  # (item_size,) tuples, most recent on top
            self.stack_total = 0.0
            self.max_stack = 30

        def _flush_bin(self):
            """Greedily fill a bin from the stack, taking largest items first."""
            # Sort stack descending
            self.stack.sort(reverse=True)
            bin_items = []
            bin_total = 0.0
            remaining = []

            for item in self.stack:
                if bin_total + item <= capacity + 1e-9:
                    bin_items.append(item)
                    bin_total += item
                else:
                    remaining.append(item)

            if bin_items:
                self.result_bins.append(bin_items)
            self.stack = remaining
            self.stack_total = sum(remaining)

        def place(self, item):
            self.stack.append(item)
            self.stack_total += item

            # Flush when stack can fill a bin well (>85% capacity)
            # or when stack is getting too big
            if self.stack_total >= 0.85 * capacity or len(self.stack) >= self.max_stack:
                self._flush_bin()
                return len(self.result_bins) - 1

            # Return a placeholder - item is in the stack
            return len(self.result_bins) + len(self.stack) - 1

        def get_bins(self):
            # Flush remaining stack items
            while self.stack:
                old_len = len(self.stack)
                self._flush_bin()
                if len(self.stack) == old_len:
                    # Can't flush any more - remaining items each get own bin
                    for item in self.stack:
                        self.result_bins.append([item])
                    self.stack = []
                    break
            return [list(b) for b in self.result_bins]

    return Packer()
