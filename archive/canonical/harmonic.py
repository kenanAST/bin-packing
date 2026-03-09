def pack(items, capacity):
    """Harmonic: classify items by size into classes (1/2, 1/3, 1/4, ...),
    pack each class separately. Items > 1/2 get their own bin."""
    # Define harmonic classes: (1/(k+1), 1/k] for k = 1, 2, ..., K
    K = 10  # number of classes
    class_bins = {k: [] for k in range(1, K + 1)}  # bins per class
    class_bin_sums = {k: [] for k in range(1, K + 1)}
    overflow_bins = []
    overflow_sums = []

    for item in items:
        # Determine class
        if item > capacity / 2:
            # Class 1: items in (1/2, 1] — one per bin
            overflow_bins.append([item])
            overflow_sums.append(item)
            continue

        assigned_class = K  # default to smallest class
        for k in range(2, K + 1):
            if item > capacity / (k + 1):
                assigned_class = k
                break

        # Try to fit in an existing bin for this class
        # Each class-k bin can hold k items
        placed = False
        for i in range(len(class_bins[assigned_class])):
            if (class_bin_sums[assigned_class][i] + item <= capacity and
                    len(class_bins[assigned_class][i]) < assigned_class):
                class_bins[assigned_class][i].append(item)
                class_bin_sums[assigned_class][i] += item
                placed = True
                break

        if not placed:
            class_bins[assigned_class].append([item])
            class_bin_sums[assigned_class].append(item)

    # Collect all bins
    all_bins = overflow_bins
    for k in range(1, K + 1):
        all_bins.extend(class_bins[k])

    return all_bins if all_bins else []
