# R212 — Volterra No-Reset Intrinsic-Count Identification (ALAN line)

Created: 2026-09-18. Parent: R211 (active-probe transfer). This round ingests the
ALAN Volterra programme (intrinsic-count no-reset identification), audits it,
repairs the certificate debt, and tracks the open frontier.

## Internal sources now in this directory
- R212_STATE.md — this file.
- phasezero_replay.py — exact phase-zero determinants + Smith forms (RUN: PASS).
- phasezero_bipartite_unimodular_standalone.py — det B_h = ±1, h=1..8; residual
  -z0 certificate (RUN: PASS).
- resonant_boundary_cubic_cert.py — F0/F1/F2 reciprocal-conjugate resultants
  Res = -780 / 23004 / -192 over Q(eta), gcds degree 0 (RUN: PASS).
- VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE.py — full K0/K1/K2 fixed-state
  reconstruction: delta bridge PASS; deg K1=12, K0=K2=13; gcd(K_i,K_i^sharp)=1;
  removable physical nodes q=eta (d=13,19) and q=1 (d=11,17) nonzero in the
  original finite physical determinant (RUN: PASS, sympy-only, no floats).
- (Original bundle: ~/Developer/VOLTERRA_REPRODUCIBILITY_REPAIR_COMPLETE_2026-09-18.zip;
  note RESONANT_FIXED_STATE_REPAIR_NOTE.md in ~/Developer.)

## REPRODUCIBILITY DEBT: CLOSED (2026-09-18)
All four previously-open artifact gaps replayed exactly in our environment:
- Phase-zero SNF(M_r^(nu)): nu even -> I; nu odd -> diag(1..1, r-2) [exact SNF
  replay r=5,7,9; dets Psi/2 match RUN_COMPLETE.txt line-for-line].
- B_h bipartite unimodularity: det = (-1)^{floor((h+1)/2)} pattern h=1..8, all
  unit-pivot reductions, final residual -z0 (both e-parities h even/odd).
- F0/F1/F2 resultants: -780, 23004, -192; gcd(K,K^sharp) degree 0 each.
- K0/K1/K2 coefficient lists recovered (emitted verbatim above); the sharp
  convention is now DEFINED in-source: K^sharp(q) = q^deg * K_bar(1/q),
  eta -> eta^2 (matches verify_05's inferred convention — inference confirmed).
Consequence: the resonant L=3, n=d theorem is now backed by a replayable
exact certificate layer; phase-zero repair is backed by general proof + replay.
The verify_05 caveat from the desktop audit is CLOSED.

## Source documents (user-supplied)
- Full research report (ALAN programme, compiled 2026-09-17): pasted in conversation.
- `~/Desktop/files/volterra_paper_draft.md` — working paper draft.
- `~/Desktop/files/VERIFICATION_REPORT.md` + `verify_01..05*.py` — independent
  certificates (5 scripts, all executed fresh by us on 2026-09-18; results match).

## Verified status (our audit, exact arithmetic/numeric)
- D_{m,r} dimension: exact. Rank-one serial theorem: full recovery from raw
  2m+1 outputs, m=4,6,9 (and via verify_01 for m=1..8, 0 real failures; the two
  m=8 misses are chart skips at |s^T Hs| ~ 1e-7/8e-7, verified deterministic).
- Theorem 2 closure H = Y(Om^T Y)^{-1} Y^T: verified on 98 valid charts (<=7.4e-15).
- T^r=-I architecture; 2r antipodal degree separation (affine vs quadratic exact).
- Unit-phase: Laurent support/diagonal claims; P_H polynomial identity
  (1+t^2)P_H = 1 - t + (-1)^{H-1} t^{2H-1}(1+t) (H=2..10); on physical t reduces
  to report's (1+sigma)+(sigma-1)t; P_H = 2/(1+t^2) or -2t/(1+t^2); never zero
  (all H 2..12, both eps branches).
- Budgets: H*r = r(r+1)/2 = dim Sym_r (unit-phase); phase-zero sum g_k = r(r+3)/2;
  curvature count r + r(r-1)/2; even-rank candidate budget = C(r+2,2) (r=2..20).
- Composite geometry: |F| = dp + (e+1) = H (10 combos); iota bijection; donor/
  recipient indices disjoint.
- P(T) orbit: P(z) != 0 on z^r = -1 for (15,6),(21,6),(27,9),(33,11),(45,18),
  (25,10),(35,10); gcd(P, x^r+1)=1 via verify_04 (90 d>=3 rows).
- Identity Q_{k+1} - xi^{s_k} Q_k = R_{k+1}(u)+R_{k+1}(v)-1: exact.
- Trig identity |C|^2-1 = 8 sin(Q/2) sin((A+Q)/2) cos(A/2): exact; zeros iff
  q=1 or aq=1 or a=-1.
- Head identities, suffix normalization (ASSUMES R_0=1 — must be stated),
  two-channel separation J-D=(eta-1)B, eta D-J=(eta-1)A, period-3 boundary: exact.
- verify_05 resultants under INFERRED F^sharp convention: |Res| = 23004, 780, 192;
  no unit-circle roots. Convention inference flagged; S2 needed to close.

## Audit findings (ours, 2026-09-18)
1. L=3,n=d resonant theorem: rank e+3 exceeds d at d=3 (deficiency -1). Theorem
   needs explicit "d >= 5"; d->7 reduction needs d>=7; base cases d=3,5 lack
   stated certificates.
2. Suffix normalization S_k = sum x^{-P_i} assumes R_0=1; state it.
3. Rank-one window walk visits negative-side staircase in DECREASING x-index;
   recovery verified correct, but the mirror/window-order convention is implicit
   — one-line clarification needed for referees.
4. verify_04/VERIFICATION_REPORT/draft all say "108 triples with d,L odd >=3";
   actual: 108 includes 18 d=1 rows; honest d>=3 count is 90. The 10 printed
   "FAILURES" are exactly out-of-domain d=1 rows (gcd = x+1 structurally, since
   P = 1+x^n has root -1 for n odd). Fix wording or gate script at d>=3.
5. Structural fact worth adding to draft: P(T) orbit is singular exactly on the
   d=1 boundary (d=1 => gcd(1+x^n, x^r+1) = x+1 nontrivially, always).
6. Reproducibility debt (report's own flags): CLOSED 2026-09-18 — see above.
   Remaining NON-artifact opens (mathematics, per DEBT_STATUS.md): Q195, Q196,
   remaining L=3 reflection sectors, L>=5, Lemma B, universal all-odd, noise
   stability, external novelty.

## Frontier after the repair (what the new pieces CHANGE)
- The desktop audit's "unverifiable" items 3–4 are now verified; the only audit
  findings still standing are the d=3 qualifier (L=3,n=d rank formula needs d>=5,
  d->7 needs d>=7, base cases d=3,5), the R_0=1 statement, the window-order
  clarification, and the 108-vs-90 wording in verify_04/draft.
- K_i degrees (12,13,13) now MATCH the handoff's claimed degrees exactly; the
  draft's numbers were right.
- The standalone cert's period-six fixed-state mechanism (geometric q^6 tail,
  fixed-degree G_i(q) per d mod 3) is the executable form of the handoff's
  period-2/period-3 lcm argument — this is new tooling for the OPEN sectors:
  the same fixed-state machinery is the natural attack route for the remaining
  reflection sectors (Q195/Q196) since it bounds boundary complexity growth.

## Open frontier (unchanged by our audit)
Q195 two-sided helical collision -> Q196 2D boundary closure -> L=3 reference
closure; Lemma B; L>=5; universal all-odd theorem. Correctly scoped in sources.

## Working rules
- User supplies missing internal pieces; we test whether the open-problem
  apparatus pertains, then consolidate THIS file as the persistent context.
- Nothing committed to git unless asked.

## R211 lineage (what laballcompass had BEFORE this ALAN ingestion)
R211 = Volterra ACTIVE-PROBE transfer (reset-and-replay machinery), completed
before R212. Key verified results there (probe_transfer.py, 17 unittests, all
passing; stress grids machine-precision clean):
- Higher-order active probing: probe_multilinear generalizes the 4-point
  bilinear polarization to order d (2^d queries per evaluation, exact).
  recover_multilinear: image phase (m*r probes) -> SVD basis -> optional r^d
  core. No dense m^d tensor ever formed; storage mr + r^d.
- CP factor extraction (extract_cp_factors): generalized eig of two random
  slices S_t = G^T D_t G; eigenvectors = columns of G^{-1} for ANY invertible
  G; eigengap retry loop for degenerate weight ratios (wall 3).
- WALL 6 BROKEN: core-free absolute weights. D[a] = T(f_a, f_a, w1),
  M[a,b] = Gram[a,b]^2 * (f_b . w1), w = M^{-1} D. Cost r extra probes;
  kernel reconstruction <= 2.6e-12 over 100 nonorthogonal cases.
- WALL 1 BROKEN (order-4+): order-d slice extraction with order-2 contractions
  (2*(r^2) probes per attempt); parity-correct weights (even-order weights keep
  signs; odd-order made positive); orders 4-6 verified, 90 core-free cases,
  worst rel. kernel error 4.6e-10. Query count n*2^d*(mr + 2r^2 + r).
- Crossover result retained: dense ridge beats active learner at m=12 equal
  budget; reversal at m=100 (5/5) consistent with O(mr) vs O(m^2) params.
- R211 open walls AFTER R212 breakthroughs: wall 2 (noisy identifiability
  theorem) remains open in BOTH lines; wall 4 (equal-amplitude budgets),
  wall 5 (sequential/agent transfer) untouched.
- Frontier scan (R209/210 era): passive tensor-network Volterra (Batselier/
  Kilic BTN-V, arXiv 2511.20457) is SOTA passive lane; active reset-and-probe
  identification (R211) and now no-reset intrinsic-count (ALAN, R212) are the
  novel lanes. R212's no-reset constraint is STRICTER than R211's reset
  access; the two lines share the H=low-rank recovery philosophy but the
  query models differ fundamentally (arbitrary z in R211 vs sliding windows
  of one scalar trajectory in R212).

## Relationship between the two lines (R211 <-> R212)
- Shared core algebra: low-rank symmetric quadratic kernel; recover small
  object (Y=H*Omega / CP factors) instead of dense H; generic chart det !=
  0; anti-periodic/signed cyclic structure appears in both (R211 order-d
  slices vs ALAN T^r=-I recurrence).
- NOT interchangeable: R211's polarization needs x+-y independent control;
  ALAN's serial constraint forbids exactly that. ALAN's intrinsic count
  D_{m,r} has no R211 analogue (R211 pays 2^d per probe, not intrinsic).
- Cross-pollination candidates: R211's noisy-order-4 whitening/JDTM step and
  robust-Kruskal perturbation theory could supply ALAN's missing noise
  stability theory (open in both). R212's fixed-state period-six collapse
  could inform R211's retry/conditioning analysis for near-degenerate slices.

## R212 executable core (added 2026-09-18)
- intrinsic_no_reset.py: sliding windows, rank-one trajectory, rank-one
  recovery (q = Hs via differences, H = qq^T/(s^T q), ell/b telescoping),
  rank-r closure, anti-periodic T, 2r antipodal separation, D_{m,r}.
- Verified: rank-one 250 random cases worst error 7.1e-13 (exact intrinsic
  count 2m+1 outputs); rank-r closure 140 valid charts worst 7.2e-15;
  antipodal separation exact (affine odd / quadratic even), r=5,7,9.
- Position vs R211: R211 pays 2^d per probe (reset access, arbitrary z);
  R212 pays exactly D_{m,r} raw outputs (no reset, one scalar walk). Both
  recover the low-rank object to machine precision in noiseless arithmetic.

## Single consolidated validation (2026-09-18) — ALL 7 CHECKS PASS
validate_all.py -> R212_VALIDATION.txt (one process, subprocess-isolated certs):
1. intrinsic_core: 160 rank-one no-reset cases, worst err 7.12e-13 (exact 2m+1 outputs)
2. rank_r_closure: 104 valid charts, worst err 6.22e-15
3. antipodal_separation: affine odd / quadratic even, exact, r=5,7,9
4. phasezero_replay: PASS
5. bipartite_unimodular: det B_h = +-1, PASS
6. cubic_cert: Res = -780 / 23004 / -192, PASS
7. fixed_state_cert: K0/K1/K2 + delta bridge + physical nodes, PASS
Note: earlier in-process exec version reported false FAILs (stdout redirect did
not capture child prints under exec); subprocess isolation is the correct
harness. Both lines (R211 reset-probe, R212 no-reset intrinsic) now share ONE
validated artifact set in this directory. Sources used together: ALAN report
+ paper draft + desktop verify suite + Developer repair bundle + R211 engine.

## Q195 attack log (2026-09-18) — FIRST PROBES, problem remains OPEN
Scope confirmation: repair bundle's DEBT_STATUS lists Q195/Q196 as genuine open
mathematics; the repaired resonant cert covers the L=3,n=d resonant family,
NOT the reflection regime u^d=v^d where Q195 lives. Open confirmed.
Executed probes (exact arithmetic, d=3..11, r=3d):
1. Cumulative phases P_k from the validated schedule_L3 word — total drift
   P_r = r*n + sum(g), consistent (d=9: 621 = 27*9 + 378).
2. Forward suffix rows S_j = sum_{i<j} pi([i->j]) with pi = anti-periodic
   x^{P_j-P_i-1}: the (r x r) suffix matrix has FULL rank r for all d —
   one-sided injectivity of the physical suffix map CONFIRMED numerically
   (report claims this proved; consistent).
3. Naive two-sided joint kernel [C_fwd | C_rev] (rev = edges out of j to later
   prefixes): nullity = r, dominated by mixed vectors with SINGLETON rev
   support — these are the telescoping relations S_j - S_{j+1} = -[j->j+1],
   legal row-space objects, NOT collisions.
HONEST VERDICT: the naive joint-matrix probe does NOT instantiate the report's
packet spaces (C~-> = lifted interval code, C~<- = J_xi image; relations not
free spans). Nothing about Q195 is settled either way by these probes. The
true interval-code generators are not fully specified in the consolidated
report or repair bundle — rebuilding them needs S1 (AI_NATIVE_MATH_MASTER
_HANDOFF_2026-09-08) or the original Q195 derivation. Next concrete step:
ask user for S1's interval-code construction, OR derive the lifted code from
the successor-splice word directly (risk: guessing conventions).

## Q195 attack (2026-09-18, session 2) — EVIDENCE FOR PASS, not yet a theorem
S1 (AI_NATIVE_MATH_MASTER_HANDOFF_2026-09-08) + Q193/Q194 source ingested.
Executed the true two-sided collision test with the suffix-difference lift:
- Word: exact states from schedule_L3 (validated cert machinery), n0 in {1,2},
  d = 3..15 (r = 3d). P_k cumulative phases; edges [i->j] over prefix set;
  pi([i->j]) = anti-periodic x^{P_j-P_i-1} histogram over r bins.
- C~-> = span{ tildeQ_{T_{i+1}} - tildeQ_{T_i} }, i = 0..H-3, over the ordered
  F* chronology (P = h_{d-1} = R_d at time d; F minus (0,2p)).
- C~<- = J_xi image (edge reversal).
- FORMAL consistency check: C~-> ∩ C~<- = 0 in edge coordinates for ALL
  tested (d, n0) — independently CONFIRMS the report's formal transversality.
- Q195 KERNEL TEST: joint physical matrix [pi(C~->) | pi(C~<-)] has NULLITY 0
  for every (d, n0) tested => NO two-sided collision, i.e. the width-3
  helical organism has NO surviving mode through both boundaries.
- Non-vacuousness: pi is far from injective on the full edge space (d=7:
  231 edges -> 41 bins, up to 10 edges/bin), so nullity 0 is CONTENT.
- Falsification sweep: enlarging C~-> to all pairwise F* generators gives
  nullity > 0, but those are boundary (b_in/b_out) directions deliberately
  excluded by the Q193 surgery — they belong to Q196, not the bulk lemma.
  Their fwd-only rank is exactly H-1 (simplex structure, no collapse).
- Early bug found+fixed: P = h_{d-1} (time d), NOT q_{d-1}; initial duplicate
  time slot produced spurious nullity 2.
VERDICT: strong exact EVIDENCE that Q195 = PASS for L=3, n0 in {1,2}, d odd
3..15. NOT yet a proof: (i) Gamma's suffix-difference formula is our
reconstruction (consistent with S1 15.1 identity, verified d=3,5,7 both
forms); (ii) finite d range; (iii) s=0 untwisted sector not separately swept.
NEXT: Q196 (2D boundary closure: [(I+J)b_in] and [P(u)P(v)] span D_xi) —
now testable with the same machinery; and push d range / write the local
3-face transport derivation the handoff asks for.
