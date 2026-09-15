# R200 — Pitrat Failure Schemas + Preisach Frontier Algebra

## HM-08 — Pitrat: failure trace'ten quotient metaknowledge'e

### Neden ilk iki mutasyon çalışmadı?

Yalnız leaf conflict kaydetmek ve exact partial assignment nogood taşımak, farklı
sorgular aynı yapıya sahip olsa bile aynı assignment'a nadiren döndüğü için arama
ağacını küçültmedi:

```text
plain ~= fresh core ~= shared exact core ~= shared full-state nogood
```

### Cebir terfisi

1. Her branch failure explanation'ı parent variable üzerinden resolve edildi.
2. Graph'ta aynı adjacency signature'a sahip vertex'ler otomatik structural
   equivalence sınıfına alındı.
3. İki eşdeğer vertex'in farklı renk almasının çözümsüzlüğünü kanıtlayan resolved
   core, tekil vertex kimliklerinden quotient edilerek sınıf-level failure schema'ya
   çevrildi.
4. Sonraki sorguda aynı schema farklı vertex ve color isimlerinde uygulanabildi.

4/5/6-part complete multipartite aileleri, 6 seed, toplam 18 vaka ve her vakada
36 farklı precoloring sorgusu:

- exact shared core plain solver'ı yalnız 3/18 geçti;
- quotient failure schema exact core'u **18/18** geçti;
- mean node: plain `882.0`, exact core `880.72`, quotient schema `542.33`;
- reduction yaklaşık **%38.5**;
- satisfiable/unsatisfiable hükümleri bütün solver'larda aynı kaldı;
- hiçbir node cap'e çarpmadı.

Bu sonuç, “başarısızlığı kaydet” fikrinin yetersiz olduğunu gösteriyor. Taşınabilir
metaknowledge için failure explanation'ın problem simetrileri altında quotient
edilmesi gerekiyor.

Sınır: mevcut schema formu—aynı structural class'ta farklı değerler—kodda
tanımlıdır; sistem schema dilini sıfırdan keşfetmiyor. Conflict learning,
symmetry breaking, nogood generalization ve lifted constraint learning ile
collision audit açıktır.

Status: `SCOPED_FAILURE_SCHEMA_TRANSFER_WORKS_SCHEMA_LANGUAGE_NOT_DISCOVERED`

## HM-11 — Preisach: dense relay state'ten frontier + factor density'ye

Scalar Preisach gridinde relay'ler `(alpha,beta)`, `alpha > beta` üçgeninde yaşar.
Sabit bir `beta` satırında on-state relay'ler her zaman alpha yönünde bir prefix
oluşturur. Dolayısıyla bütün `O(n^2)` Boolean state yerine yalnız frontier tutuldu:

```text
frontier[beta] = o satırda on kalan en büyük alpha
```

Input yükselirken ilgili prefix uzar; düşerken geçilen beta satırları kapanır.
Density de masked low-rank ise:

```text
w(alpha,beta) = sum_r U(alpha,r) V(beta,r),  alpha > beta
```

output, `U` prefix sums ve frontier üzerinden `O(nr)` hesaplanır; dense relay
matrix veya dense state gerekmez.

8 seed × 32/64/128 levels = 24 vaka, her birinde 900-adımlı random reversal path:

- reconstructed relay state dense simulator ile **24/24 exact**;
- maksimum output farkı `1.15e-14`;
- 128 levels, rank 4'te state+density temsil küçülmesi **14.11×**.

Dense random density stress'i sınırı gösterdi: rank-4 approximation relative
error ortalama `0.81654`. Yani state frontier'i scalar input için exact olsa da
density compression yalnız gerçekten low-rank density sınıfında exact.

Bu iki ayrı bottleneck hükmüdür:

- scalar Preisach **state memory** `O(n^2) -> O(n)` exact;
- low-rank masked density ile **weight/output representation** `O(n^2) -> O(nr)` exact;
- arbitrary dense density hâlâ açık.

Modern staircase/Everett algorithms ve low-rank hysteresis approximation ile
collision audit gereklidir; novelty iddiası yoktur.

Status: `SCALAR_STATE_EXACTLY_COMPRESSED_LOWRANK_DENSITY_SCOPED_DENSE_OPEN`

## Kaynaklar

- Pitrat, *Artificial Beings: The Conscience of a Conscious Machine* (2009),
  metaknowledge/self-observation hattı:
  https://doi.org/10.1002/9780470611791
- Preisach, *Über die magnetische Nachwirkung* (1935):
  https://doi.org/10.1007/BF01349418

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_pitrat_preisach.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' pitrat_preisach.py
```

