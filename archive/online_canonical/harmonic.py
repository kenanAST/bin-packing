def create_packer(capacity):
    """Harmonic: classify items by size into classes (1/2, 1/3, ..., 1/K),
    pack each class into dedicated bins. Items > 1/2 get their own bin."""
    K = 10

    class Packer:
        def __init__(self):
            self.class_bins = {k: [] for k in range(1, K + 1)}
            self.class_bin_sums = {k: [] for k in range(1, K + 1)}
            self.overflow_bins = []
            self.overflow_sums = []
            self._all_bins = []
            self._dirty = True

        def place(self, item):
            self._dirty = True
            if item > capacity / 2:
                self.overflow_bins.append([item])
                self.overflow_sums.append(item)
                return -1  # new bin

            assigned_class = K
            for k in range(2, K + 1):
                if item > capacity / (k + 1):
                    assigned_class = k
                    break

            for i in range(len(self.class_bins[assigned_class])):
                if (self.class_bin_sums[assigned_class][i] + item <= capacity + 1e-9
                        and len(self.class_bins[assigned_class][i]) < assigned_class):
                    self.class_bins[assigned_class][i].append(item)
                    self.class_bin_sums[assigned_class][i] += item
                    return i

            self.class_bins[assigned_class].append([item])
            self.class_bin_sums[assigned_class].append(item)
            return len(self.class_bins[assigned_class]) - 1

        def get_bins(self):
            result = list(self.overflow_bins)
            for k in range(1, K + 1):
                result.extend(self.class_bins[k])
            return [list(b) for b in result if b]

    return Packer()
