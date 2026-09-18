#!/usr/bin/env python3
"""Dependency-free exact checker for the canonical phase-zero bipartite block B_h.

This checker verifies the algebraic object used in VOLTERRA_BIPARTITE_UNIMODULAR_NOTE.md.
It does not need the historical quotient/simplex modules.  The note proves that the
physical residual block is row-equivalent (permutation/signs) to this canonical block.
"""
from __future__ import annotations
import argparse
import sympy as sp


def canonical_matrix(h: int) -> sp.Matrix:
    assert h >= 1
    delta = (-1)**h
    a = [2*((-1)**j) for j in range(h)]
    b = [-x for x in a]
    b[-1] -= delta
    rows=[]
    # Sparse rows: X[i,h-1]-X[i,j]
    for i in range(h-1):
        for j in range(i,h-1):
            row=[0]*(h*h)
            row[i*h+(h-1)] += 1
            row[i*h+j] -= 1
            rows.append(row)
    # Dense rows (a+delta e_p)^T X b and (a+delta e_p)^T X(b+e_q)
    for p in range(h):
        u=a[:]; u[p]+=delta
        def outer_row(v):
            return [u[i]*v[j] for i in range(h) for j in range(h)]
        rows.append(outer_row(b))
        for q in range(p):
            v=b[:]; v[q]+=1
            rows.append(outer_row(v))
    M=sp.Matrix(rows)
    assert M.shape==(h*h,h*h)
    return M


def one_parameter_candidate(h: int, z0=1):
    # Candidate after all sparse rows and differences of dense equations.
    X=sp.zeros(h,h)
    for i in range(h):
        for j in range(h):
            X[i,j]=z0*((2*i+1) if i<=j else (2*j+2))
    delta=(-1)**h
    a=sp.Matrix([2*((-1)**j) for j in range(h)])
    b=-a
    b[h-1]-=delta
    A0=(a.T*X*b)[0]
    c0=(sp.eye(h).row(0)*X*b)[0]
    residual=sp.expand(A0+delta*c0)
    return X,sp.expand(A0),sp.expand(c0),sp.expand(residual)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--max-h',type=int,default=8)
    args=ap.parse_args()
    print('CANONICAL B_h EXACT DETERMINANTS')
    for h in range(1,args.max_h+1):
        M=canonical_matrix(h)
        d=int(M.det())
        assert abs(d)==1,(h,d)
        print(f'h={h:2d} r={2*h+1:2d} size={h*h:3d} det={d:+d}')
    print('\nONE-PARAMETER LAST-EQUATION CERTIFICATE')
    for h in range(1,max(args.max_h,10)+1):
        X,A0,c0,res=one_parameter_candidate(h,sp.Symbol('z0'))
        z0=sp.Symbol('z0')
        assert sp.expand(res+z0)==0,(h,res)
        print(f'h={h:2d}: A0={A0}, c0={c0}, residual={res}')
    print('\nEvery final residual is -z0.  The proof note derives the preceding reductions using only unit pivots.')
    print('PHASE-ZERO BIPARTITE UNIMODULAR STANDALONE CHECK: PASS')

if __name__=='__main__':
    main()
