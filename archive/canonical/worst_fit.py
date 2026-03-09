def pack(items, capacity):
    """Worst Fit: place each item in the bin with the most remaining space."""
    bins = []
    bin_sums = []
    for item in items:
        worst_idx = -1
        worst_remaining = -1
        for i in range(len(bins)):
            remaining = capacity - bin_sums[i]
            if item <= remaining and remaining > worst_remaining:
                worst_remaining = remaining
                worst_idx = i
        if worst_idx >= 0:
            bins[worst_idx].append(item)
            bin_sums[worst_idx] += item
        else:
            bins.append([item])
            bin_sums.append(item)
    return bins
