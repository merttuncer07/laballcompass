"""
Certificate 4: exact quadratic-to-affine cancellation identity (Section "Exact
quadratic-to-affine cancellation", marked PROVED):

   Q_{k+1} - xi^{s_k} Q_k = R_{k+1}(u) + R_{k+1}(v) - 1

where R_{k+1} = 1 + x^{s_k} R_k, Q_k = R_k(u) R_k(v), xi = uv.

Certificate 5: the trigonometric identity underlying the P(T) distinguished
orbit theorem (Section 13, eq. 50):

   |C|^2 - 1 = 8 sin(Q/2) sin((A+Q)/2) cos(A/2),   C = 1 + a(1-q), a=e^{iA}, q=e^{iQ}
"""
import sympy as sp

print("=== Quadratic-to-affine identity ===")
# u, v, s_k assumed positive so that (uv)^{s_k} = u^{s_k} v^{s_k} without branch-cut
# ambiguity; this is the standard convention implicit in the report's formal
# power-series manipulations, not an extra assumption on the true model.
u, v, sk = sp.symbols('u v s_k', positive=True)
Rk_u, Rk_v = sp.symbols('R_k_u R_k_v')  # treat R_k(u), R_k(v) as free symbols

Rk1_u = 1 + u**sk * Rk_u
Rk1_v = 1 + v**sk * Rk_v
Qk = Rk_u * Rk_v
Qk1 = Rk1_u * Rk1_v
xi = u * v

lhs = sp.expand(Qk1 - sp.powsimp(xi**sk * Qk, force=True))
rhs = sp.expand(Rk1_u + Rk1_v - 1)
diff = sp.simplify(sp.powsimp(lhs - rhs, force=True))
print("lhs - rhs simplifies to:", diff)
print("Identity holds exactly:", diff == 0)

print("\n=== Trig identity (eq. 50), |C|^2 - 1 = 8 sin(Q/2) sin((A+Q)/2) cos(A/2) ===")
A, Q = sp.symbols('A Q', real=True)
a = sp.exp(sp.I * A)
q = sp.exp(sp.I * Q)
C = 1 + a * (1 - q)
lhs2 = sp.simplify(sp.expand(C * sp.conjugate(C)) - 1)
rhs2 = 8 * sp.sin(Q/2) * sp.sin((A+Q)/2) * sp.cos(A/2)
diff2 = sp.simplify(sp.trigsimp(sp.expand_trig(lhs2 - rhs2)))
print("lhs - rhs simplifies to:", diff2)

# sympy sometimes needs rewriting via exponentials to fully cancel; do a numeric sweep as a cross-check
import random
maxerr = 0
for _ in range(2000):
    Av = random.uniform(-10, 10)
    Qv = random.uniform(-10, 10)
    Cv = 1 + complex(sp.cos(Av), sp.sin(Av)) * (1 - complex(sp.cos(Qv), sp.sin(Qv)))
    lhs_num = abs(Cv)**2 - 1
    rhs_num = 8*sp.sin(Qv/2)*sp.sin((Av+Qv)/2)*sp.cos(Av/2)
    err = abs(lhs_num - float(rhs_num))
    maxerr = max(maxerr, err)
print("Numeric sweep over 2000 random (A,Q): max |lhs-rhs| =", maxerr)
