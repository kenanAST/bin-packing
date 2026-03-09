def pack(items, capacity):
    """First Fit: place each item in the first bin that has room."""
    bins = []
    bin_sums = []
    for item in items:
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
