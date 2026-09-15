# R196 — Theory Bottleneck Portfolio, Wave 1

Bu roundun hedefi bir ürünü seçmek değil, üç tarihî teorinin takıldığı işlemi
değiştirip yeni kabiliyet kalıp kalmadığını ölçmektir. Pozitif bir home-field
sonucu global teori çözümü veya novelty sayılmaz. Ham vakalar `R196_RESULT.json`,
çalışan deney `portfolio_wave1.py` içindedir.

## Kısa hüküm

| Damar | Eski bottleneck | Yapısal değişiklik | Hüküm |
|---|---|---|---|
| Steinbuch Lernmatrix | Tek hit ile kalıcı hücre doygunluğu | Her hücreyi 2-bit yerel kanıta terfi; signed sınıf-dışı kanıt ablation'ı | Doygunluk kırıldı; signed kısmın eşit-bellek üstünlüğü kanıtlanmadı |
| Choquet capacity | Genel kapasitede `2^d-2` serbest değer | Sparse 2-additive Möbius support keşfi + closed-form exact monotonicity projection | Üstel bottleneck yalnız sparse 2-additive sınıfta kırıldı |
| Volterra hereditary series | İkinci mertebede `O(m^2)` kernel ve segmentler arası sahte hafıza | Rank-separable quadratic form + bilinen değişim sınırında hafıza reset | Deploy bottleneck'i düşük-rank sınıfta kırıldı; doğrudan faktör eğitimi açık |

## HM-07 — Steinbuch: latch'ten küçük kanıt hücresine

12 sınıf, 192 bit, üç load ve iki query-noise rejiminde 48 vaka çalıştı.

- Yüksek load'da binary latch matrisinin hücrelerinin `%82.48`i doldu ve accuracy
  `0.4533`e düştü.
- Signed ternary hücre `0.9992`, float centroid `0.9997`, aynı 2-bit unsigned
  count baseline'ı `0.9996` accuracy verdi.
- Signed ternary binary matrisi 40/48 vakada geçti; fakat aynı bellekli unsigned
  baseline'ı yalnız 4/48 vakada geçti.

Dolayısıyla **doygunluk sorunu çözülüyor**, ama güçlü fikir “signed evidence” diye
şişirilemez. Asıl terfi 1-bit irreversible memory'den küçük, yeniden ölçülebilir
evidence state'ine geçiştir. Bu şimdilik faydalı bir teori düzeltmesi; breakthrough
değildir.

## HM-10 — Choquet: üstel capacity'den sparse interaction cebirine

2-additive capacity şu şekilde yazıldı:

```text
C_mu(x) = sum_i a_i x_i + sum_(i,j in E) b_ij min(x_i, x_j)
```

Monotonicity'nin üstel subset taraması gerektirmeyen exact alt sınırı:

```text
min_S Delta_i mu(S) = a_i + sum_(j: b_ij < 0) b_ij >= 0
```

Bu eşitsizlik projection ve certificate olarak kullanıldı. 12/20 boyut, 80/200
örnek, 8 seed ile 32 sparse vakada:

- sparse model additive modeli 27/32;
- monotone full-pair modeli 32/32;
- monotonicity'siz raw full-pair modeli 32/32 geçti;
- 32/32 exact monotonicity certificate verdi;
- mean RMSE: additive `0.01644`, raw full pair `0.02150`, sparse `0.00688`;
- bulunan 7 interaction'ın ortalama `4.53`ü gerçek support'taydı.

Fakat dense-interaction stress'te full model 6/6 kazandı (`0.00145` vs `0.06574`).
Yani genel Choquet kapasitesinin üstel problemi çözülmedi; **sparse 2-additive
capacity sınıfı için** `O(d+s)` temsile ve exact certificate'e indirildi. Bir
sonraki ciddi adım support'un gerçekten sparse olup olmadığını veriden sertifika
eden bir testtir; aksi halde bu yöntem abstain etmelidir.

## HM-12 — Volterra: yoğun hereditary kernelden separable memory'ye

İkinci mertebe kernel:

```text
z^T H z  ->  sum_r lambda_r (v_r^T z)^2
```

olarak terfi edildi. Bilinen segment/change sınırlarında lag state sıfırlandı;
önceki bağımsız rejimden sahte hafıza taşınmadı. 16 memory, rank 3, iki train
load'u ve 8 seed ile 16 vakada:

- separable model dense Volterra'nın %10 bandında 16/16 kaldı ve ortalamada daha
  düşük RMSE verdi (`0.01826` vs `0.02197`);
- linear modeli 16/16 geçti (`0.56187` mean RMSE);
- boundary-aware sürüm no-reset sürümü 16/16 geçti (`0.01826` vs `0.30429`);
- deploy parametreleri 152'den 67'ye, `%55.9` azaldı.

Dense-rank stress'te sonuç tersine döndü: dense model 6/6 kazandı (`0.01333` vs
`0.46308`). Ayrıca mevcut deney önce dense `H` fit edip sonra rank-truncate ediyor.
Bu nedenle **deploy/kernel representation bottleneck'i** low-rank ve boundary
marker bulunan sınıfta kırıldı; training bottleneck'i ancak faktörleri dense
matris kurmadan doğrudan öğrenirsek kırılmış olacak.

## Disruption okuması — şimdilik yalnız kabiliyet

- Steinbuch hattı disruption adayı değil; basit ama sağlam bir düzeltme.
- Choquet hattındaki ilginç kabiliyet, az sayıda signed interaction ile karar
  fonksiyonunu hem compact hem exact monotone tutabilmek. Önce sparsity-abstention
  çözülmeli.
- Volterra hattındaki ilginç kabiliyet, nonlinear uzun hafızayı dense kernel
  taşımadan çalıştırmak. Doğrudan online factor learning çözülürse gerçek bir
  teori ilerlemesine dönüşebilir.

Bu yorumlar ürün seçimi değildir. Bir sonraki wave teorik açık işlemleri hedefler:
Pugachev'de conditional expectation/closure, Aizerman'da support growth ve
Glushkov'da composition state explosion.

## Kaynak sınırı

- Steinbuch, *Die Lernmatrix*, Kybernetik 1 (1961), 36–45:
  https://bibbase.org/network/publication/steinbuch-dielernmatrix-1961
- Choquet, *Theory of capacities* (1954):
  https://www.numdam.org/articles/10.5802/aif.53/
- Volterra'nın integral-equation/functional hattındaki birincil kitaplarından
  *The theory of permutable functions* (1915) taraması:
  https://commons.wikimedia.org/wiki/File:The_theory_of_permutable_functions_(IA_theoryofpermutab00voltrich).pdf

Low-rank Volterra ve sparse/k-additive Choquet modern prior-art alanlarıdır.
Buradaki deneyler novelty değil, bottleneck hükmü verir; collision audit açıktır.

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_portfolio_wave1.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' portfolio_wave1.py
```

Status: `ONE_OPERATIONAL_FIX_TWO_SCOPED_THEORY_ADVANCES_NO_BREAKTHROUGH_CLAIM`
