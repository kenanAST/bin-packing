def pack(items, capacity):
    """Best Fit: place each item in the bin with the least remaining space that still fits."""
    bins = []
    bin_sums = []
    for item in items:
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
