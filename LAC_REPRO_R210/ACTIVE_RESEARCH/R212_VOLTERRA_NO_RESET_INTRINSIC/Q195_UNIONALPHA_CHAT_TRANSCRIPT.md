# Q195 UnionAlpha Chat Transcript (Step 2)

Provenance record. No mathematics improved here. Code/output transcribed from
accessible UnionAlpha turns. Superseded runs are marked SUPERSEDED, not deleted.

Scope: accessible history begins at the user message "What did we do so far?".
Any earlier same-chat UnionAlpha work is outside current context and is NOT
covered by this file (see Q195_PROVENANCE.md, NOT RECOVERED).

```text
UNIONALPHA CHAT BLOCK 1

Purpose:
First probe. Grid-coordinate helpers; enumerate F* surfaces d=3,5.

Original code/output:
```

```python
import sys
sys.path.insert(0, '.')
import numpy as np
import sympy as sp
from q195_suffix_lift import physical_word, poly_shift_mul
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

print("=== Q195 CORE: two-sided collision test on TRUE interval-code spaces ===")
```

(plus defining commentary on Gamma[a,b] as suffix difference
tildeQ_b - tildeQ_a with pi(Gamma) = Q_b - Q_a; grid_coords with
iota(a,0)=a, iota(a,t) = d + (d-1-a)(L-1) + (t-1); build_Fstar with
F = {(a,2)} union {(a,1): a<=e}, F* = (F minus {(0,2p)}) union {(d-1,1)})

```text
d=3: word length 9, F* = [(0, 1), (1, 1), (1, 2), (2, 1), (2, 2)]
d=5: word length 15, F* = [(0, 1), (1, 1), (1, 2), (2, 1), (2, 2), (3, 2), (4, 1), (4, 2)]
```

```text
Immediate interpretation made in chat:
Grid-coordinate F* sets listed; chronological ordering still open.
Persisted elsewhere? NO.
```

```text
UNIONALPHA CHAT BLOCK 2

Purpose:
Locate F* prefix times via exact state matching (states_int, d=3).

Original code/output:
```

```python
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3, states_int

d = 3
states, sched = states_int(d, 1)
r = 3 * d
for k in range(0, r + 1):
    nz = [(i, c) for i, c in enumerate(states[k]) if c != 0]
    if len(nz) <= 2:
        print(f"k={k}: {nz}")
```

```text
k=0: [(0, 1)]
k=1: [(0, 1), (4, 1)]
```

```text
Immediate interpretation made in chat:
Single-monomial matching does not locate surfaces; states accumulate support.
Persisted elsewhere? NO.
```

```text
UNIONALPHA CHAT BLOCK 3

Purpose:
Survey exact state support sizes along the word (d=3).

Original code/output:
```

```python
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3, states_int

d = 3
states, sched = states_int(d, 1)
r = 3 * d
for k in range(r + 1):
    nz = [(i, c) for i, c in enumerate(states[k]) if c != 0]
    print(f"k={k}: support size {len(nz)}: {nz if len(nz) <= 4 else '...'}")
```

```text
k=0: support size 1: [(0, 1)]
k=1: support size 2: [(0, 1), (4, 1)]
k=2: support size 3: [(0, 1), (4, 1), (8, 1)]
k=3: support size 4: [(0, 1), (2, -1), (3, 1), (7, 1)]
k=4: support size 5: ...
k=5: support size 6: ...
k=6: support size 7: ...
k=7: support size 8: ...
k=8: support size 9: ...
k=9: support size 9: ...
```

```text
Immediate interpretation made in chat:
Support grows monotonically; matching-by-support abandoned.
Persisted elsewhere? NO.
```

```text
UNIONALPHA CHAT BLOCK 4

Purpose:
Pin F* prefix-time chronology from S1 12.1
(h_a = R_{r-2-2a}, q_a = R_{r-1-2a}, P = h_{d-1} = R_d).

Original code/output:
```

```python
def surface_times(d):
    r = 3 * d
    e = (d - 1) // 2
    times = {}
    for a in range(d):
        times[(a, 1)] = r - 1 - 2 * a
        times[(a, 2)] = r - 2 - 2 * a
    return times

def ordered_Fstar_times(d):
    times = surface_times(d)
    e = (d - 1) // 2
    F = [(a, 2) for a in range(d)] + [(a, 1) for a in range(e + 1)]
    F = [x for x in F if x != (0, 2)]
    all_surf = [(d - 1, 1)] + F
    ordered = sorted(all_surf := [((d-1,1), times[(d-1,1)])] +
                     [(x, times[x]) for x in F], key=lambda p: p[1])
    return ordered
```

```text
d=3: H = 5 surfaces; ordered F* times = [3, 4, 5, 6, 8]... count=5
d=5: H = 8 surfaces; ordered F* times = [5, 5, 7, 9, 10, 11]... count=8
d=7: H = 11 surfaces; ordered F* times = [7, 7, 9, 11, 13, 14]... count=11
```

```text
Immediate interpretation made in chat:
Repeated time present (seed of P-mislabel diagnosis).
Persisted elsewhere? NO (superseded).
```

```text
UNIONALPHA CHAT BLOCK 5

Purpose:
First formal edge-space joint attempt (tuple-keyed). Failed.

Original code/output:
```

```python
def edge_index(r, i, j):
    return i * r + j

def build_test(d, n0=1):
    r, n, s, R, P = physical_word(d, n0)
    H = (r + 1) // 2
    times = [(a, 2, r - 2 - 2 * a) for a in range(d)] + [(a, 1, r - 1 - 2 * a) for a in range((d - 1) // 2 + 1)]
    surf = {('h', a): r - 2 - 2 * a for a in range(d)}
    surf_q = {('q', a): r - 1 - 2 * a for a in range(d)}
    e = (d - 1) // 2
    F = [('h', a) for a in range(d)] + [('q', a) for a in range(e + 1)]
    F = [x for x in F if x != ('h', 0)]
    ordered = [('q', d - 1)] + sorted([x for x in F if x != ('q', d - 1)],
                                      key=lambda x: surf[x[0]] if x[0] == 'h' else surf_q[x[0]])
    ts = {('h', a): r - 2 - 2 * a for a in range(d)}
    ts.update({('q', a): r - 1 - 2 * a for a in range(d)})
    ts[('q', d - 1)] = d
    ordered = sorted(ordered, key=lambda x: ts[x])
    T = [ts[x] for x in ordered]
    def tildeQ(j):
        v = np.zeros((r + 1) * r, dtype=object)
        for i in range(j):
            v[edge_index(r, i, j)] += 1
        return v
    C_fwd = [tildeQ(T[i + 1]) - tildeQ(T[i]) for i in range(len(T) - 2)]
    return r, T, C_fwd, surf, surf_q
```

```text
Traceback (most recent call last):
  File "<stdin>", line 50, in <module>
  File "<stdin>", line 32, in build_test
  File "<stdin>", line 33, in <lambda>
KeyError: 'h'
```

```text
Immediate interpretation made in chat:
Sort lambda indexes surf[x[0]] inconsistently. Unified in Block 6.
Persisted elsewhere? PARTIAL (failure mode recorded here only).
```

```text
UNIONALPHA CHAT BLOCK 6

Purpose:
Fixed time map; P-override retained. First T-vectors (DUPLICATE time).

Original code/output:
```

```python
def build_test(d, n0=1):
    r, n, s, R, P = physical_word(d, n0)
    H = (r + 1) // 2
    ts = {}
    for a in range(d):
        ts[('h', a)] = r - 2 - 2 * a
        ts[('q', a)] = r - 1 - 2 * a
    ts[('q', d - 1)] = d
    e = (d - 1) // 2
    F = [('h', a) for a in range(d)] + [('q', a) for a in range(e + 1)]
    F = [x for x in F if x != ('h', 0)]
    allS = [('q', d - 1)] + [x for x in F if x != ('q', d - 1)]
    ordered = sorted(set(allS), key=lambda x: ts[x])
    T = [ts[x] for x in ordered]
    def tildeQ(j, r=r):
        v = np.zeros((r + 1) * r, dtype=object)
        for i in range(j):
            v[i * r + j] += 1
        return v
    C_fwd = [tildeQ(T[i + 1]) - tildeQ(T[i]) for i in range(len(T) - 2)]
    return r, T, C_fwd
```

```text
d=3: T = [3, 3, 5, 6, 8], interior generators = 3 (expect H-2 = 3)
d=5: T = [5, 5, 7, 9, 10, 11, 12, 14], interior generators = 6 (expect H-2 = 6)
d=7: T = [7, 7, 9, 11, 13, 14, 15, 16, 17, 18, 20], interior generators = 9 (expect H-2 = 9)
d=9: T = [9, 9, 11, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 26], interior generators = 12 (expect H-2 = 12)
```

```text
Immediate interpretation made in chat:
Counts match H-2 but every T opens with a duplicated time.
Persisted elsewhere? NO (superseded by Block 8 fix).
```

```text
UNIONALPHA CHAT BLOCK 7 — SUPERSEDED (pre-fix P labeling)

Purpose:
Two-sided collision kernel with the P-override chronology (duplicate time).

Original code/output:
```

```python
def build(d, n0=1):
    r, n, s, R, P = physical_word(d, n0)
    ts = {}
    for a in range(d):
        ts[('h', a)] = r - 2 - 2 * a
        ts[('q', a)] = r - 1 - 2 * a
    ts[('q', d - 1)] = d
    e = (d - 1) // 2
    F = [('h', a) for a in range(d)] + [('q', a) for a in range(e + 1)]
    F = [x for x in F if x != ('h', 0)]
    allS = [('q', d - 1)] + [x for x in F if x != ('q', d - 1)]
    ordered = sorted(set(allS), key=lambda x: ts[x])
    T = [ts[x] for x in ordered]
    E = (r + 1) * r
    def tildeQ(j):
        v = np.zeros(E, dtype=object)
        for i in range(j):
            v[i * r + j] += 1
        return v
    C_fwd = [tildeQ(T[i + 1]) - tildeQ(T[i]) for i in range(len(T) - 2)]
    def pi_edge(i, j):
        D = P[j] - P[i] - 1
        q_, rem = divmod(D, r)
        row = np.zeros(r, dtype=object)
        row[rem] += (-1) ** (q_ % 2)
        return row
    def pi_vec(v):
        out = np.zeros(r, dtype=object)
        for idx, c in enumerate(v):
            if c == 0:
                continue
            i, j = divmod(idx, r)
            out = out + c * pi_edge(i, j)
        return out
    A_fwd = np.array([pi_vec(g) for g in C_fwd]).T
    def pi_vec_rev(v):
        out = np.zeros(r, dtype=object)
        for idx, c in enumerate(v):
            if c == 0:
                continue
            i, j = divmod(idx, r)
            out = out + c * pi_edge(j, i)
        return out
    A_rev = np.array([pi_vec_rev(g) for g in C_fwd]).T
    return r, A_fwd, A_rev
```

```text
d=3: joint (9 x 6), rank = 4, nullity = 2
d=5: joint (15 x 12), rank = 10, nullity = 2
d=7: joint (21 x 18), rank = 16, nullity = 2
d=9: joint (27 x 24), rank = 22, nullity = 2
d=11: joint (33 x 30), rank = 28, nullity = 2
```

```text
Immediate interpretation made in chat:
Persistent nullity 2 first read as possible survivor modes, then diagnosed
as artifact in Block 8.
Persisted elsewhere? PARTIAL (bad numbers recorded here only; diagnosis YES
in R212_STATE.md).
```

```text
UNIONALPHA CHAT BLOCK 8 — THE P-MISLABEL DIAGNOSIS AND FIX

Purpose:
Diagnose the nullity-2 artifact; correct P identification.

Original chat reasoning (verbatim substance):
P = h_{d-1} = R_d at time d (S1 12.1), NOT q_{d-1}. The override
ts[('q', d-1)] = d duplicated ('h', d-1) at time d, so T opened with a
repeated time and the first generator tildeQ diff was the 0 vector, freeing
2 dimensions (u_0, v_0). Fix: use P = ('h', d-1); ('q', d-1) was never in F.

Original code/output (fixed build):
```

```python
def build(d, n0=1):
    r, n, s, R, P = physical_word(d, n0)
    ts = {}
    for a in range(d):
        ts[('h', a)] = r - 2 - 2 * a
        ts[('q', a)] = r - 1 - 2 * a
    e = (d - 1) // 2
    F = [('h', a) for a in range(d)] + [('q', a) for a in range(e + 1)]
    F = [x for x in F if x != ('h', 0)]
    allS = [('h', d - 1)] + [x for x in F if x != ('h', d - 1)]
    ordered = sorted(set(allS), key=lambda x: ts[x])
    T = [ts[x] for x in ordered]
    assert len(set(T)) == len(T), f"repeated surface time: {T}"
    E = (r + 1) * r
    def tildeQ(j):
        v = np.zeros(E, dtype=object)
        for i in range(j):
            v[i * r + j] += 1
        return v
    C = [tildeQ(T[i + 1]) - tildeQ(T[i]) for i in range(len(T) - 2)]
    def pi_row(i, j):
        D = P[j] - P[i] - 1
        q_, rem = divmod(D, r)
        row = np.zeros(r, dtype=object)
        row[rem] += (-1) ** (q_ % 2)
        return row
    def pi_vec(v, rev=False):
        out = np.zeros(r, dtype=object)
        for idx, c in enumerate(v):
            if c == 0:
                continue
            i, j = divmod(idx, r)
            a, b = (j, i) if rev else (i, j)
            out = out + c * pi_row(a, b)
        return out
    A_f = np.array([pi_vec(g) for g in C]).T
    A_r = np.array([pi_vec(g, rev=True) for g in C]).T
    return r, T, A_f, A_r
```

```text
d=3: T unique: True, joint rank 4/4, nullity 0
d=5: T unique: True, joint rank 10/10, nullity 0
d=7: T unique: True, joint rank 16/16, nullity 0
d=9: T unique: True, joint rank 22/22, nullity 0
d=11: T unique: True, joint rank 28/28, nullity 0
d=13: T unique: True, joint rank 34/34, nullity 0
d=15: T unique: True, joint rank 40/40, nullity 0
```

```text
Immediate interpretation made in chat:
No two-sided collision on the interior consecutive code.
Persisted elsewhere? PARTIAL (verdict YES in R212_STATE.md; code/outputs NO).
NOTE: corrected T-vectors themselves were never printed (only uniqueness).
```

```text
UNIONALPHA CHAT BLOCK 9

Purpose:
Repeat the collision test in both sectors n0=1 and n0=2.

Original code/output (fixed build from Block 8, both n0):
```

```text
-- n0 = 1 --
  d=3: joint (9, 4), rank 4, nullity 0
  d=5: joint (15, 10), rank 10, nullity 0
  d=7: joint (21, 16), rank 16, nullity 0
  d=9: joint (27, 22), rank 22, nullity 0
  d=11: joint (33, 28), rank 28, nullity 0
  d=13: joint (39, 34), rank 34, nullity 0
-- n0 = 2 --
  d=3: joint (9, 4), rank 4, nullity 0
  d=5: joint (15, 10), rank 10, nullity 0
  d=7: joint (21, 16), rank 16, nullity 0
  d=9: joint (27, 22), rank 22, nullity 0
  d=11: joint (33, 28), rank 28, nullity 0
  d=13: joint (39, 34), rank 34, nullity 0
```

```text
Immediate interpretation made in chat:
Nullity 0 in both sectors; caution raised whether the test could be vacuous.
Persisted elsewhere? PARTIAL (verdict YES in R212_STATE.md; table NO).
```

```text
UNIONALPHA CHAT BLOCK 10

Purpose:
Non-vacuousness: count edges vs distinct signed bins under pi.

Original code/output:
```

```python
def edge_bins(d, n0):
    r, n, s, R, P = physical_word(d, n0)
    bins = {}
    for i in range(r + 1):
        for j in range(i + 1, r + 1):
            D = P[j] - P[i] - 1
            q_, rem = divmod(D, r)
            bins[(i, j)] = (rem, (-1) ** (q_ % 2))
    from collections import Counter
    cnt = Counter((rem, sgn) for (rem, sgn) in bins.values())
    collisions = {k: v for k, v in cnt.items() if v > 1}
    return len(bins), len(cnt), collisions
```

```text
d=3: 45 edges -> 17 distinct signed bins; max edges sharing a bin: 5
d=5: 120 edges -> 29 distinct signed bins; max edges sharing a bin: 8
d=7: 231 edges -> 41 distinct signed bins; max edges sharing a bin: 10
```

```text
Immediate interpretation made in chat:
pi is far from injective globally, so nullity 0 is content, not artifact.
Persisted elsewhere? PARTIAL (d=7 numbers YES in R212_STATE.md; rest NO).
```

```text
UNIONALPHA CHAT BLOCK 11

Purpose:
Falsification attempt: enlarge packet space to ALL pairwise F* generators.

Original code/output (fixed chronology; gens = tildeQ(T[b]) - tildeQ(T[a])
for all a<b):
```

```text
n0=1 d=3: full pairwise span (9, 12), nullity 6
n0=1 d=5: full pairwise span (15, 42), nullity 30
n0=1 d=7: full pairwise span (21, 90), nullity 72
n0=1 d=9: full pairwise span (27, 156), nullity 132
n0=2 d=3: full pairwise span (9, 12), nullity 6
n0=2 d=5: full pairwise span (15, 42), nullity 30
n0=2 d=7: full pairwise span (21, 90), nullity 72
n0=2 d=9: full pairwise span (27, 156), nullity 132
```

```text
Immediate interpretation made in chat:
Nonzero nullity lives in boundary (b_in/b_out) directions excluded by the
Q193 surgery; belongs to Q196, not the bulk lemma.
Persisted elsewhere? PARTIAL (verdict YES in R212_STATE.md; table NO).
```

```text
UNIONALPHA CHAT BLOCK 12

Purpose:
Check fwd-only rank of the enlarged pairwise span (telescope structure).

Original code/output:
```

```text
d=3: H-1 = 3; rank of fwd-only physical span = 3
d=5: H-1 = 6; rank of fwd-only physical span = 6
d=7: H-1 = 9; rank of fwd-only physical span = 9
d=9: H-1 = 12; rank of fwd-only physical span = 12
```

```text
Immediate interpretation made in chat:
Simplex structure intact; no collapse.
Persisted elsewhere? PARTIAL (verdict YES in R212_STATE.md; table NO).
```

```text
UNIONALPHA CHAT BLOCK 13

Purpose:
Formal transversality in edge coordinates (no pi): joint [C | J(C)] kernel.

Original code/output:
```

```python
def J_vec(v):
    w = np.zeros(E, dtype=object)
    for idx, c in enumerate(v):
        if c == 0:
            continue
        i, j = divmod(idx, r)
        w[j * r + i] += c
    return w
```

```text
n0=1 d=3: FORMAL joint (90, 4), nullity 0
n0=1 d=5: FORMAL joint (240, 10), nullity 0
n0=1 d=7: FORMAL joint (462, 16), nullity 0
n0=1 d=9: FORMAL joint (756, 22), nullity 0
n0=1 d=11: FORMAL joint (1122, 28), nullity 0
n0=2 d=3: FORMAL joint (90, 4), nullity 0
n0=2 d=5: FORMAL joint (240, 10), nullity 0
n0=2 d=7: FORMAL joint (462, 16), nullity 0
n0=2 d=9: FORMAL joint (756, 22), nullity 0
n0=2 d=11: FORMAL joint (1122, 28), nullity 0
```

```text
Immediate interpretation made in chat:
Independently confirms the report's formal transversality claim.
Persisted elsewhere? PARTIAL (verdict YES in R212_STATE.md; shapes NO).
```

```text
UNIONALPHA CHAT BLOCK 14

Purpose:
Methodological self-check (no new mathematics).

Original output (verbatim):
"Self-check verdict: hypothesis PARTIALLY applies. What applies: I have run
several span/nullity variants and should now LOCK the construction and run ONE
decisive falsification pass instead of more variants. What does not apply:
there is no 'paper-claimed kernel dimension' to match — Q195 is OPEN in the
paper (its nullity is the unknown), so nullity 0 is my COMPUTED EVIDENCE for
the conjecture, not a mismatch with a claimed value. The genuinely untried
decisive step the paper itself prescribes (S1 section 16/23) is NOT more span
enumeration: derive the WIDTH-3 LOCAL TRANSPORT law c_{delta+1} = M_delta
c_delta from the word, and check whether nonzero 3-face modes survive both
end boundaries."

Persisted elsewhere? NO.
```

```text
UNIONALPHA CHAT BLOCK 15 — SUPERSEDED (brute-force label map)

Purpose:
First helical-label attempt (brute force mod 2*d*n0). Produced (0,0)/(4,0)
artifacts. Abandoned.

Original output:
[(1, 0), (1, 0), (1, 0), (1, 0), (0, 0), (0, 0), (4, 0), (0, 0),
 (4, 0), (0, 0), (4, 0), (0, 0), (4, 0), (0, 0), (0, 0)]

Persisted elsewhere? NO (correctly absent; superseded junk).
```

```text
UNIONALPHA CHAT BLOCK 16

Purpose:
Proper helical map: decompose s_k - n = g_k into
1 -> (1,0); 0 -> (0,1); r-1 -> (-1,1); r or 2r -> (0,2).

Original code/output (d=5, r=15, n=5):
```

```text
k=0: s=6, g=1, label=(1, 0)
k=1: s=6, g=1, label=(1, 0)
k=2: s=6, g=1, label=(1, 0)
k=3: s=6, g=1, label=(1, 0)
k=4: s=5, g=0, label=(0, 1)
k=5: s=5, g=0, label=(0, 1)
k=6: s=19, g=14, label=(-1, 1)
k=7: s=5, g=0, label=(0, 1)
k=8: s=19, g=14, label=(-1, 1)
k=9: s=20, g=15, label=(0, 2)
k=10: s=19, g=14, label=(-1, 1)
k=11: s=20, g=15, label=(0, 2)
k=12: s=19, g=14, label=(-1, 1)
k=13: s=20, g=15, label=(0, 2)
k=14: s=20, g=15, label=(0, 2)
```

```text
Immediate interpretation made in chat:
Step-label sequence for Step 13 recovery (condensed in chat as
(1,0)x4, (0,1), (0,1), (-1,1), (0,1), (-1,1), (0,2), (-1,1),
(0,2), (-1,1), (0,2), (0,2)).
Persisted elsewhere? NO.
```

```text
UNIONALPHA CHAT BLOCK 17

Purpose:
Integrate step labels from (0,0); verify cycle closure.

Original output (d=5):
  0: (0, 0)
  1: (1, 0)
  2: (2, 0)
  3: (3, 0)
  4: (4, 0)
  5: (4, 1)
  6: (4, 2)
  7: (3, 0)
  8: (3, 1)
  9: (2, 2)
  10: (2, 1)
  11: (1, 2)
  12: (1, 1)
  13: (0, 2)
  14: (0, 1)
  15: (0, 0)
cycle closure: (0, 0) (0, 0)

Persisted elsewhere? NO.
```

```text
UNIONALPHA CHAT BLOCK 18

Purpose:
Full-cycle edge histogram over r=15 bins (d=5).

Original output:
unsigned histogram: [7, 8, 9, 10, 11, 7, 8, 9, 10, 6, 7, 8, 9, 10, 1]
signed histogram:   [-1, -4, -3, -4, 1, 3, -2, -1, 2, 2, 3, 2, -3, -6, 1]

Persisted elsewhere? NO.
```

END OF RECOVERED UNIONALLPHA CHAT (accessible scope).





