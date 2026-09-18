#!/usr/bin/env python3
"""Self-contained exact replay for the Volterra phase-zero repair chart.

Reconstructs the physical recurrence realization directly from T^r=-I and
R_{k+1}=e0 + T^(n+g_k) R_k, so it has no dependency on the missing historical
VOLTERRA_UNIMODULAR_SIMPLEX / VOLTERRA_EVEN_BOOST_ORBIT modules.

Default run reproduces the determinant and small Smith-form data recorded in
VOLTERRA_PHASEZERO_REPAIR_RUN (1).txt (up to harmless affine-anchor orientation
signs in det(A)).
"""
from __future__ import annotations
import argparse
from collections import Counter
import math
import sympy as sp
from sympy.matrices.normalforms import smith_normal_form
from sympy.polys.domains import ZZ


def shift(v, k, r):
    """Multiply coefficient vector by x^k in Z[x]/(x^r+1)."""
    k %= 2*r
    if k >= r:
        return [-x for x in shift(v, k-r, r)]
    out = [0]*r
    for i,a in enumerate(v):
        j = i+k
        if j < r:
            out[j] += a
        else:
            out[j-r] -= a
    return out


def add_e0(v):
    w = list(v)
    w[0] += 1
    return w


def physical_realization(r: int, nu: int):
    assert r >= 3 and r % 2 == 1 and nu >= 1
    n = nu*r - 1
    boosted = set(range(1, r, 2))
    gaps = [2 + (r if k in boosted else 0) for k in range(r)]

    # R_k = recurrence state at quotient surface k.
    R = [[1] + [0]*(r-1)]
    X = []
    pos = []
    for k,g in enumerate(gaps):
        p = len(X)
        pos.append(p)
        X.append(R[k])
        # Zero-residual samples within this gap are T^(n+j) R_k.
        for j in range(1, g+1):
            X.append(shift(R[k], n+j, r))
        R.append(add_e0(shift(R[k], n+g, r)))
    pos.append(len(X))
    return X, pos, boosted


def repair_matrix(r: int, nu: int):
    X, pos, boosted = physical_realization(r, nu)
    s = 2
    anchors = []
    for k,p in enumerate(pos[:-1]):
        # even/unboosted: second zero point; odd/boosted: antipodal endpoint
        anchors.append(sp.Matrix(X[p+s+r] if k in boosted else X[p+s]))
    A = sp.Matrix.hstack(*anchors)
    detA = int(A.det())
    if abs(detA) != 1:
        raise AssertionError((r,nu,"affine anchor not unimodular",detA))
    Ai = A.inv()
    if any(x.q != 1 for x in Ai):
        raise AssertionError((r,nu,"inverse not integral"))

    def coords(v):
        y = Ai * sp.Matrix(v)
        return [int(x) for x in y]

    def half_curv(y):
        out = [y[i]*(y[i]-1)//2 for i in range(r)]
        out += [y[i]*y[j] for i in range(r) for j in range(i+1,r)]
        return out

    rows = []
    # First zero point from every surface.
    for k,p in enumerate(pos[:-1]):
        rows.append(half_curv(coords(X[p+1])))
    # Full r-point orbit from every boosted odd surface.
    for k,p in enumerate(pos[:-1]):
        if k in boosted:
            for t in range(r):
                rows.append(half_curv(coords(X[p+s+t])))

    M = sp.Matrix(rows)
    qh = r*(r+1)//2
    assert M.shape == (qh,qh)
    return detA, M


def expected_abs_det(r, nu):
    return 1 if nu % 2 == 0 else r-2


def exact_table(max_r=13):
    print("EXACT DETERMINANTS OF M = Psi/2")
    for r in range(3,max_r+1,2):
        vals=[]
        for nu in (1,2):
            detA,M = repair_matrix(r,nu)
            d = int(M.det())
            exp = expected_abs_det(r,nu)
            assert abs(d) == exp, (r,nu,d,exp)
            vals.append((nu,detA,d,exp))
        print("r=",r,vals)


def smith_cases(cases=((5,1),(5,2),(7,1),(7,2),(9,1),(9,2))):
    print("\nEXACT SMITH FORMS")
    for r,nu in cases:
        _,M = repair_matrix(r,nu)
        S = smith_normal_form(M,domain=ZZ)
        diag=[abs(int(S[i,i])) for i in range(S.rows)]
        c=Counter(diag)
        target = Counter({1:M.rows}) if nu%2==0 else Counter({1:M.rows-1,r-2:1})
        assert c == target, (r,nu,c,target)
        print(f"r {r} nu {nu} {dict(c)}")


def rank_mod(A, p):
    A=[[(int(x)%p) for x in row] for row in A.tolist()]
    m=len(A); n=len(A[0]) if m else 0; row=0
    for col in range(n):
        piv=next((i for i in range(row,m) if A[i][col]),None)
        if piv is None: continue
        A[row],A[piv]=A[piv],A[row]
        inv=pow(A[row][col],p-2,p)
        A[row]=[(x*inv)%p for x in A[row]]
        for i in range(row+1,m):
            if A[i][col]:
                f=A[i][col]
                A[i]=[(x-f*y)%p for x,y in zip(A[i],A[row])]
        row+=1
        if row==m: break
    return row


def modular_stress(max_r=25, nus=(1,2,3,4), p=1000003):
    print(f"\nMODULAR FULL-RANK STRESS odd r <= {max_r}, nu={list(nus)}, p={p}")
    bad=[]
    for r in range(3,max_r+1,2):
        qh=r*(r+1)//2
        vals=[]
        for nu in nus:
            detA,M=repair_matrix(r,nu)
            rk=rank_mod(M,p)
            vals.append((nu,detA,rk,qh))
        ok=all(abs(dA)==1 and rk==qh for nu,dA,rk,qh in vals)
        print(f"r {r:2d}:","PASS" if ok else vals)
        if not ok: bad.append((r,vals))
    assert not bad,bad
    print("bad= []")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--max-r',type=int,default=13,help='largest odd r for exact determinants')
    ap.add_argument('--stress',action='store_true',help='also run modular full-rank stress')
    ap.add_argument('--stress-max-r',type=int,default=25)
    args=ap.parse_args()
    exact_table(args.max_r)
    smith_cases()
    if args.stress:
        modular_stress(args.stress_max_r)
    print("\nPHASE-ZERO SELF-CONTAINED REPLAY: PASS")

if __name__=='__main__':
    main()
