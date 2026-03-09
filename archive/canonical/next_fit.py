def pack(items, capacity):
    """Next Fit: keep one open bin, start a new one when item doesn't fit."""
    if not items:
        return []
    bins = [[]]
    for item in items:
        if bins[-1] and sum(bins[-1]) + item > capacity:
            bins.append([])
        bins[-1].append(item)
    return bins
