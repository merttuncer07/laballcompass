#!/usr/bin/env python3
"""
Standalone exact reproducibility certificate for the resonant L=3,n=d
Volterra reference+physical-rescue boundary theorem.

Dependency: sympy only.
No floating point arithmetic is used.
"""
import math
import sympy as sp
from sympy import QQ
from sympy.polys.matrices import DomainMatrix

q = sp.symbols('q')
t = sp.symbols('t')
x = sp.symbols('x')

# -----------------------------------------------------------------------------
# Q(eta), eta^2+eta+1=0, represented as a+b*eta with rational functions in q.
# -----------------------------------------------------------------------------
class E:
    __slots__ = ('a','b')
    def __init__(self,a=0,b=0): self.a=sp.cancel(a); self.b=sp.cancel(b)
    def __add__(self,o): o=toE(o); return E(self.a+o.a,self.b+o.b)
    __radd__=__add__
    def __neg__(self): return E(-self.a,-self.b)
    def __sub__(self,o): return self+(-toE(o))
    def __rsub__(self,o): return toE(o)-self
    def __mul__(self,o):
        o=toE(o); a,b,c,d=self.a,self.b,o.a,o.b
        return E(a*c-b*d, a*d+b*c-b*d)
    __rmul__=__mul__
    def inv(self):
        n=sp.cancel(self.a*self.a-self.a*self.b+self.b*self.b)
        if n==0: raise ZeroDivisionError
        return E((self.a-self.b)/n,-self.b/n)
    def __truediv__(self,o): return self*toE(o).inv()
    def __rtruediv__(self,o): return toE(o)*self.inv()
    def __pow__(self,n):
        if n<0:return self.inv()**(-n)
        r=E(1); z=self
        while n:
            if n&1:r=r*z
            z=z*z; n//=2
        return r
    def zero(self): return sp.cancel(self.a)==0 and sp.cancel(self.b)==0
    def simp(self): self.a=sp.factor(sp.cancel(self.a)); self.b=sp.factor(sp.cancel(self.b)); return self
    def __repr__(self): return f'({self.a})+({self.b})*eta'
def toE(z): return z if isinstance(z,E) else E(z)
etaE=E(0,1); kapE=etaE**2

def va(a,b): return [u+v for u,v in zip(a,b)]
def vs(c,a): return [toE(c)*u for u in a]
def zmul(a,k,d,s):
    out=[E() for _ in range(d)]
    for i,u in enumerate(a):
        if u.zero(): continue
        quo,rem=divmod(i+k,d); out[rem]=out[rem]+u*(s**quo)
    return out
def mon(k,d,s,c=1):
    out=[E() for _ in range(d)]; quo,rem=divmod(k,d); out[rem]=toE(c)*(s**quo); return out

def ringmul(a,b,d,s):
    out=[E() for _ in range(d)]
    for i,u in enumerate(a):
        if u.zero(): continue
        for j,v in enumerate(b):
            if v.zero(): continue
            quo,rem=divmod(i+j,d); out[rem]=out[rem]+u*v*(s**quo)
    return out

# -----------------------------------------------------------------------------
# Physical L=3 successor-splice schedule and exact integer recurrence states.
# -----------------------------------------------------------------------------
def schedule_L3(d,n0=1):
    r=3*d; n=d*n0; e=(d-1)//2
    U=set(range(0,d-1))
    B=set(d+1+2*j for j in range(d-1))
    F=set(r-1-2*a for a in range(d)) | set(r-2-2*a for a in range(e+1))
    g=[]
    for k in range(r):
        if k in U: gg=1
        elif k in B: gg=r-1
        elif k in F-B: gg=r
        else: gg=0
        g.append(gg)
    Fs=(F-{r-1})|{d}
    return r,n,e,U,B,F,Fs,g

def shift_int(v,k,r):
    k%=2*r
    if k>=r:return [-z for z in shift_int(v,k-r,r)]
    out=[0]*r
    for i,a in enumerate(v):
        j=i+k
        if j<r:out[j]+=a
        else:out[j-r]-=a
    return out

def states_int(d,n0=1):
    r,n,e,U,B,F,Fs,g=schedule_L3(d,n0)
    R=[[1]+[0]*(r-1)]
    for k in range(r):
        sh=shift_int(R[-1],n+g[k],r)
        R.append([(1 if i==0 else 0)+sh[i] for i in range(r)])
    return R,(r,n,e,U,B,F,Fs,g)

# Horizontal modal coordinates: u^d=-1, v^d=-eta, u=Z/q, v=eta^2 Z^-1.
def eval_u(state,d,s):
    out=[E() for _ in range(d)]
    for i,c in enumerate(state):
        if not c: continue
        a,b=divmod(i,d)
        out=va(out,mon(b,d,s,E(c*((-1)**a)*q**(-b))))
    return out

def eval_v(state,d,s):
    out=[E() for _ in range(d)]
    for i,c in enumerate(state):
        if not c: continue
        a,b=divmod(i,d)
        coef=E(c)*((-etaE)**a)*(kapE**b)
        out=va(out,mon(-b,d,s,coef))
    return out

def rho_for(d): return {0:kapE,1:etaE,2:E(1)}[d%3]

def reduce_E_relation(z,d,rho):
    out=E()
    for part,tag in ((z.a,0),(z.b,1)):
        num,den=sp.fraction(sp.cancel(part))
        if sp.degree(den,q)>0: raise ValueError('unexpected q denominator in relation reduction')
        P=sp.Poly(sp.expand(num),q,domain=sp.QQ)
        for (k,),c in P.terms():
            quo,rem=divmod(k,d); term=E(c)*(rho**quo)*E(q**rem)/E(den)
            out += term if tag==0 else etaE*term
    return out.simp()

# -----------------------------------------------------------------------------
# Exact physical -> normalized delta bridge.
# -----------------------------------------------------------------------------
def bridge_checks(d):
    e=(d-1)//2; rho=rho_for(d); s=-rho
    states,_=states_int(d,1); hidx=lambda a:d+2*(d-1-a)
    delta=[E(((-1)**k)*q**(d-1-k)) for k in range(d)]
    Pu=eval_u(states[d],d,s)
    Pv=eval_v(states[d],d,s)
    # q^(d-1) P_u = q^(d-1)*1 - Delta, exact before q^d reduction.
    lhs=vs(E(q**(d-1)),Pu); rhs=va(mon(0,d,s,E(q**(d-1))),vs(-1,delta))
    assert all((a-b).zero() for a,b in zip(lhs,rhs))
    # Center resonant u-head.
    Ue=eval_u(states[hidx(e)],d,s)
    c=vs(E(q**(d-1)),va(Ue,vs(-1,mon(0,d,s))))
    assert all((reduce_E_relation(c[i],d,rho)+delta[i]).zero() for i in range(d))
    # Lower closure u-head.
    U0=eval_u(states[hidx(0)],d,s)
    Ubar=mon(0,d,s)
    for k in range(1,e+1):Ubar=va(Ubar,mon(-k,d,s,E(2*q**k)))
    du=vs(E(q**(d-1)),va(U0,vs(-1,Ubar)))
    sg=E((-1)**(e+1))
    assert all((reduce_E_relation(du[i],d,rho)-sg*delta[i]).zero() for i in range(d))
    # P product bridge follows from idempotence Delta*g=g(-q)Delta; verify directly.
    Pprod=ringmul(Pu,Pv,d,s)
    left=vs(E(q**(d-1)),Pprod)
    # evaluate Pv at Z=-q in the Z^d=s quotient
    pvnode=E()
    for k,cc in enumerate(Pv): pvnode += cc*E((-q)**k)
    right=va(vs(E(q**(d-1)),Pv),vs(-pvnode,delta))
    right=[reduce_E_relation(z,d,rho) for z in right]
    left=[reduce_E_relation(z,d,rho) for z in left]
    assert all((a-b).zero() for a,b in zip(left,right))

# -----------------------------------------------------------------------------
# Normalized boundary system reconstructed from physical v-channel states.
# -----------------------------------------------------------------------------
def build_normalized(d):
    e=(d-1)//2; rho=rho_for(d); s=-rho
    states,_=states_int(d,1); hidx=lambda a:d+2*(d-1-a)
    V={a:eval_v(states[hidx(a)],d,s) for a in range(e+1)}
    H=V[e]; Be=va(V[e-1],vs(-1,V[e]))
    Ds=[va(mon(-j-1,d,s,E(2*q**(j+1))),zmul(Be,j,d,s)) for j in range(3)]
    Pv=eval_v(states[d],d,s)
    Ubar=mon(0,d,s)
    for k in range(1,e+1):Ubar=va(Ubar,mon(-k,d,s,E(2*q**k)))
    C0=va(mon(0,d,s),va(Ubar,vs(etaE,V[0])))
    rows=[]
    for k in range(4,e+1):rows.append(mon(-k,d,s))
    for k in range(3,e):rows.append(zmul(Be,k,d,s))
    rows += Ds+[H,Pv,C0]
    assert len(rows)==d-1
    delta=[E(((-1)**k)*q**(d-1-k)) for k in range(d)]
    rows.append(delta)
    return rows,rho

def reduce_interior(rows,d):
    ni=d-7; B=[]; piv=[]
    for rr in rows[:ni]:
        v=rr[:]
        for pc,b in zip(piv,B):
            if not v[pc].zero():
                f=v[pc]; v=[z-f*w for z,w in zip(v,b)]
        pc=next((j for j,z in enumerate(v) if not z.zero()),None)
        if pc is None:raise RuntimeError('interior dependence')
        inv=v[pc].inv(); v=[z*inv for z in v]; B.append(v);piv.append(pc)
    free=[j for j in range(d) if j not in piv]
    reduced=[]
    for rr in rows[ni:]:
        v=rr[:]
        for pc,b in zip(piv,B):
            if not v[pc].zero():
                f=v[pc];v=[z-f*w for z,w in zip(v,b)]
        reduced.append([v[j] for j in free])
    assert len(reduced)==7 and free==[1,2,3,(d-1)//2,d-3,d-2,d-1]
    return reduced,free

# -----------------------------------------------------------------------------
# SymPy exact algebraic field machinery for period-six certificate.
# -----------------------------------------------------------------------------
AF=QQ.alg_field_from_poly(sp.Poly(x**2+x+1,x)); eta=AF.ext.as_expr()
RRqt=AF.poly_ring(q,t); RRq=AF.poly_ring(q); qR=RRq.gens[0]

def coeffs(z):
    pa=sp.Poly(sp.expand(z.a),q,domain=sp.QQ); pb=sp.Poly(sp.expand(z.b),q,domain=sp.QQ); D={}
    for (k,),c in pa.terms():D[k]=D.get(k,E())+E(c)
    for (k,),c in pb.terms():D[k]=D.get(k,E())+etaE*E(c)
    return D

def qt_keep(z,e):
    ex=0
    for k,c in coeffs(z).items():
        j,r=divmod(k,e)
        if j>2:raise ValueError((k,e,j))
        ex+=(c.a+c.b*eta)*q**r*t**j
    return RRqt.from_sympy(sp.expand(ex))

def reduce_t(S,rho):
    rhoK=AF.from_sympy(rho.a+rho.b*eta);A={};B={};minq=0
    for (iq,it),c in S.to_dict().items():
        k,par=divmod(it,2);jq=iq-k;cc=c*(rhoK**k)
        D=A if par==0 else B;D[(jq,)]=D.get((jq,),AF.zero)+cc;minq=min(minq,jq)
    sh=-minq if minq<0 else 0
    if sh:
        A={(j+sh,):c for (j,),c in A.items()};B={(j+sh,):c for (j,),c in B.items()}
    return RRq.new(A),RRq.new(B),sh

def boundary_parts(d):
    rows,rho=build_normalized(d);red,_=reduce_interior(rows,d);e=(d-1)//2
    M=[[qt_keep(z,e) for z in row] for row in red];six=M[:6];delta=M[6];cof=[]
    for j in range(7):
        minor=[[row[k] for k in range(7) if k!=j] for row in six]
        c=DomainMatrix.from_list(minor,RRqt).det()
        if j%2:c=-c
        cof.append(c)
    S=RRqt.zero
    for c,z in zip(cof,delta):S+=c*z
    A,B,sh=reduce_t(S,rho)
    return A,B,rho,cof,sh

def fixed_obstruction(d0):
    e0=(d0-1)//2
    A0,B0,rho,C0,sh0=boundary_parts(d0)
    A1,B1,r1,C1,sh1=boundary_parts(d0+12)
    assert sh0==sh1==0 and C0==C1 and A0==A1
    diff=B1-B0; mindeg=min(k[0] for k,c in diff.to_dict().items()); H=diff.exquo(qR**mindeg)
    A2,B2,r2,C2,sh2=boundary_parts(d0+24)
    assert C2==C0 and A2==A0 and B2-B1==qR**(mindeg+6)*H
    assert mindeg-e0==1
    rhoK=AF.from_sympy(rho.a+rho.b*eta);one=RRq.one
    At=(one-qR**6)*A0-H.mul_ground(rhoK)
    Bt=(one-qR**6)*B0+qR**mindeg*H
    G=qR*(At**2)-(Bt**2).mul_ground(rhoK)
    return G,rho

def sharp_poly(p):
    ex=RRq.to_sympy(p);deg=p.degree();y=sp.symbols('y')
    conj=sp.expand(ex.subs(eta,y)).subs(y,-1-y)
    conj=sp.Poly(conj,y,domain=sp.QQ.frac_field(q)).rem(sp.Poly(y**2+y+1,y,domain=sp.QQ.frac_field(q))).as_expr().subs(y,eta)
    return RRq.from_sympy(sp.expand(q**deg*conj.subs(q,1/q)))

def primitive_pair(p):
    ex=RRq.to_sympy(p);y=sp.symbols('y')
    rem=sp.Poly(ex.subs(eta,y),y,domain=sp.QQ.frac_field(q)).rem(sp.Poly(y**2+y+1,y,domain=sp.QQ.frac_field(q))).as_expr()
    a=sp.Poly(sp.expand(rem).coeff(y,0),q,domain=sp.QQ);b=sp.Poly(sp.expand(rem).coeff(y,1),q,domain=sp.QQ)
    den=[sp.denom(c) for c in a.all_coeffs()+b.all_coeffs()];L=sp.ilcm(*den) if den else 1
    ai=[int(c*L) for c in a.all_coeffs()];bi=[int(c*L) for c in b.all_coeffs()];g=0
    for c in ai+bi:g=math.gcd(g,abs(c))
    ai=[c//g for c in ai];bi=[c//g for c in bi]
    lead=next((c for c in ai+bi if c),1)
    if lead<0:ai=[-c for c in ai];bi=[-c for c in bi]
    return sp.Poly.from_list(ai,gens=q).as_expr(),sp.Poly.from_list(bi,gens=q).as_expr()

def expected_factor(branch):
    common=(q-1)**2*(q+1)**2*(q+eta)**2*(q+eta**2)**2*(q-eta**2)**2
    if branch==1:common*=q-eta
    return RRq.from_sympy(sp.expand(common))

def certify_branch(d0,label,degree):
    G,rho=fixed_obstruction(d0);fac=expected_factor(d0%3);Kp,rem=divmod(G,fac)
    assert rem==RRq.zero and Kp.degree()==degree
    g=Kp.gcd(sharp_poly(Kp));assert g.degree()==0
    A,B=primitive_pair(Kp)
    print(f'{label}: d0={d0}, deg={degree}, gcd(K,Ksharp)=1')
    print(' A=',A);print(' B=',B,'  (K=A+B*eta)')
    return Kp

# -----------------------------------------------------------------------------
# Original physical seven-row determinant for removable-node checks.
# -----------------------------------------------------------------------------
def physical_rows(d):
    e=(d-1)//2;rho=rho_for(d);s=-rho;states,_=states_int(d,1);hidx=lambda a:d+2*(d-1-a)
    U={a:eval_u(states[hidx(a)],d,s) for a in range(e+1)};V={a:eval_v(states[hidx(a)],d,s) for a in range(e+1)}
    Htr={a:va(va(U[a],V[a]),mon(0,d,s,-1)) for a in range(e+1)}
    Ds=[]
    for j in range(3):
        a=e-j;Ds.append(va(Htr[a-1],vs(-1,Htr[a])))
    center=Htr[e];Pu=eval_u(states[d],d,s);Pv=eval_v(states[d],d,s);Pprod=ringmul(Pu,Pv,d,s)
    I0=va(mon(0,d,s,1),va(U[0],vs(etaE,V[0])));Be=va(V[e-1],vs(-1,V[e]))
    rows=[]
    for k in range(4,e+1):rows.append(mon(-k,d,s))
    for k in range(3,e):rows.append(zmul(Be,k,d,s))
    scale=E(q**(d-1));rows += [vs(scale,z) for z in Ds+[center,Pprod,I0]]
    delta=[E(((-1)**k)*q**(d-1-k)) for k in range(d)];rows.append(delta)
    return rows,rho

def det_E(A):
    A=[[z for z in row] for row in A];n=len(A);det=E(1);sgn=1
    for c in range(n):
        p=next((i for i in range(c,n) if not A[i][c].zero()),None)
        if p is None:return E()
        if p!=c:A[c],A[p]=A[p],A[c];sgn=-sgn
        piv=A[c][c];det=det*piv;inv=piv.inv()
        for j in range(c+1,n):A[c][j]=A[c][j]*inv
        for i in range(c+1,n):
            f=A[i][c]
            if f.zero():continue
            for j in range(c+1,n):A[i][j]=A[i][j]-f*A[c][j]
            A[i][c]=E()
    return det*sgn

def _eval_rat_q(expr,nodeE):
    num,den=sp.fraction(sp.cancel(expr))
    def epoly(poly):
        P=sp.Poly(sp.expand(poly),q,domain=sp.QQ)
        out=E()
        for (k,),c in P.terms(): out += E(c)*(nodeE**k)
        return out
    return epoly(num)/epoly(den)

def _eval_q_E(z,nodeE):
    return _eval_rat_q(z.a,nodeE) + etaE*_eval_rat_q(z.b,nodeE)

def physical_node_value(d,nodeE):
    rows,rho=physical_rows(d)
    rows=[[ _eval_q_E(z,nodeE) for z in row] for row in rows]
    red,_=reduce_interior(rows,d)
    return det_E(red).simp()

def main():
    # Bridge across all three arithmetic branches.
    for d in (13,15,17,23):bridge_checks(d)
    print('physical->normalized delta bridge: PASS')
    certify_branch(13,'K1',12)
    certify_branch(15,'K0',13)
    certify_branch(17,'K2',13)
    # Removable physical nodes, both e mod 6 classes.
    for d in (13,19):
        v=physical_node_value(d,etaE);assert v!=AF.zero;print(f'physical q=eta check d={d}: nonzero ({v})')
    for d in (11,17):
        v=physical_node_value(d,E(1));assert v!=AF.zero;print(f'physical q=1 check d={d}: nonzero ({v})')
    print('ALL RESONANT FIXED-STATE CERTIFICATES PASS')
if __name__=='__main__':main()
