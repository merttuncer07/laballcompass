# R198 — Pugachev Recursive Moment + Tail Closure

R197'de tek-adımlı conditional expectation derlenmişti. R198 asıl açık işlemi
hedefledi: bu map'in kendi posterior approximation'ı altında tekrar tekrar
çalışması ve uncertainty state'inin kapanması.

## Kırılan cebir

Önceki tek koordinatlı Gaussian closure:

```text
state = (mean, variance)
interval_90 = mean +/- 1.644854 sqrt(variance)
```

non-Gaussian recursion'da iki ayrı rolü karıştırıyordu. Variance'i coverage için
şişirmek sonraki adımın prior scale'ini de şişirdi ve mean RMSE'yi `0.269 -> 0.356`
bozdu. R198 state'i şu biçimde ayırdı:

```text
dynamic state = (conditional mean, conditional second-moment scale)
tail state    = recursive standardized-residual q_0.90
interval_90   = mean +/- q_0.90 sqrt(variance)
```

Mean ve second moment aynı conditional innovation basis'inden derlenir. Tail
coordinate ise ayrı calibration trajectories üzerinde, testten bağımsız bir pass
ile derlenir. Böylece tail kalibrasyonu recursion dinamiğini değiştirmez.

## Deney

- Gaussian, skew-prior/heavy-tail-noise, bimodal-prior/mixture-noise;
- 5 seed × 3 rejim × home/shift = 30 vaka;
- her vakada 70 bağımsız trajectory × 65 adım;
- shift: transition `0.82 -> 0.90`, observation cubic `0.18 -> 0.24`;
- baselines: EKF, UKF ve doğru process/noise modelini bilen 512-particle filter.

## Sonuç

- Home non-Gaussian vakalarda compiled closure EKF'yi **10/10**, UKF'yi
  **10/10** geçti.
- Home vakaların **15/15**inde particle filter RMSE'sinin `%15` bandında kaldı.
- Shift vakalarında UKF'yi **10/15** geçti; bu 10 galibiyet non-Gaussian
  vakaların tamamıdır.
- Mean home RMSE: compiled `0.26924`, UKF `0.30255`, particle `0.26128`.
- Home 90% interval coverage: **`0.90037`**.
- Median wall-time speedup: **`54.25x`** vs 512-particle filter.

Rejim kırılımı:

| Rejim | Shift | Compiled RMSE | UKF RMSE | Particle RMSE | Compiled coverage90 |
|---|---:|---:|---:|---:|---:|
| Gaussian | hayır | 0.24 | 0.24 | 0.24 | 0.90 |
| Gaussian | evet | 0.22 | 0.22 | 0.22 | 0.88 |
| Mixture | hayır | 0.28 | 0.32 | 0.28 | 0.91 |
| Mixture | evet | 0.28 | 0.31 | 0.27 | 0.90 |
| Skew | hayır | 0.29 | 0.35 | 0.27 | 0.90 |
| Skew | evet | 0.28 | 0.36 | 0.26 | 0.84 |

## Hüküm

Test edilen scalar nonlinear/non-Gaussian sınıfta expensive conditional inference
ve recursive mean closure bottleneck'i kırıldı. İkinci moment ile tail quantile'in
ayrılması, yalnız hızlandırma değil, eski conditional-optimal filter state'ine
yeni bir coordinate ekleyen teori değişikliğidir.

Henüz çözülmeyenler:

- skew dynamics shift altında tail coverage `0.84`e düşüyor;
- çok boyutlu state ve correlated observation yok;
- latent/discrete regime switch yok;
- compiler model ailesi başına offline simulation kullanıyor;
- particle filter yalnız 512 parçacık ve scalar problemde test edildi;
- learned/amortized filters, assumed-density filtering, sigma-point families ve
  modern conditional density estimation ile collision/benchmark açık;
- global novelty veya breakthrough iddiası yok.

Bu, ürün seçimi değil; **ciddi, kapsamı belli bir bottleneck kırılmasıdır**.
Disruptive potansiyel, aynı closure'ın çok boyutlu ve regime-shift altında da
yaşamasına bağlıdır.

## Kaynak

Pugachev, Sinitsyn, Shin (1987), nonlinear stochastic systems için conditionally
optimal real-time filtering:
https://www.mathnet.ru/eng/at4683

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_recursive_closure.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' recursive_closure.py
```

Status: `SCOPED_RECURSIVE_BOTTLENECK_BROKEN_SHIFT_TAIL_AND_MULTIVARIATE_OPEN`
