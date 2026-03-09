def pack(items, capacity):
    """First Fit Decreasing: sort items large-to-small, then apply First Fit."""
    sorted_items = sorted(items, reverse=True)
    bins = []
    bin_sums = []
    for item in sorted_items:
        placed = False
        for i in range(len(bins)):
            if bin_sums[i] + item <= capacity:
                bins[i].append(item)
                bin_sums[i] += item
                placed = True
                break
        if not placed:
            bins.append([item])
            bin_sums.append(item)
    return bins
