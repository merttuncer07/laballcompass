# R208 — Döblin'in yarım kalan karşılaştırmasını ayrık zamanda korumak

## 1. Birincil metinden çıkan gerçek mekanizmalar

Döblin'in 1939–1940'ta yazıp sealed envelope'a bıraktığı metin gerçekten
tamamlanmamıştır. İlk sayfada finite zaman aralıklarında sayısı sonlu, zamanla
hareket eden singular points'e izin veren time-inhomogeneous Markov transition
law ile başlar. Metindeki ana mekanizmalar şunlardır:

1. local drift'i çıkar:

\[
M_t=X_t-X_0-\int_0^t a(X_s,s)\,ds;
\]

2. accumulated local variance'i yeni saat yap:

\[
A_t=\int_0^t \sigma^2(X_s,s)\,ds,
\qquad T_\tau=\inf\{t:A_t>\tau\};
\]

3. `M_{T_tau}`yu Brownian motion olarak kullan;
4. `sigma=0` degeneracy'sini bağımsız `epsilon`-Brownian motion ekleyip
   `epsilon -> 0` limitiyle ele al;
5. moving-boundary crossing probabilities, existence by smooth approximation ve
   drift monotonicity/CDF comparison kur.

Manuskript son maddede, `a^- <= a <= a^+` ve ortak `sigma` için üç particle
tanımladıktan hemen sonra kesilir. Yazdığı hedef eşitsizlik CDF yönünde

\[
F_{a^-}(x,y;s,t)\ge F_a(x,y;s,t)\ge F_{a^+}(x,y;s,t)
\]

şeklindedir.

Birincil kaynak:
https://djalil.chafai.net/docs/M2/history-brownian-motion/CRAS%20Doeblin%20-%202000%20-%20French/Doeblin-Partie-II-Equation-de-Kolmogoroff.pdf

## 2. Tarihî açık uç bugün açık mı?

Genel olarak hayır. Sürekli local martingale'in quadratic-variation clock altında
Brownian motion olması 1965 Dambis–Dubins–Schwarz teoremidir. Bir boyutlu SDE'ler
için ordered drift/common diffusion comparison teoremleri de sonraki literatürde
geliştirilmiştir; discontinuous drift ve degenerate diffusion için dahi önemli
sınıflar vardır.

Dolayısıyla R208 “Döblin'in bitiremediği theorem'i ilk kez bitirdi” demez. Daha
dar ama gerçek bir computational boşluk seçer: continuous-time order doğru olsa
bile kullanılan time discretization aynı order certificate'ını koruyor mu?

## 3. Raw Euler neden sertifikayı bozabilir?

Üç SDE aynı Brownian path'i ve aynı state-dependent diffusion `sigma(x)`i
kullansın:

\[
dX_t^j=b_j(X_t^j)dt+\sigma(X_t^j)dW_t,
\qquad b_-\le b_0\le b_+.
\]

Uygun regularity altında exact çözümler

\[
X_t^-\le X_t^0\le X_t^+
\]

olarak couple edilebilir. Raw Euler ise

\[
X_{k+1}^j=X_k^j+h b_j(X_k^j)+\sigma(X_k^j)\sqrt h\,Z_k
\]

kullanır. States ayrıldıktan sonra noise multipliers farklıdır; aynı `Z_k` bile
update map'ini monotone yapmak zorunda değildir. Bu nedenle finite `h`de paths
cross edebilir ve continuous comparison certificate'ı numerical solver içinde
kaybolur.

## 4. Döblin/Lamperti koordinatında order-preserving update

Pozitif smooth ortak diffusion için artan coordinate map

\[
H(x)=\int^x\frac{du}{\sigma(u)},\qquad Y=H(X)
\]

seç. Ito formülü ile

\[
dY_t^j=\beta_j(Y_t^j)dt+dW_t,
\]

ve ortak `sigma` nedeniyle drift order dönüşüm altında korunur. R208 test ailesi

\[
X=\frac{\sinh(cY)}c,
\quad \sigma(X)=\sqrt{1+c^2X^2},
\]

\[
\beta_j(y)=-\kappa\tanh y+o_j,
\quad o_-<o_0<o_+
\]

kullanır. Calendar drift tam olarak

\[
b_j(x)=\sigma(x)\beta_j(H(x))+\frac12c^2x
\]

olur ve pointwise ordered'dır.

Transformed Euler:

\[
Y_{k+1}^j=Y_k^j+h\beta_j(Y_k^j)+\sqrt h Z_k.
\]

## 5. Ayrık karşılaştırma teoremi

**Teorem.** `beta_j(y)=g(y)+o_j`, `o_-<=o_0<=o_+` olsun. Eğer

\[
q_h(y)=y+h g(y)
\]

monotone nondecreasing ise shared-noise transformed Euler her step'te

\[
Y_k^-\le Y_k^0\le Y_k^+
\]

order'ını exact korur. `H^{-1}` artan olduğundan aynı order `X` koordinatında da
korunur.

**İspat.** `y_1<=y_2` için

\[
q_h(y_1)+h o_-\le q_h(y_2)+h o_0
\]

olur. Her iki tarafa aynı `sqrt(h)Z_k` eklemek eşitsizliği değiştirmez. İkinci
çift için aynı argümanı uygula ve induction yap. Artan `H^{-1}` order'ı geri
taşır. ∎

Test ailesinde

\[
q'_h(y)=1-h\kappa\operatorname{sech}^2 y\ge0
\]

olması için `h*kappa<=1` yeterlidir.

## 6. Deney ve hüküm

R208 aynı Brownian increments ile raw ve transformed Euler'i 50,000 path üzerinde
birden fazla step size'ta çalıştırır. Ölçülen şey yalnız RMSE değildir:

- herhangi bir step'te pathwise order violation;
- nonfinite path;
- terminal empirical CDF order violation.

Bu deney scoped theorem'in executable counterexample'ıdır. 50,000 path ile elde
edilen sonuçlarda raw Euler order-failure oranı `h=0.1` için `%6.272`, `h=0.05`
için `%2.664`, `h=0.02` için `%0.080` oldu; `h=0.01` ve `h=0.005` örneklerinde
ihlâl görülmedi. Transformed Euler beş step size'ın tamamında sıfır pathwise
ihlâl ve sıfır nonfinite path verdi. Terminal empirical CDF'ler her iki yöntemde
de doğru stochastic order yönünde kaldı; dolayısıyla ayrım yalnız dağılımsal bir
grafik değil, pathwise coupling sertifikasıdır. Ham yöntemin hatası adım
küçüldükçe kaybolduğu için bu, consistency karşı-örneği değil finite-step
invariant kaybıdır. `R208_RESULT.json` bütün ham sayıları taşır.

## 7. Collision ve açık sınırlar

- quadratic clock: Dambis–Dubins–Schwarz tarafından özümsenmiş;
- continuous comparison: modern 1D SDE comparison theory tarafından özümsenmiş;
- Lamperti numerical schemes ve order-preserving schemes: aktif literatür;
- discontinuous `sigma` için `H'` sıçrar ve generalized Ito–Tanaka/local-time
  correction gerekir; R208 bunu çözmez;
- multidimensional order için scalar monotone coordinate yeterli değildir;
- step condition bozulursa transformed Euler guarantee de biter.

Doğru karar: tarihî kaynak gerçek ve çok güçlüdür; R208 numerical invariantı da
gerçektir, fakat bu turda breakthrough/novel theory bulunmamıştır.

Modern collision izleri:

- Dambis–Dubins–Schwarz tarihî atıf:
  https://www.pnas.org/doi/10.1073/pnas.53.5.913
- Discontinuous drift/degenerate diffusion comparison:
  https://doi.org/10.1016/0304-4149(90)90092-7
- Order-preserving SDE schemes:
  https://doi.org/10.1016/j.apnum.2016.11.008
- Generalized Ito/local-time formulas:
  https://arxiv.org/abs/math/0505195
