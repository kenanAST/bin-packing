def pack(items, capacity):
    """Best Fit Decreasing: sort items large-to-small, then apply Best Fit."""
    sorted_items = sorted(items, reverse=True)
    bins = []
    bin_sums = []
    for item in sorted_items:
        best_idx = -1
        best_remaining = capacity + 1
        for i in range(len(bins)):
            remaining = capacity - bin_sums[i]
            if item <= remaining and remaining < best_remaining:
                best_remaining = remaining
                best_idx = i
        if best_idx >= 0:
            bins[best_idx].append(item)
            bin_sums[best_idx] += item
        else:
            bins.append([item])
            bin_sums.append(item)
    return bins
