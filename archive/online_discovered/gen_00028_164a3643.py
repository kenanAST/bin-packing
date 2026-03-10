def create_packer(capacity):
    """Gap Demand Marketplace: scores bins by gap fillability using
    a running item-size histogram. Near-full capped at 1.0 so
    high-demand gaps override tightness."""
    NB, BW = 25, capacity / 25

    class Packer:
        def __init__(self):
            self.bins, self.nid, self.n = {}, 0, 0
            self.h = [0]*NB
            self.gc = [0]*NB
            self.top, self.dm = 0, 1.8

        def _b(self, v):
            return max(0, min(NB-1, int(v/BW)))

        def _gap_score(self, g):
            gb = self._b(g)
            f = self.h[gb] / self.n
            if gb > 0: f += 0.12 * self.h[gb-1] / self.n
            if gb < NB-1: f += 0.12 * self.h[gb+1] / self.n
            r = g - (self.top + 0.5) * BW
            if g > 0.12*capacity and 0.005*capacity < r < capacity:
                f += (self.h[self.top]/self.n)*(self.h[self._b(r)]/self.n)*2
            s = self.dm * f
            dt = abs(g - (self.top + 0.5) * BW)
            if dt < 0.08*capacity: s += 0.8*(1.0 - dt/(0.08*capacity))
            if self.gc[gb] > 3: s -= 0.25*(self.gc[gb]-3)/max(len(self.bins),1)
            if f < 0.015: s -= 0.7
            return s

        def place(self, item):
            self.n += 1; self.h[self._b(item)] += 1
            if self.n % 10 == 0:
                self.top = max(range(NB), key=lambda i: self.h[i])
                r2 = sorted(range(NB), key=lambda i: -self.h[i])
                self.dm = 2.5 if self.n>15 and self.h[r2[0]]+self.h[r2[1]]>0.6*self.n else 1.8

            bi, bs = -1, -1e18
            for k, v in self.bins.items():
                rem = capacity - v['t']
                if item > rem+1e-9: continue
                g = rem - item
                s = 1.0 if g < 0.005*capacity else (
                    self._gap_score(g) + 0.04*v['t']/capacity if self.n >= 5
                    else 1.0 - g/capacity)
                if s > bs: bs = s; bi = k

            if bi >= 0:
                v = self.bins[bi]; r0 = capacity-v['t']
                v['i'].append(item); v['t'] += item; r1 = capacity-v['t']
                if r0 > 0.005*capacity: self.gc[self._b(r0)] -= 1
                if r1 > 0.005*capacity: self.gc[self._b(r1)] += 1
                return bi
            bid = self.nid; self.nid += 1
            self.bins[bid] = {'i':[item],'t':item}
            r = capacity-item
            if r > 0.005*capacity: self.gc[self._b(r)] += 1
            return bid

        def get_bins(self):
            return [list(v['i']) for v in self.bins.values()]

    return Packer()
