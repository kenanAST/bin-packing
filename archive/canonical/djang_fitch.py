def pack(items, capacity):
    """Djang-Fitch: First Fit Decreasing with a tighter pairing heuristic.
    After sorting, try to pair the largest unplaced item with the largest
    item that fits alongside it."""
    sorted_items = sorted(items, reverse=True)
    bins = []
    used = [False] * len(sorted_items)

    for i in range(len(sorted_items)):
        if used[i]:
            continue
        used[i] = True
        current_bin = [sorted_items[i]]
        remaining = capacity - sorted_items[i]

        # Greedily fill the rest of this bin with the largest fitting items
        for j in range(i + 1, len(sorted_items)):
            if used[j]:
                continue
            if sorted_items[j] <= remaining:
                current_bin.append(sorted_items[j])
                remaining -= sorted_items[j]
                used[j] = True
                if remaining < 0.01:
                    break

        bins.append(current_bin)

    return bins
