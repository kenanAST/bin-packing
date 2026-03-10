"""Generate batch of candidate heuristics with systematic variations."""
import os
import sys

TEMPLATE_LAYERED = '''def create_packer(capacity):
    """Layered fill: target={target}, step={step}, advance_pct={advance_pct}, tiebreak={tiebreak}."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.target = {target}
            self.n = 0
        def place(self, item):
            self.n += 1
            cap = capacity
            ts = self.target * cap
            if len(self.bins) > 3:
                above = 0
                for s in self.bin_sums:
                    if s >= ts - 0.04 * cap:
                        above += 1
                if above >= len(self.bins) * {advance_pct} and self.target < 0.97:
                    self.target = min(self.target + {step}, 0.99)
                    ts = self.target * cap
            best_idx = -1
            best_diff = 1e18
            best_tb = {tb_init}
            for i in range(len(self.bins)):
                rem = cap - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                fa = self.bin_sums[i] + item
                diff = abs(fa - ts)
                nr = rem - item
                if diff < best_diff - 0.02 * cap:
                    best_diff = diff
                    best_idx = i
                    best_tb = nr
                elif abs(diff - best_diff) <= 0.02 * cap and {tb_cmp}:
                    best_idx = i
                    best_tb = nr
            if best_idx < 0:
                return self._new_bin(item)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            return best_idx
        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1
        def get_bins(self):
            return [list(b) for b in self.bins]
    return Packer()
'''

TEMPLATE_ENTROPY = '''def create_packer(capacity):
    """Entropy minimizer: buckets={buckets}, close_thresh={close_thresh}."""
    from math import log
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.NB = {buckets}
            self.fill_hist = [0] * self.NB
        def _bucket(self, ff):
            return max(0, min(int(ff * self.NB), self.NB - 1))
        def _entropy(self):
            total = sum(self.fill_hist)
            if total <= 1:
                return 0.0
            e = 0.0
            for c in self.fill_hist:
                if c > 0:
                    p = c / total
                    e -= p * log(p + 1e-15)
            return e
        def place(self, item):
            ct = {close_thresh} * capacity
            best_idx = -1
            best_e = 1e18
            best_rem = capacity + 1
            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9:
                    continue
                nf = (self.bin_sums[i] + item) / capacity
                of = self.bin_sums[i] / capacity
                ob = self._bucket(of)
                nb = self._bucket(nf)
                if ob != nb:
                    self.fill_hist[ob] -= 1
                    self.fill_hist[nb] += 1
                    e = self._entropy()
                    self.fill_hist[ob] += 1
                    self.fill_hist[nb] -= 1
                else:
                    e = self._entropy()
                nr = rem - item
                if e < best_e - 1e-9 or (abs(e - best_e) < 1e-9 and nr < best_rem):
                    best_e = e
                    best_idx = i
                    best_rem = nr
            nf2 = item / capacity
            nb2 = self._bucket(nf2)
            self.fill_hist[nb2] += 1
            ne = self._entropy()
            self.fill_hist[nb2] -= 1
            if best_idx < 0 or ne < best_e - 1e-9:
                return self._new_bin(item)
            ob = self._bucket(self.bin_sums[best_idx] / capacity)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            nb = self._bucket(self.bin_sums[best_idx] / capacity)
            if ob != nb:
                self.fill_hist[ob] -= 1
                self.fill_hist[nb] += 1
            return best_idx
        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            b = self._bucket(item / capacity)
            self.fill_hist[b] += 1
            return len(self.bins) - 1
        def get_bins(self):
            return [list(b) for b in self.bins]
    return Packer()
'''

TEMPLATE_FILLABILITY = '''def create_packer(capacity):
    """Fillability packer: buckets={buckets}, tol_mult={tol_mult}, weights=({w1},{w2},{w3})."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.NB = {buckets}
            self.hist = [0] * self.NB
            self.min_seen = capacity
        def _b(self, v):
            return max(0, min(int(v * self.NB / capacity), self.NB - 1))
        def _rp(self, lo, hi):
            if lo > hi or self.n < 1: return 0.0
            c = 0
            for i in range(max(0,self._b(lo)), min(self.NB-1,self._b(hi))+1):
                c += self.hist[i]
            return c / self.n
        def _score(self, gap):
            if gap < 1e-9: return 50.0
            if self.n >= 5 and gap < self.min_seen * 0.85: return 30.0
            bw = capacity / self.NB
            t = bw * {tol_mult}
            p1 = self._rp(gap-t, gap+t)
            p2 = self._rp(gap/2-t, gap/2+t)**2
            p3 = self._rp(gap/3-t, gap/3+t)**3
            return p1*{w1} + p2*{w2} + p3*{w3}
        def place(self, item):
            self.n += 1
            self.hist[self._b(item)] += 1
            if item < self.min_seen: self.min_seen = item
            best_idx = -1
            best_s = -1.0
            best_r = capacity + 1
            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9: continue
                g = rem - item
                s = self._score(g)
                if s > best_s + 0.01 or (abs(s-best_s)<=0.01 and g < best_r):
                    best_s = s; best_idx = i; best_r = g
            ng = capacity - item
            ns = self._score(ng)
            if best_idx < 0 or ns > best_s + 0.01:
                return self._new_bin(item)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            return best_idx
        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1
        def get_bins(self):
            return [list(b) for b in self.bins]
    return Packer()
'''

TEMPLATE_DEADZONE = '''def create_packer(capacity):
    """Dead-zone: close={close_t}, open={open_t}, trend_thresh={trend_t}."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.window = []
        def _trend(self):
            w = self.window
            n = len(w)
            if n < 10: return 0.0
            mv = sum(w) / n
            mi = (n-1)/2.0
            num = den_v = den_i = 0.0
            for j in range(n):
                di = j - mi
                dv = w[j] - mv
                num += di*dv; den_v += dv*dv; den_i += di*di
            if den_v < 1e-12 or den_i < 1e-12: return 0.0
            return num / (den_v*den_i)**0.5
        def place(self, item):
            self.n += 1
            self.window.append(item)
            if len(self.window) > 25: self.window.pop(0)
            t = self._trend()
            if t > {trend_t}:
                ct = {close_t} * capacity
                ot = {open_t} * capacity
            else:
                ct = 0.03 * capacity
                ot = 0.95 * capacity
            bc = bo = bd = -1
            bcr = bor = bdr = capacity + 1
            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9: continue
                nr = rem - item
                if nr < ct:
                    if nr < bcr: bcr = nr; bc = i
                elif nr >= ot:
                    if nr < bor: bor = nr; bo = i
                else:
                    if nr < bdr: bdr = nr; bd = i
            nnr = capacity - item
            if bc >= 0: idx = bc
            elif bo >= 0: idx = bo
            elif nnr >= ot:
                return self._new_bin(item)
            elif bd >= 0: idx = bd
            else: return self._new_bin(item)
            self.bins[idx].append(item)
            self.bin_sums[idx] += item
            return idx
        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1
        def get_bins(self):
            return [list(b) for b in self.bins]
    return Packer()
'''

TEMPLATE_HYBRID_LAYER_FILL = '''def create_packer(capacity):
    """Hybrid layered+fillability: target={target}, step={step}, nbuckets={nbuckets}."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.target = {target}
            self.n = 0
            self.NB = {nbuckets}
            self.hist = [0] * self.NB
            self.min_seen = capacity
        def _b(self, v):
            return max(0, min(int(v*self.NB/capacity), self.NB-1))
        def _rp(self, lo, hi):
            if lo > hi or self.n < 1: return 0.0
            c = 0
            for i in range(max(0,self._b(lo)), min(self.NB-1,self._b(hi))+1):
                c += self.hist[i]
            return c / self.n
        def _fill_score(self, gap):
            if gap < 1e-9: return 50.0
            if self.n >= 5 and gap < self.min_seen * 0.85: return 30.0
            bw = capacity / self.NB
            t = bw * 0.8
            return self._rp(gap-t,gap+t)*5 + self._rp(gap/2-t,gap/2+t)**2*2
        def place(self, item):
            self.n += 1
            self.hist[self._b(item)] += 1
            if item < self.min_seen: self.min_seen = item
            cap = capacity
            ts = self.target * cap
            if len(self.bins) > 3:
                above = sum(1 for s in self.bin_sums if s >= ts - 0.04*cap)
                if above >= len(self.bins) * 0.7 and self.target < 0.97:
                    self.target = min(self.target + {step}, 0.99)
                    ts = self.target * cap
            best_idx = -1
            best_score = -1e18
            for i in range(len(self.bins)):
                rem = cap - self.bin_sums[i]
                if item > rem + 1e-9: continue
                fa = self.bin_sums[i] + item
                layer_dist = -abs(fa - ts) / cap
                gap = rem - item
                fs = self._fill_score(gap)
                score = layer_dist * 3.0 + fs * 0.5
                if score > best_score:
                    best_score = score; best_idx = i
            ng = capacity - item
            ns = -abs(item - ts)/cap * 3.0 + self._fill_score(ng) * 0.5
            if best_idx < 0 or ns > best_score:
                return self._new_bin(item)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            return best_idx
        def _new_bin(self, item):
            self.bins.append([item])
            self.bin_sums.append(item)
            return len(self.bins) - 1
        def get_bins(self):
            return [list(b) for b in self.bins]
    return Packer()
'''

TEMPLATE_VARIANCE_PLUS = '''def create_packer(capacity):
    """Variance-min + fillability hybrid: var_weight={vw}, fill_weight={fw}, nbuckets={nb}."""
    class Packer:
        def __init__(self):
            self.bins = []
            self.bin_sums = []
            self.n = 0
            self.nc = 0; self.mean = 0.0; self.m2 = 0.0
            self.active = []
            self.NB = {nb}
            self.hist = [0] * self.NB
        def _b(self, v):
            return max(0, min(int(v*self.NB/capacity), self.NB-1))
        def _fs(self, gap):
            if gap < 1e-9: return 5.0
            if self.n < 3: return 0.0
            bw = capacity / self.NB; t = bw
            lo = max(0, self._b(gap-t)); hi = min(self.NB-1, self._b(gap+t))
            c = sum(self.hist[lo:hi+1])
            return c / self.n * 3.0
        def _add(self, v):
            self.nc += 1; d = v-self.mean; self.mean += d/self.nc; self.m2 += d*(v-self.mean)
        def _rem(self, v):
            if self.nc <= 1: self.nc=0; self.mean=0; self.m2=0; return
            om = self.mean; self.nc -= 1; self.mean = (om*(self.nc+1)-v)/self.nc
            self.m2 -= (v-om)*(v-self.mean)
            if self.m2 < 0: self.m2 = 0
        def _var(self):
            return self.m2/self.nc if self.nc >= 2 else 0.0
        def place(self, item):
            self.n += 1
            self.hist[self._b(item)] += 1
            th = 0.04 * capacity
            best_idx = -1; best_score = -1e18
            for i in range(len(self.bins)):
                rem = capacity - self.bin_sums[i]
                if item > rem + 1e-9: continue
                nr = rem - item; wa = self.active[i]; na = nr >= th
                if wa: self._rem(rem)
                if na: self._add(nr)
                v = self._var()
                if na: self._rem(nr)
                if wa: self._add(rem)
                fs = self._fs(nr)
                score = -v * {vw} + fs * {fw}
                if score > best_score:
                    best_score = score; best_idx = i
            nr2 = capacity - item; na2 = nr2 >= th
            if na2: self._add(nr2)
            v2 = self._var()
            if na2: self._rem(nr2)
            ns = -v2 * {vw} + self._fs(nr2) * {fw}
            if best_idx < 0 or ns > best_score:
                return self._new_bin(item)
            orem = capacity - self.bin_sums[best_idx]
            if self.active[best_idx]: self._rem(orem)
            self.bins[best_idx].append(item)
            self.bin_sums[best_idx] += item
            nrem = capacity - self.bin_sums[best_idx]
            na = nrem >= th; self.active[best_idx] = na
            if na: self._add(nrem)
            return best_idx
        def _new_bin(self, item):
            self.bins.append([item]); self.bin_sums.append(item)
            r = capacity-item; a = r >= 0.04*capacity; self.active.append(a)
            if a: self._add(r)
            return len(self.bins) - 1
        def get_bins(self):
            return [list(b) for b in self.bins]
    return Packer()
'''

# Parameter grid
configs = []
cid = int(sys.argv[1]) if len(sys.argv) > 1 else 130

# Layered fill variations
for target in [0.20, 0.25, 0.35, 0.40]:
    for step in [0.08, 0.12, 0.18]:
        for adv in [0.6, 0.75, 0.85]:
            for tb in ['best', 'worst']:
                tb_init = "capacity + 1" if tb == 'best' else "-1"
                tb_cmp = "nr < best_tb" if tb == 'best' else "nr > best_tb"
                code = TEMPLATE_LAYERED.format(
                    target=target, step=step, advance_pct=adv,
                    tiebreak=tb, tb_init=tb_init, tb_cmp=tb_cmp)
                configs.append(('layered_fill', code, f'target={target}_step={step}_adv={adv}_tb={tb}'))

# Entropy variations
for buckets in [8, 12, 15, 20]:
    for ct in [0.0, 0.05, 0.10]:
        code = TEMPLATE_ENTROPY.format(buckets=buckets, close_thresh=ct)
        configs.append(('entropy_min', code, f'buckets={buckets}_ct={ct}'))

# Fillability variations
for buckets in [20, 25, 35]:
    for tol in [0.6, 0.9, 1.2]:
        for w1, w2, w3 in [(5,2,0.5), (8,1,0), (3,3,1)]:
            code = TEMPLATE_FILLABILITY.format(buckets=buckets, tol_mult=tol, w1=w1, w2=w2, w3=w3)
            configs.append(('fillability', code, f'b={buckets}_t={tol}_w={w1}_{w2}_{w3}'))

# Dead-zone variations
for ct in [0.08, 0.12, 0.18]:
    for ot in [0.45, 0.55, 0.65]:
        for tt in [0.15, 0.25, 0.4]:
            code = TEMPLATE_DEADZONE.format(close_t=ct, open_t=ot, trend_t=tt)
            configs.append(('dead_zone', code, f'ct={ct}_ot={ot}_tt={tt}'))

# Hybrid layered+fillability
for target in [0.25, 0.30, 0.40]:
    for step in [0.10, 0.15]:
        for nb in [20, 30]:
            code = TEMPLATE_HYBRID_LAYER_FILL.format(target=target, step=step, nbuckets=nb)
            configs.append(('hybrid_layer_fill', code, f't={target}_s={step}_nb={nb}'))

# Variance + fillability
for vw in [1.0, 2.0, 5.0]:
    for fw in [0.5, 1.0, 2.0]:
        for nb in [15, 25]:
            code = TEMPLATE_VARIANCE_PLUS.format(vw=vw, fw=fw, nb=nb)
            configs.append(('variance_fill', code, f'vw={vw}_fw={fw}_nb={nb}'))

print(f"Total configs: {len(configs)}")
print(f"Starting at candidate {cid}")

# Write candidates
for i, (strategy, code, desc) in enumerate(configs):
    fname = f"candidates/candidate_{cid + i:03d}.py"
    with open(fname, 'w') as f:
        f.write(code)

print(f"Wrote candidates {cid} to {cid + len(configs) - 1}")
print(f"Config file: gen_batch_configs.json")

import json
with open('gen_batch_configs.json', 'w') as f:
    json.dump([{'id': cid + i, 'strategy': s, 'desc': d} for i, (s, _, d) in enumerate(configs)], f)
