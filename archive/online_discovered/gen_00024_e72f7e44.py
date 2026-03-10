def create_packer(capacity):
    """Regret-Adaptive Packer with Gap-Targeted Bin Channels.

    Bins are assigned to one of two channels based on what gap size
    they should maintain. Channel targets come from the two most
    common item size buckets. Items placed in a channel's bin aim
    to leave a gap matching that channel's target.

    When bins nearly fill, they're "sealed" and waste is tracked.
    High average waste triggers worst-fit for small items.
    """
    class Packer:
        def __init__(self):
            self.bins = []
            self.sums = []
            self.chan = []  # 0 or 1
            self.n = 0
            self.hist = [0] * 8
            self.bw = capacity / 8.0
            self.targets = [capacity * 0.3, capacity * 0.6]
            self.waste_sum = 0.0
            self.waste_n = 0
            self.sealed = set()

        def _update_targets(self):
            best = [(-1, 0), (-1, 0)]
            for i in range(8):
                c = self.hist[i]
                if c > best[0][1]:
                    best[1] = best[0]
                    best[0] = (i, c)
                elif c > best[1][1]:
                    best[1] = (i, c)
            t0 = (best[0][0] + 0.5) * self.bw if best[0][0] >= 0 else capacity * 0.3
            t1 = (best[1][0] + 0.5) * self.bw if best[1][0] >= 0 else capacity * 0.6
            if abs(t0 - t1) < self.bw:
                t1 = max(0.05 * capacity, capacity - t0)
            self.targets = [t0, t1]

        def place(self, item):
            self.n += 1
            self.hist[min(7, max(0, int(item / self.bw)))] += 1
            if self.n <= 12 or self.n % 6 == 0:
                self._update_targets()

            high_waste = (self.waste_sum / self.waste_n > 0.12 * capacity) if self.waste_n else False
            small = item < 0.35 * capacity

            best_i, best_s = -1, 1e18
            for i in range(len(self.bins)):
                rem = capacity - self.sums[i]
                if item > rem + 1e-9:
                    continue
                gap = rem - item
                if gap < 0.025 * capacity:
                    s = -1000.0 + gap
                elif high_waste and small:
                    s = -gap
                else:
                    t = self.targets[self.chan[i]]
                    s = abs(gap - t)
                if s < best_s:
                    best_s = s
                    best_i = i

            if best_i < 0:
                best_i = len(self.bins)
                gap = capacity - item
                c = 0 if abs(gap - self.targets[0]) <= abs(gap - self.targets[1]) else 1
                self.bins.append([])
                self.sums.append(0.0)
                self.chan.append(c)

            self.bins[best_i].append(item)
            self.sums[best_i] += item
            if capacity - self.sums[best_i] < 0.03 * capacity and best_i not in self.sealed:
                self.sealed.add(best_i)
                self.waste_sum += capacity - self.sums[best_i]
                self.waste_n += 1
            return best_i

        def get_bins(self):
            return [list(b) for b in self.bins]

    return Packer()
