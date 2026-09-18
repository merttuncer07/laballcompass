"""Q195 UnionAlpha recovery replay (Step 19).

Runs, in order: convention self-check; smallest case; P-mislabel
regression; formal transversality; exact sweep; non-vacuousness;
enlarged-code negative control; helical labels; closed walk; unsigned and
signed histograms; c_delta regroup equivalence.

Exact arithmetic only. Exits nonzero on any failure.
"""

import os
import sys

import numpy as np

import q195_collision_recovered as Q

# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
# poly_shift_mul mirrors filed q195_suffix_lift.poly_shift_mul
# (a * x^k in Z[x]/(x^r+1), anti-periodic).
def poly_shift_mul(a, k, r):
    out = np.zeros(r, dtype=object)
    for i, c in enumerate(a):
        if c == 0:
            continue
        q_, rem = divmod(i + k, r)
        out[rem] += (-1) ** (q_ % 2) * c
    return out


from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

CHAT_T = {3: [3, 5, 6, 8], 5: [5, 7, 9, 10, 11, 12, 14]}
CHAT_BINS = {3: (17, 5), 5: (29, 8), 7: (41, 10)}
CHAT_NEG = {3: 6, 5: 30, 7: 72, 9: 132}
CHAT_LABELS = [(1, 0)] * 4 + [(0, 1), (0, 1), (-1, 1), (0, 1), (-1, 1),
               (0, 2), (-1, 1), (0, 2), (-1, 1), (0, 2), (0, 2)]
CHAT_WALK = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1), (4, 2),
             (3, 0), (3, 1), (2, 2), (2, 1), (1, 2), (1, 1), (0, 2),
             (0, 1), (0, 0)]
CHAT_UNSIGNED = [7, 8, 9, 10, 11, 7, 8, 9, 10, 6, 7, 8, 9, 10, 1]
CHAT_SIGNED = [-1, -4, -3, -4, 1, 3, -2, -1, 2, 2, 3, 2, -3, -6, 1]


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}")
    if not cond:
        sys.exit(1)


def test_historical_P_mislabel_bug():
    """Step 7: old labeling reproduces chat's bad run; corrected run passes."""
    d, n0 = 3, 1
    r, n, s, R, P = Q.physical_word(d, n0, schedule_L3, poly_shift_mul)
    ts = {}
    for a in range(d):
        ts[('h', a)] = r - 2 - 2 * a
        ts[('q', a)] = r - 1 - 2 * a
    ts[('q', d - 1)] = d  # HISTORICAL MISTAKE (transcript Block 7)
    e = (d - 1) // 2
    F = [('h', a) for a in range(d)] + [('q', a) for a in range(e + 1)]
    F = [x for x in F if x != ('h', 0)]
    allS = [('q', d - 1)] + [x for x in F if x != ('q', d - 1)]
    Told = [ts[x] for x in sorted(set(allS), key=lambda x: ts[x])]
    check("buggy T reproduces chat duplicate", Told == [3, 3, 5, 6, 8])
    E = (r + 1) * r
    Gold = [Q.tildeQ(Told[i + 1], E, r) - Q.tildeQ(Told[i], E, r)
            for i in range(len(Told) - 2)]
    check("buggy first generator is the zero vector",
          all(int(x) == 0 for x in Gold[0]))
    Aold = np.hstack([
        np.array([Q.pi_vec(g, P, r) for g in Gold]).T,
        np.array([Q.pi_vec(g, P, r, rev=True) for g in Gold]).T])
    check("buggy run reproduces chat nullity 2",
          len(Q.exact_nullity(Aold)) == 2)
    Tnew, _ = Q.surface_chronology(d)
    check("corrected chronology is duplicate-free", Tnew == [3, 5, 6, 8])


def main():
    # 0. clean-dir provenance: modules must load from the run directory
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, Q):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))
    # 1. source/convention self-check
    r, n, e, U, B, F, Fs, g = schedule_L3(5, 1)
    check("schedule r=3d,n=d,e=(d-1)/2", (r, n, e) == (15, 5, 2))
    check("P time d equals h_{d-1} time r-2-2(d-1)", r - 2 - 2 * 4 == 5)
    check("q_{d-1} time is d+1", r - 1 - 2 * 4 == 6)
    check("b_in spans (d,d+1); b_out spans (r-2,r-1)",
          (r - 2 - 2 * 4, r - 1 - 2 * 4) == (5, 6)
          and (r - 2 - 2 * 0, r - 1 - 2 * 0) == (13, 14))
    rr, nn, ss, RR, PP = Q.physical_word(3, 1, schedule_L3, poly_shift_mul)
    check("R_0 = 1 initialization", int(RR[0][0]) == 1
          and all(int(x) == 0 for x in RR[0][1:]))

    # 2. smallest case
    c = Q.build_case(3, 1, schedule_L3, poly_shift_mul)
    check("d=3 word", c['s'] == [4, 4, 3, 3, 11, 12, 11, 12, 12])
    check("d=3 cumulative P",
          c['P'] == [0, 4, 8, 11, 14, 25, 37, 48, 60, 72])
    check("d=3 keys", c['keys'] == [('h', 2), ('h', 1), ('q', 1), ('q', 0)])
    check("d=3 T", c['T'] == [3, 5, 6, 8])
    check("d=3 formal edges", c['E'] == 90)
    check("d=3 code dims", len(c['C_fwd']) == 2 and len(c['C_rev']) == 2)
    Mform = np.hstack([np.array(c['C_fwd']).T, np.array(c['C_rev']).T])
    check("d=3 formal joint (90,4)", Mform.shape == (90, 4))
    check("d=3 FORMAL intersection 0", len(Q.exact_nullity(Mform)) == 0)
    check("d=3 projected fwd/rev rank 2",
          Q.exact_rank(c['A_fwd']) == 2 and Q.exact_rank(c['A_rev']) == 2)
    Mphys = np.hstack([c['A_fwd'], c['A_rev']])
    check("d=3 physical joint (9,4) rank 4 nullity 0",
          Mphys.shape == (9, 4) and Q.exact_rank(Mphys) == 4
          and len(Q.exact_nullity(Mphys)) == 0)

    # 3. regression
    test_historical_P_mislabel_bug()

    # 4+5. formal transversality + exact sweep
    rows = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            cc = Q.build_case(d, n0, schedule_L3, poly_shift_mul)
            Mf = np.hstack([np.array(cc['C_fwd']).T,
                            np.array(cc['C_rev']).T])
            fi = len(Q.exact_nullity(Mf))
            Mp = np.hstack([cc['A_fwd'], cc['A_rev']])
            rk = Q.exact_rank(Mp)
            nu = len(Q.exact_nullity(Mp))
            ok = (fi == 0 and rk == Mp.shape[1] and nu == 0)
            rows.append((d, n0, len(cc['C_fwd']), len(cc['C_rev']),
                         fi, rk, nu, ok))
            check(f"sweep d={d} n0={n0} formal0/rankfull/nullity0", ok)
    with open("Q195_RECOVERED_SWEEP.txt", "w") as f:
        f.write("# Q195 Recovered Exact Sweep (Step 8)\n")
        for (d, n0, df, dr, fi, rk, nu, ok) in rows:
            f.write(f"d={d} n0={n0} dim C_forward={df} dim C_reverse={dr} "
                    f"formal intersection={fi} physical projected rank={rk} "
                    f"collision nullity={nu} {'PASS' if ok else 'FAIL'}\n")

    # 6. non-vacuousness
    for d in (3, 5, 7):
        cc = Q.build_case(d, 1, schedule_L3, poly_shift_mul)
        E, r, P = cc['E'], cc['r'], cc['P']
        Pi = np.zeros((r, E), dtype=object)
        for ei in range(E):
            i, j = divmod(ei, r)
            if i < j:
                D = P[j] - P[i] - 1
                q_, rem = divmod(D, r)
                Pi[rem, ei] = (-1) ** (q_ % 2)
        pr = Q.exact_rank(Pi)
        nb, nd, mx = Q.edge_bin_stats(P, r)
        exp_bins, exp_max = CHAT_BINS[d]
        check(f"d={d} ker_pi nontrivial ({E-pr} dims)", E - pr > 0)
        check(f"d={d} bins/max match chat ({nd}/{mx})",
              nd == exp_bins and mx == exp_max)

    # 7. enlarged-code negative control
    for n0 in (1, 2):
        for d in (3, 5, 7, 9):
            cc = Q.build_case(d, n0, schedule_L3, poly_shift_mul)
            G = Q.negative_control_enlarged_code(cc['T'], cc['E'], cc['r'])
            Af = np.array([Q.pi_vec(x, cc['P'], cc['r']) for x in G]).T
            Ar = np.array([Q.pi_vec(x, cc['P'], cc['r'], rev=True)
                           for x in G]).T
            nu = len(Q.exact_nullity(np.hstack([Af, Ar])))
            check(f"negative control n0={n0} d={d} nullity={CHAT_NEG[d]}",
                  nu == CHAT_NEG[d])

    # 8-9. helical labels + closed walk
    coords, labels = Q.integrate_walk(5, 1, schedule_L3)
    check("d=5 labels generated, match chat", labels == CHAT_LABELS)
    check("d=5 walk closed + matches chat",
          coords == CHAT_WALK and coords[0] == coords[15] == (0, 0))

    # 10-11. histograms
    _, _, _, _, P5 = Q.physical_word(5, 1, schedule_L3, poly_shift_mul)
    H, S = Q.edge_histograms(P5, 15)
    check("unsigned histogram matches chat", H == CHAT_UNSIGNED)
    check("signed histogram matches chat", S == CHAT_SIGNED)

    # 12. c_delta regroup equivalence
    cc = Q.build_case(5, 1, schedule_L3, poly_shift_mul)
    v = cc['C_fwd'][0] + cc['C_fwd'][1]
    cdelta, proj = Q.c_delta_representation(v, coords, P5, 15, 5)
    check("c_delta shape d x 3",
          len(cdelta) == 5 and all(len(row) == 3 for row in cdelta))
    check("c_delta regroup == direct projection",
          list(proj) == list(Q.pi_vec(v, P5, 15)))

    print("Q195 UNIONALPHA RECOVERY: ALL CHECKS PASS")


if __name__ == "__main__":
    main()
