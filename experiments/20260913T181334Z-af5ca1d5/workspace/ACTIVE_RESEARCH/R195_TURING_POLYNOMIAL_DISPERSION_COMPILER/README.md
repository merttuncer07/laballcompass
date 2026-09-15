# R195 — Turing Polynomial Dispersion Compiler

## Karar

Bu roundda **ciddi, çalışan, collision-audit-open bir teori/mekanizma ilerlemesi**
çıktı: `PolynomialDispersionCompiler`. Bu bir ürün seçimi değildir. Turing tipi
mode-selection problemindeki continuous-search, incumbent-lock ve katsayı
belirsizliği darboğazlarının belirli bir sınıfta kırıldığına dair deneysel adaydır.

R179 yalnız canonical Swift–Hohenberg adjacent crossing'i biliyordu. R195 bunu
her even polynomial dispersion için target-mode inverse design, exact candidate
enumeration, coefficient-box certificate ve iki-rate micro-probe control
calibration'a yükseltir.

Global academic novelty henüz kanıtlanmadı. Gerçek materyal cihazı/deneyi de henüz
yoktur. Buna rağmen R193/R194'ten farklı olarak targeted search'te aynı dar
compiler bileşiminin doğrudan çakışması bulunmadı ve mekanizma geniş bir modern
optimizer'ı taklit etmek yerine sonlu bir cebirsel çözüm üretiyor.

## Cebir

Girdi dispersion:

```text
g(k) = c0 + c1 k^2 + c2 k^4 + ... + cp k^(2p)
k_n = boundary_factor * n / L
q   = (boundary_factor/L)^2
```

Dolayısıyla her discrete mode rate'i `q` içinde polinomdur:

```text
g_n(q) = sum_p c_p n^(2p) q^p
```

Target'ın bütün rakiplere karşı margin'i:

```text
M(q) = min_r [g_target(q) - g_r(q)]
```

Bir compact interval'da bu lower envelope'in maksimumu yalnız şu sonlu adaylarda
olabilir:

1. interval uçları;
2. target/rival crossing kökleri;
3. her margin polinomunun derivative kökleri;
4. iki rakibin aktif-rival olarak yer değiştirdiği kökler.

Compiler bu kökleri çıkarır ve yalnız onları değerlendirir. Dense grid veya
gradient optimizer taşımaz.

Seçilen yerde additive control için:

```text
u_quench = -(g_target + max_rival g_r)/2
```

olduğunda target ve en güçlü rakip eşit büyüklükte zıt işaretli olur.

## 144-case exact-design benchmark

- 12 seed;
- Swift–Hohenberg, thin-film quartic ve sixth-order material dispersion;
- target mode `3,5,8,12`;
- rakip mode'lar `1..16`;
- karşılaştırma: her vakada 100,001-point dense oracle.

| Ölçü | Sonuç |
|---|---:|
| algebraic design oracle'dan geri kalmadı | **144/144** |
| maksimum pozitif relative margin regret | **0.0** |
| bütün point quenches sign-separated | **144/144** |
| median candidate sayısı | **73.5** |
| median compile süresi | **6.82 ms** |

Dense sonuç “oracle” yalnız sonlu grid olduğu için algebraic aday bazen ondan
az miktarda daha iyi çıkar; regret negatifse sıfıra kırpılmıştır.

## Nonlinear doğrulama

İlk generic amplitude ODE testinde compiled quench 90/90 kazandı; bu fazla kolay
bir shell olduğu için son karar ona dayanmaz.

Ardından aynı polynomial Fourier symbol ve local cubic saturation kullanan 1D
pseudospectral PDE çalıştırıldı. Normal işletimde en güçlü rakibin rate'i compiled
modal margin'e göre değiştirildi:

| Normal rival rate / margin | Normal target | Incumbent lock | Quench target | Settle retention |
|---:|---:|---:|---:|---:|
| 0.2 | 30/30 | 0/30 | 30/30 | 30/30 |
| 0.5 | 30/30 | 0/30 | 30/30 | 30/30 |
| 1.0 | 28/30 | 2/30 | 30/30 | 30/30 |
| 2.0 | 0/30 | 30/30 | 30/30 | 30/30 |
| 3.0 | 0/30 | 30/30 | 30/30 | 30/30 |
| 5.0 | 0/30 | 30/30 | 30/30 | 30/30 |

Sonuç sınırı nettir: zayıf lock rejiminde normal linear advantage zaten yeterlidir;
quench'in edge'i güçlü incumbent saturation/hysteresis rejimidir.

## Belirsizlik ve ikinci cebir değişikliği

Point-estimate stress: 20 seed × 3 dispersion × 3 target × 6 coefficient-noise
seviyesi = 1,080 vaka.

Point quench kırılgandı:

| Katsayı noise | True sign separation |
|---:|---:|
| 0% | 180/180 |
| 1% | 140/180 |
| 3% | 69/180 |
| 5% | 56/180 |

İlk robust çözüm absolute target lower-bound ile rival upper-bound'u ayırdı. Tam
garantiliydi fakat %1 noise'ta yalnız 36/180 pencere kabul etti; fazla
muhafazakârdı.

Son mutasyon ortak offset'i modelden tahmin etmeye çalışmaz:

1. Aynı coefficient vector altındaki `target-rival` farkının interval minimumu
   term işaretine göre exact polinom yapılır.
2. Bu robust difference lower envelope'i exact derlenir.
3. Seçilen geometride target ve worst-rival growth rate kısa bir micro-probe ile
   ölçülür.
4. Quench bu iki ölçümün orta noktasından kurulur.

Sonuç:

| Katsayı noise | Shape-window kabul | Kabul edilenlerde true dominance + probe sign separation |
|---:|---:|---:|
| 0% | 180/180 | 180/180 |
| 1% | **178/180** | **178/178** |
| 3% | 53/180 | **53/53** |
| 5%+ | 0 | claim yok |

Interval gerçek katsayıyı kapsadığında kabul edilen hiçbir vaka certificate'i
bozmadı. Symmetric micro-probe hata bütçesi certificate margin'inin yarısından
küçük olmalıdır; benchmark her rate ölçümünde margin'in %40'ına kadar hata kullandı.

## Mekanizma sözleşmesi

**Girdi**

- fitted even-polynomial dispersion coefficients;
- tercihen coefficient confidence intervals/bootstrap box;
- allowed discrete mode seti ve target;
- fiziksel geometry'den türeyen `q` aralığı;
- robust-shape yolunda seçilen geometride iki kısa modal growth-rate probe.

**Çıktı**

- target mode için geometry/length;
- certified modal separation margin;
- en tehlikeli rival;
- point veya interval-certified additive quench;
- izin verilen micro-probe error budget;
- güvenli pencere yoksa açık abstention.

**Şimdilik kapsamaz**

- non-polynomial/complex dispersion;
- 2D degenerate eigenspaces ve orientation selection;
- mode-dependent control operators;
- time-varying coefficient drift;
- gerçek cihaz actuator limits/ramp dynamics;
- experimental success claim.

## CLI

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' mode_design_cli.py `
  --coefficients '0,1.5,-0.9' `
  --target 5 `
  --modes '1,2,3,4,5,6,7,8,9' `
  --q-bounds '0.003,0.2'
```

Interval + micro-probe seçenekleri için `--lower`, `--upper`,
`--observed-target-rate`, `--observed-rival-rate` eklenir.

## Collision boundary

Growing-domain mode selection, reaction–diffusion control, directional quenching,
thin-film dispersion design ve generic polynomial root/envelope optimization ayrı
ayrı bilinen alanlardır. Hızlı targeted search şu dar bileşim için doğrudan eşleşme
bulmadı:

```text
even-polynomial dispersion
+ discrete finite-domain target mode
+ exact lower-envelope root candidate compiler
+ coefficient-box robust difference certificate
+ two-rate micro-probe calibrated sign-separating quench
```

Bu yalnız `COLLISION_AUDIT_OPEN` demektir; priority/novelty kanıtı değildir.

Başlangıç/komşu kaynaklar:

- Turing morphogenesis archive:
  https://turingarchive.kings.cam.ac.uk/morphogenesis
- growing-domain Turing mode selection:
  https://arxiv.org/abs/1912.03557
- thin-film instability dispersion and selected mode:
  https://doi.org/10.1002/polb.20631
- pattern control by spatial spectrum/Turing instability:
  https://doi.org/10.1016/j.automatica.2015.03.009
- directional quenching in Swift–Hohenberg:
  https://doi.org/10.1112/jlms.12122

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_polynomial_dispersion_compiler.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' r195_benchmark.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' pde_validation.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' uncertainty_validation.py
```

Status: `BOTTLENECK_BROKEN_IN_TESTED_CLASS_COLLISION_AUDIT_OPEN_PHYSICAL_EXPERIMENT_REQUIRED`
