# R193 — Markov Omitted-Event Chain Compiler

## Outcome

`OmittedEventChainCompiler` retained event kayıtlarından gerçek tek-adım Markov
dinamiğini optimizer veya EM olmadan derleyen çalışan bir primitive'dir. Sonuç
ticari olarak kullanılabilir bir dar ürün adayıdır; geniş novelty/breakthrough
değildir.

### 72-rejim benchmark

12 seed; sticky, cyclic, sparse ve dense zincirler; 4/7 state; omission
`0.20/0.50/0.75`; 3,000/15,000 gerçek eğitim adımı:

| Ölçü | raw tam inverse vs naive | regularized compiler vs naive |
|---|---:|---:|
| transition matrix error | 65/72 | **66/72** |
| true-step held-out log-loss | 44/72 | **70/72** |
| first-passage relative error | **57/72** | 54/72 |
| stationary law error | 32/72 | 36/72 |
| median matrix-error ratio | 0.353 | 0.368 |
| median log-loss gain | 0.00564 | **0.04491 nat/step** |

Stationary sonuç kasıtlı bir negatif kontroldür: `P` ve geometrik subsample
`Q` aynı stationary dağılımı taşır. De-thinning burada bilgi üretmez.

### Finite-sample düzeltme

Population cebiri tamdır:

```text
Q = (1-r) P (I-rP)^(-1)
P = ((1-r)I+rQ)^(-1) Q
```

Fakat finite sample inverse + simplex projection küçük gerçek geçişleri yanlışlıkla
sıfırlayabilir. İlk ikinci-tur koşusu bu nedenle birkaç ağır log-loss üretti.
Deploy edilen compiler tam inverse'i tek başına kullanmaz:

```text
P_strength = simplex((1-strength) Q_hat + strength P_inverse)
```

`alpha` ve `strength`, yalnız retained train/dev likelihood ile seçilir. En yüksek
strength `0.995` olduğundan gözlenen zincirden küçük bir support floor her zaman
kalır. Bu değişiklik log-loss galibiyetini 54/72'den 70/72'ye çıkardı.

### Omission-rate misspecification

Doğru oran çevresinde `-0.10/-0.05/+0.05/+0.10` sapma ile naive'a karşı log-loss
galibiyetleri sırasıyla `71/72, 71/72, 68/72, 54/72` oldu. Oranı olduğundan fazla
söylemek daha tehlikelidir çünkü aşırı inversion yapar.

### Tanımlanamazlık sınırı

Omission oranı yalnız retained state dizisinden genel olarak öğrenilemez. Bir
population testinde aynı `Q` için 0.00–0.56 arasındaki 29 ayrı assumed rate,
farklı stochastic `P` matrisleriyle maksimum `3.33e-16` forward error verdi.
Bu yüzden ürün sözleşmesi retention rate'i sequence counter, heartbeat audit,
sampling configuration veya ayrı calibration kaynağından ister.

### Hız

12 state population inversion median `86.8 µs`; roundtrip maksimum hata
`1.67e-16`. Bu bir büyük optimizer benchmark'ı değildir, yalnız deployed
algebraic core maliyetidir.

## Ürün yüzeyi

```python
from omitted_chain_compiler import OmittedEventChainCompiler

model = OmittedEventChainCompiler(omission_rate=0.40).fit(retained_state_ids)
true_one_step_transition = model.transition_
print(model.diagnostics())
```

Uygun alanlar: sampling oranı bilinen industrial telemetry, privacy-sampled event
streams, clickstream instrumentation, reliability/fraud state transitions.
Uygun olmayan alanlar: retention mekanizması state'e bağlıysa, rate bilinmiyorsa,
veya süreç birinci-mertebe homogeneous Markov değilse.

## Collision audit

Bu problemin literatürü vardır. Barsotti, De Castro, Espinasse ve Rochet (2014)
random zamanlarda gözlenen zincirlerde `Q`'nun `P`'nin analitik fonksiyonu olduğunu,
gap distribution bilinmediğinde tanımlanamazlığı ve support bilgisiyle bir estimator
kurmayı açıkça çalışmıştır:

https://arxiv.org/abs/1405.0384

Intermittent missing-data için nonlinear-equation ve EM yöntemleri de
karşılaştırılmıştır:

https://doi.org/10.1080/03610910903480800

Dolayısıyla novelty claim yoktur. Lab katkısı: bilinen Bernoulli omission rate'i
için explicit resolvent inverse, held-out strength selection, false-zero support
floor, identifiability contract ve çalışan küçük API'nin tek primitive olmasıdır.

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_omitted_chain_compiler.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' r193_benchmark.py
```

Status: `MATERIAL_NARROW_PRODUCT_PRIOR_ART_EXISTS_NOT_BREAKTHROUGH`
