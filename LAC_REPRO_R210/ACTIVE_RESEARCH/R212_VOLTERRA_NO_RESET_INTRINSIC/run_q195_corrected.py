"""Corrected Q195-harness driver: B4 checks + B9 provisional diagnostic.

PROVISIONAL ONLY — plain reversal stands in for the unrecovered exact J_xi.
No result here is Q195. Exits nonzero on any mismatch. Writes
Q195_PROVISIONAL_SWEEP.txt into the run directory.
"""

import os
import sys

import numpy as np

import q195_corrected_sourcefaithful as C

# RECONSTRUCTED BY MUSE — mirrors filed q195_suffix_lift.poly_shift_mul
def poly_shift_mul(a, k, r):
    out = np.zeros(r, dtype=object)
    for i, c in enumerate(a):
        if c == 0:
            continue
        q_, rem = divmod(i + k, r)
        out[rem] += (-1) ** (q_ % 2) * c
    return out


from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

AUDIT_N01 = {3: (6, 0), 5: (12, 0), 7: (18, 0), 9: (22, 2),
             11: (30, 0), 13: (36, 0), 15: (36, 6)}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}")
    if not cond:
        sys.exit(1)


def main():
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, C):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))

    # B3/B4: counts + exact chronologies
    for d, exp_keys, exp_T in [
            (3, [('h', 2), ('q', 2), ('h', 1), ('q', 1), ('h', 0)],
             [3, 4, 5, 6, 7]),
            (5, [('h', 4), ('q', 4), ('q', 3), ('h', 2), ('q', 2),
                 ('h', 1), ('q', 1), ('h', 0)],
             [5, 6, 8, 9, 10, 11, 12, 13])]:
        T, keys, b_in, b_out = C.fstar_chronology(d)
        check(f"d={d} F* keys", keys == exp_keys)
        check(f"d={d} F* times", T == exp_T)
        check(f"d={d} |F*| = H", len(T) == (3 * d + 1) // 2)
    cc = C.build_corrected_case(3, 1, schedule_L3, poly_shift_mul)
    check("d=3 dim(C) = H-2 = 3", len(cc['C']) == 3)
    check("d=3 b_in = Gamma[T0,T1]",
          cc['keys'][0] == ('h', 2) and cc['keys'][1] == ('q', 2))
    check("d=3 objects separate",
          not np.array_equal(np.asarray(cc['b_in'], dtype=int),
                             np.asarray(cc['C'][0], dtype=int)))

    # B9: provisional diagnostic, audit checkpoints
    lines = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            c = C.build_corrected_case(d, n0, schedule_L3, poly_shift_mul)
            M = np.hstack([c['A_fwd'], c['A_rev']])
            rk = C._sp(M).rank()
            nu = len(C._sp(M).nullspace())
            lines.append(f"n0={n0} d={d}: cols={M.shape[1]} "
                         f"rank={rk} nullity={nu}")
            if n0 == 1:
                er, en = AUDIT_N01[d]
                check(f"provisional n0=1 d={d} rank={er} nullity={en}",
                      (rk, nu) == (er, en))
            else:
                check(f"provisional n0=2 d={d} full column rank",
                      nu == 0 and rk == M.shape[1])
    with open("Q195_PROVISIONAL_SWEEP.txt", "w") as f:
        f.write("# B9 provisional diagnostic (plain reversal; NOT Q195)\n")
        f.write("\n".join(lines) + "\n")
    print("Q195 CORRECTED DIAGNOSTIC: ALL CHECKPOINTS REPRODUCED "
          "(provisional reversal; NOT a Q195 result)")


if __name__ == "__main__":
    main()
