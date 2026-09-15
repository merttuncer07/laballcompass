# R197 — Theory Bottleneck Portfolio, Wave 2

Bu wave Pugachev'in conditional-optimal filtering hattı ile
Aizerman–Braverman–Rozonoer potential-function hattını değiştirdi. Birincisi
ciddi ikinci-tur survivor oldu; ikincisinde bounded support mümkün olsa da bizim
özel moment mutation'ımızın edge'i çıkmadı.

## HM-04 — Pugachev conditional moment compiler

### Değiştirilen işlem

Nonlinear conditional expectation'ı her observation'da particle/optimizer ile
yeniden çözmek yerine, model geometrisiyle normalize edilmiş innovation basis'i
üzerinde conditional correction önceden derlendi:

```text
r = (z - h(m)) / sqrt(h'(m)^2 s^2 + R)
x_hat = m + s * beta^T phi(m, s, r)
```

`phi`, raw `(m,s,z)` polinomu değildir: normalized innovation powers, bounded
odd transforms ve state/uncertainty interactions taşır. Katsayı bir OLS pass ve
bir residual-weighted pass ile çıkarıldı; deploy sabit bir matrix-vector işlemidir.

### Birinci test

Her biri 6 seed olan Gaussian, skew-prior/heavy-tail-noise ve bimodal-prior/
mixture-noise sınıfları; ayrıca cubic observation `0.18 -> 0.24` shift'i:

- non-Gaussian home-field'da compiled filter EKF'yi **12/12**, UKF'yi **12/12**
  geçti;
- 18/18 home vakada 2,048-sample importance posterior oracle'ın `%12` RMSE
  bandında kaldı;
- mean RMSE: EKF `0.46043`, UKF `0.37082`, compiled `0.26690`, oracle `0.25491`;
- 35 terimli raw degree-4 `(m,s,z)` polynomial regression'ı **18/18** geçti
  (`0.26690` vs `0.28807`);
- cubic shift'te UKF'yi **18/18** geçti;
- median vectorized deploy maliyeti yaklaşık `0.23 µs/case`;
- robust ikinci pass OLS'yi yalnız 7/18 geçti: ana edge robust weighting değil,
  conditional geometry ile normalize edilen basis'tir.

Bu sonuç tek-adımlı conditional estimation içindir. Gerçek nonlinear filtering
bottleneck'i henüz tamamen kırılmadı; recursion için posterior variance/shape
closure gerekir. R198'in doğrudan hedefi budur.

Status: `SERIOUS_SURVIVOR_CONDITIONAL_MEAN_COMPILED_RECURSIVE_CLOSURE_OPEN`

## HM-09 — Aizerman signed potential condensation

Growing support'u bounded tutmak için aynı işaretli Gaussian potential'lar
birleştirildi. Yeni pseudo-potential signed mass, center of mass ve isotropic
second moment'i korudu. 1,200 support yerine 8/16/32 support; stationary ve
rotating-drift moons; 8 seed ile 48 vaka:

- support reduction `%99.33`;
- full mean accuracy `0.99633`, moment merge `0.99495`;
- moment merge FIFO'yu 41/48 geçti ve 48/48 full modelin üç puan bandında kaldı;
- fakat basit same-sign centroid merge `0.99601` verdi ve moment merge onu yalnız
  4/48 geçti.

Dolayısıyla support growth pratikte bounded hale geliyor, fakat bizim second-
moment mutation'ımız gereksiz karmaşıklık çıktı. Bounded kernel/potential methods
modern prior art bakımından da geniştir. Bu damar yeni bir algebra bulunmadan
yüksek öncelikli değildir.

Status: `BOUNDED_SUPPORT_CAPABILITY_REAL_PROPOSED_MOMENT_EDGE_REJECTED`

## Kaynak sınırı

- Pugachev, Sinitsyn, Shin, nonlinear stochastic systems için conditionally
  optimal real-time filtering survey (1987):
  https://www.mathnet.ru/eng/at4683
- Aizerman, Braverman, Rozonoer, probabilistic recognition and potential
  functions (1964):
  https://www.mathnet.ru/eng/at11723

Compiled/amortized inference, nonlinear basis filters ve budgeted kernels ile
collision audit açıktır. Buradaki hüküm global novelty değil, test edilen
bottleneck'te yeni capability olup olmadığıdır.

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_theory_wave2.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' theory_wave2.py
```

