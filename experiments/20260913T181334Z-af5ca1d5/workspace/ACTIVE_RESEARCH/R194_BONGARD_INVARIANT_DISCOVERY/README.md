# R194 — Bongard Invariant Discovery

## Outcome

`SparseInvariantScout`, pozitif/negatif küçük örneklerden translation/scale
nuisance'ını kaldırıp hangi denklem ailesinin var olduğunu önceden bilmeden
insan-okunur sparse relation çıkarır. Çalışan bir scientific/quality-control
primitive'idir; approximate-vanishing-ideal prior art nedeniyle broad novelty
değildir.

## Sert ikinci tur

- 5 relation family: linear balance, product equality, quadratic energy balance,
  orthogonality ve determinant/proportionality.
- Her vaka: 16 pozitif + 16 negatif eğitim sahnesi, 1,000 test sahnesi.
- Testte eğitimden çok daha geniş translation/scale dönüşümü.
- Noise: `0.005, 0.02, 0.05`; 4 seed; toplam 60 relation vakası.
- Aynı lifted features'ı gören tuned polynomial ridge ve RBF kernel ridge.
- Eşitlik içermeyen 24 half-space/threshold kontrolü.

İlk koşu 53/60 baseline galibiyeti verdi ama non-relation kontrollerinde 12/12
sahte denklem üretti. Bu başarısız sonuç korunarak mekanizma değiştirildi:

1. discovery örnekleri katsayıyı kurar;
2. selection örnekleri 6,175 sparse support arasından seçer;
3. dokunulmamış audit örnekleri claim'i kabul veya reddeder;
4. iki bağımsız positive parçada coefficient direction kararlı olmalıdır;
5. audit-positive median normalized residual `<=0.03` olmalıdır;
6. geçmezse model yanlış denklem vermek yerine abstain eder.

## Final sonuç

| Ölçü | Sonuç |
|---|---:|
| relation vakası | 60 |
| kabul edilen | 41 |
| kabul edilenlerde iki baseline'a birden galibiyet | **41/41** |
| kabul edilenlerde ortalama test accuracy | **0.9790** |
| exact minimal support recovery | **37/41** |
| kabul edilenlerde mean coefficient cosine | **0.9511** |
| non-relation doğru abstention | **24/24** |

Noise breakdown:

| Noise | Kabul | Accepted mean accuracy | Exact support |
|---:|---:|---:|---:|
| 0.005 | 20/20 | 1.000 | 19/20 |
| 0.020 | 17/20 | 0.980 | 16/17 |
| 0.050 | 4/20 | 0.890 | 2/4 |

Yüksek gürültüde coverage düşer; motor yanlış yasa vermek yerine çoğunlukla
susar. Bu ürün için doğru davranıştır fakat genel symbolic discovery iddiasını
sınırlar.

## Kullanım

```python
from invariant_scout import SparseInvariantScout

model = SparseInvariantScout().fit(scene_matrix, labels)
print(model.diagnostics())
# relation örneği: [('d0*d1', 1.0), ('d2*d3', -0.998)]
```

Her satır bir sahne, her sütun aynı tip nesne/ölçüm slotudur. `d_i`, son slota
göre farkın scene RMS ile normalize edilmiş halidir. Bu representation ortak
translation ve pozitif scale'i tam quotient eder.

## Collision audit

- Vanishing Component Analysis yaklaşık sıfırlanan polinomları nonlinear yapı ve
  supervised classification için açıkça kullanır:
  https://proceedings.mlr.press/v28/livni13.html
- Approximate Vanishing Ideal gürültü altında kararlı cebirsel basis çalışır:
  https://doi.org/10.1016/j.jsc.2008.11.010
- AI Feynman symmetry/separability ile symbolic regression yapar:
  https://arxiv.org/abs/1905.11481
- SINDy-PI implicit sparse denklem keşfinde nullspace gürültü sorununu tartışır:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7655768/

Bu nedenle “polinom relation keşfi” yeni değildir. Lab'ın dar katkısı Bongard
tarzı positive-vs-negative concept induction için affine quotient, exhaustive
sparse support, üçlü data split, coefficient stability ve explicit abstention'ın
tek küçük artifact'ta birleşmesidir.

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_invariant_scout.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' r194_benchmark.py
```

Status: `MATERIAL_DISCOVERY_PRIMITIVE_PRIOR_ART_EXISTS_NOT_BREAKTHROUGH`
