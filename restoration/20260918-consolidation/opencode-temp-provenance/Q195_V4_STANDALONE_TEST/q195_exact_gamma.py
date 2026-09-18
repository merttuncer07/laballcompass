"""Q195 exact-Gamma harness V3 (Phases 1-5 core).

# RECONSTRUCTED BY MUSE FROM USER-SPECIFIED INTERVAL DERIVATION (2026-09-18)
# NOT AN ORIGINAL SAVED UNIONALPHA FILE. Older sources
# (VOLTERRA_ALAN_MASTER_HANDOFF_2026-09-03 (2).md, Arastirma Devami.txt)
# were NOT found locally and occur NOWHERE in stored history; the
# identities below are verified directly (proof in
# Q195_EXACT_INTERVAL_DERIVATION.md + machine checks in run_q195_v3.py).

Finite-field exact arithmetic (no floats). Conventions:
- word: R_{k+1} = 1 + x^{s_k} R_k, P_0 = 0, P_{k+1} = P_k + s_k, R_0 = 1.
- quadratic values Q_k = R_k(u) R_k(v), xi = u v.
- suffix_Q_h(x) = x^{s_{h-1}-1} R_{h-1}(x), called A-helpers, NEVER Q_k.
"""

# ---------- small sparse polys over F_p, reduced mod (x^r + 1) ----------

def _modp(a, p):
    return a % p


def padd(a, b, p):
    c = {e: v % p for e, v in a.items() if v % p != 0}
    for e, v in b.items():
        c[e] = (c.get(e, 0) + v) % p
        if c[e] == 0:
            del c[e]
    return c


def pscale(a, s, p):
    s %= p
    if s == 0:
        return {}
    return {e: (v * s) % p for e, v in a.items() if (v * s) % p}


def px_shift_mul(a, k, p, r):
    """a(x) * x^k reduced mod x^r + 1 over F_p. Handles negative k."""
    out = {}
    for e, v in a.items():
        t = e + k
        m = 0
        while t < 0:
            t += r
            m += 1
        q_, rem = divmod(t, r)
        sgn = (-1) ** (q_ + m)
        out[rem] = (out.get(rem, 0) + sgn * v) % p
    return {e: v % p for e, v in out.items() if v % p != 0}


def peval(a, x, p):
    return sum(v * pow(x, e, p) for e, v in a.items()) % p


def pvec(a, r, p):
    return [a.get(e, 0) % p for e in range(r)]


# ---------- finite field roots ----------

def prim_root(p):
    phi = p - 1
    fac = []
    n = phi
    d = 2
    while d * d <= n:
        if n % d == 0:
            fac.append(d)
            while n % d == 0:
                n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        fac.append(n)
    for g in range(2, p):
        if all(pow(g, phi // q, p) != 1 for q in fac):
            return g
    raise ValueError("no primitive root")


def rth_roots(p, r):
    assert (p - 1) % r == 0, f"r={r} does not divide p-1={p-1}"
    g = prim_root(p)
    xi0 = pow(g, (p - 1) // r, p)
    assert pow(xi0, r, p) == 1 and xi0 != 1
    return [pow(xi0, e, p) for e in range(r)]


# ---------- integer word (L=3 schedule), states as int polys ----------

def int_word(d, n0, schedule_L3):
    """Unreduced integer states: R_{k+1} = 1 + x^{s_k} R_k as formal polys."""
    r, n, e, U, B, F, Fs, g = schedule_L3(d, n0)
    s = [n + g[k] for k in range(r)]
    R = [{0: 1}]
    for sk in s:
        sh = {e + sk: v for e, v in R[-1].items()}
        nxt = dict(sh)
        nxt[0] = nxt.get(0, 0) + 1
        R.append(nxt)
    P = [0]
    for sk in s:
        P.append(P[-1] + sk)
    return r, n, s, R, P
    P = [0]
    for sk in s:
        P.append(P[-1] + sk)
    return r, n, s, R, P


def px_shift_mul_int(a, k, r):
    out = {}
    for e, v in a.items():
        q_, rem = divmod(e + k, r)
        out[rem] = out.get(rem, 0) + ((-1) ** q_) * v
    return {e: v for e, v in out.items() if v != 0}


def suffix_Q_int(R, s, h, r):
    """suffix_Q_h(x) = x^{s_{h-1}-1} R_{h-1}(x), h >= 1, formal (unreduced)."""
    assert h >= 1
    return {e + s[h - 1] - 1: v for e, v in R[h - 1].items()}


def reduce_qr(poly, p, r):
    """Reduce integer poly mod (x^r + 1) over F_p -> length-r vector."""
    out = [0] * r
    for e, v in poly.items():
        q_, rem = divmod(e, r)
        out[rem] = (out[rem] + ((-1) ** q_) * v) % p
    return out


# ---------- exact F_p linear algebra ----------

def fp_rank(rows, p):
    M = [list(map(lambda x: x % p, row)) for row in rows]
    m = len(M)
    n = len(M[0]) if m else 0
    r_ = 0
    for c in range(n):
        piv = next((i for i in range(r_, m) if M[i][c] % p != 0), None)
        if piv is None:
            continue
        M[r_], M[piv] = M[piv], M[r_]
        inv = pow(M[r_][c], p - 2, p)
        M[r_] = [(v * inv) % p for v in M[r_]]
        for i in range(m):
            if i != r_ and M[i][c] % p != 0:
                f = M[i][c]
                M[i] = [(a - f * b) % p for a, b in zip(M[i], M[r_])]
        r_ += 1
    return r_


def fp_nullity(rows, p):
    """Dimension of left kernel of row-list (nullspace of row space)."""
    if not rows:
        return 0
    n = len(rows[0])
    return n - fp_rank(rows, p)


# ---------- Phase 3: formal interval packets ----------

def formal_packet(R, P, s, a, b, xi, p):
    """Ã_{a,b} as {(i,h): w} over formal edges + scalar c. (Phase 3)"""
    w = interval_weights(P, a, b, xi, p)
    pk = {}
    for h in range(a + 1, b + 1):
        for i in range(h):
            pk[(i, h)] = (pk.get((i, h), 0) + w[h]) % p
    pk = {e: v for e, v in pk.items() if v}
    return pk, sum(w.values()) % p


def pi_packet_formal(pk, P, r):
    """Unreduced formal image: {(P_h - P_i - 1): coeff}."""
    out = {}
    for (i, h), w in pk.items():
        e = P[h] - P[i] - 1
        out[e] = out.get(e, 0) + w
    return out


# ---------- Phase 4: weighted reversal + suffix involution ----------

def J_formal(pk, P, xi, p):
    """J_xi[i->j] = xi^{P_j-P_i} [j->i]. (Phase 4, derived)"""
    out = {}
    for (i, j), w in pk.items():
        out[(j, i)] = (out.get((j, i), 0)
                       + w * pow(xi, P[j] - P[i], p)) % p
    return {e: v for e, v in out.items() if v}


def x_negpow(k, p, r):
    """x^{-k} mod (x^r+1) over F_p as {exp: coeff}."""
    m = (k + r - 1) // r if k > 0 else 0
    t = m * r - k
    return {t: (1 if m % 2 == 0 else p - 1)}


def Jhat_mon(D, xi, p, r):
    """Ĵ x^D = xi^{D+1} x^{-D-2} in the ring. (Phase 4)"""
    return pscale(x_negpow(D + 2, p, r), pow(xi, D + 1, p), p)


def J_poly(a, xi, p, r):
    """Physical involution: J1 = 1, Jx^h = -xi^h x^{r-h} (1 <= h < r)."""
    red = reduce_qr(a, p, r)
    out = [0] * r
    out[0] = (out[0] + red[0]) % p
    for h in range(1, r):
        if red[h]:
            out[(r - h) % r] = (out[(r - h) % r]
                                - pow(xi, h, p) * red[h]) % p
    return out


# ---------- Phase 5: augmented projection ----------

def Pi_augmented(pk, c, P, p, r):
    """Pi_xi(packet, c) = c/2 + x pi(packet), reduced ring vector."""
    img = pi_packet_formal(pk, P, r)
    shifted = {e + 1: v for e, v in img.items()}
    vec = reduce_qr(shifted, p, r)
    vec[0] = (vec[0] + c * pow(2, p - 2, p)) % p
    return vec


# ---------- Phases 6-7: faithful chronology + exact interval objects ----------

def fstar_chronology(d):
    """V2-verified source-faithful F* (Phase 6 hard-checks in driver)."""
    r = 3 * d
    e = (d - 1) // 2
    t = lambda kind, a: (r - 2 - 2 * a) if kind == 'h' else (r - 1 - 2 * a)
    keys = ([('q', a) for a in range(1, d)]
            + [('h', a) for a in range(e + 1)]
            + [('h', d - 1)])
    ordered = sorted(keys, key=lambda x: t(*x))
    return [t(*x) for x in ordered], ordered


def gamma_packet(R, P, s, T0, T1, xi, p, r):
    """Exact interval object for [T0, T1]: ((packet, c), Gamma-vector)."""
    pk, c = formal_packet(R, P, s, T0, T1, xi, p)
    Gam, _, _ = centered_gamma(R, P, T0, T1, xi, p)
    return (pk, c), reduce_qr(Gam, p, r)


# ---------- Phase 1: quadratic telescoping + centered Gamma ----------

def quad_values(R, u, v, p):
    Ru = [peval(a, u, p) for a in R]
    Rv = [peval(a, v, p) for a in R]
    return [(a * b) % p for a, b in zip(Ru, Rv)]


def interval_weights(P, a, b, xi, p):
    return {h: pow(xi, P[b] - P[h], p) for h in range(a + 1, b + 1)}


def centered_gamma(R, P, a, b, xi, p):
    """Gamma[a,b](x) = G - c/2 with G = sum w_h R_h. Integer R reduced mod p."""
    w = interval_weights(P, a, b, xi, p)
    G = {}
    for h, wh in w.items():
        G = padd(G, pscale({e: v % p for e, v in R[h].items()}, wh, p), p)
    c = sum(w.values()) % p
    inv2 = pow(2, p - 2, p)
    Gam = padd(G, {0: (-c * inv2) % p}, p)
    return Gam, c, w
