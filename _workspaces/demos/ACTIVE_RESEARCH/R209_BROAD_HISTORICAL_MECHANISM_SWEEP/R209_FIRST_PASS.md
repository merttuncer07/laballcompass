# R209 — Geniş Tarihî Mekanizma Taraması, İlk Tur

**Tarih:** 31 Ağustos 2026  
**Kapsam:** On yeni/park edilmiş tarihî hattın eşit bütçeli ilk ayrıştırması  
**İddia düzeyi:** Kaynak-doğrulanmış çekirdek + scoped cebirsel tanık veya
karşı-örnek. Global yenilik, ürün veya breakthrough iddiası yoktur.

## 1. Protokol

Her adayda şu sıra kullanıldı:

1. Tarihî mekanizmayı isimden ve biyografiden ayır.
2. Bugün hâlâ açık olabilecek tek işlemi yaz.
3. Korunacak invariantı seç.
4. Algoritma yerine mümkünse cebri, koordinatı veya gözlem düzenini değiştir.
5. Bir theorem witness veya ucuz kill test çalıştır.
6. Modern literatür aynı işlemi zaten taşıyorsa sonucu dürüstçe park et.

Bu round yeni bir ürün aramaz; tek bir adaya uzun compute harcamaz.

## 2. Toplu karar

| Sıra | Hat | İlk-tur hükmü | Karar |
|---:|---|---|---|
| 1 | Matthes–Kerstan–Mecke | Controlled thinning altında bounded cluster intensities exact tanımlanıyor; yüksek order ill-conditioned | **İkinci tura aday** |
| 2 | Zhuravlev | Affine/XOR corrector üstel ensemble aramasını GF(2) eliminasyonuna indiriyor ve erişilemez hedefte abstain ediyor | **Scoped devam** |
| 3 | Setun | Ortalama carry run belirgin biçimde kısalıyor; worst-case ve hardware maliyeti çözülmüyor | **Mekanizma tutuldu** |
| 4 | Ivakhnenko | Polynomial evaluation algebra finite sample üzerinde rank `<=n` quotient'a çöküyor; off-sample eşdeğerlik yok | **Teori tohumu, collision yüksek** |
| 5 | Yakubovich | Üç quadratic constraint'te scalar multiplier exactness açık 1 birim gap ile ölüyor | **Yeni multiplier dili olmadan ilerleme yok** |
| 6 | Diliberto–Straus | Leveling, finite grid cycle optimum'una ulaşıyor; rectangle witness bu örnekte exact | **Temiz yeniden ifade, yeni edge yok** |
| 7 | Kaczmarz | Inconsistent sistemde sıra bağımlılığı gerçek; simetrik ortalama azaltıyor fakat LS gap'ini kapatmıyor | **Modern alan doygun** |
| 8 | Lavrentiev | İki-parametre extrapolation bias'ı azaltıp noise'u büyütüyor | **Bilinen trade-off; park** |
| 9 | Ville | Capital mixture time-uniform bound'u koruyor; max-selection bozuluyor | **Modern e-process alanıyla çakışıyor** |
| 10 | Delsarte | Exact invertible finite transmutation similarity sınırına çarpıyor | **Universal mutasyon öldü** |

## 3. Zhuravlev — yanlış algoritmalar üzerinde affine corrector

### Tarihî çekirdek

Zhuravlev'in algebraic correction programı bir base recognition algoritmaları
ailesini çalıştırıp son kararı bir corrector ile sentezler. Isaev–Zhuravlev 1979
makalesi verilen control sample üzerinde hata yapmayan bir recognition
algoritması sentezlemeyi açıkça hedefler.

Birincil kayıtlar:

- https://www.mathnet.ru/rus/dan41348
- https://www.mathnet.ru/eng/zvmmf5406

### Mutasyon

Base algoritma `j`'nin control sample error vector'ünü
`e_j in GF(2)^n` yaz. XOR/affine corrector için hedef hata `t` ise:

```text
E w = t  (mod 2),      E=[e_1 ... e_m].
```

`2^m` altküme aramak yerine row reduction yapılır. Sistem çözümsüzse corrector
uydurmaz; erişilemez hedef certificate'iyle abstain eder. Korunan invariant
control sample üzerindeki tam error syndrome'dur.

### Sonuç ve sınır

- 28 control satırı, 18 base algoritma ve 262,144 olası altkümede planted
  corrector exact bulundu.
- Başka bir örnekte target'ın column space dışında olduğu exact belgelendi.
- Sonuç yalnız affine/XOR closure içindir. Majority, threshold veya nonlinear
  aggregation'a taşınmaz.
- Linear stacking, coding ve ensemble correction ile collision riski yüksektir.

**Hüküm:** Üstel enumeration darboğazı gerçekten kırıldı; fakat teorik tavanı
şimdilik dar. Non-affine corrector'a geçiş ancak yeni bir tractable quotient
bulunursa değerlidir.

## 4. Ivakhnenko — empirical polynomial quotient

### Tarihî çekirdek

Ivakhnenko'nun GMDH hattı küçük quadratic partial descriptions üretir, checking
set üzerinde seçer ve seçilen değişkenleri bir sonraki layer'a taşır. Orijinal
metin kombinasyon ve polynomial complexity'nin layer'lar boyunca büyüdüğünü
açıkça gösterir.

Birincil metin:

- https://www.gmdh.net/articles/history/polynomial.pdf

### Mutasyon

Sample `X={x_1,...,x_n}` ve polynomial language `P_D` olsun. Evaluation map:

```text
ev_X : P_D -> R^n,      f |-> (f(x_1),...,f(x_n)).
```

Kernel, sample üzerinde vanishing polynomial'lerden oluşur. Bu nedenle gerekli
temsil bütün symbolic polynomial ağacı değil quotient'tır:

```text
P_D / ker(ev_X),       dim <= n.
```

### Sonuç ve sınır

İki değişken ve total degree 32 altında 561 monomial, 40 sample üzerinde rank
40'a çöktü; on-sample projection error `2.7e-15`, temsil oranı `14.0x` oldu.
Fakat quotient yalnız sample prediction'larını korur; iki polynomial yeni bir
noktada tamamen farklı olabilir. Vanishing-ideal ve polynomial-kernel
literatürüyle güçlü çakışma vardır.

**Hüküm:** GMDH symbolic degree explosion için doğru koordinat olabilir; fakat
genelleme invariantı bulunmadan breakthrough değildir.

## 5. Ville — selection-safe capital mixture

Ville'in 1939 tezi selection rules ve martingale/betting bağlantısının temel
kaynağıdır:

- https://numdam.org/item/THESE_1939__218__1_0/

Her biri nonnegative test martingale olan `M_t^(k)` ve önceden belirlenen
`pi_k>=0`, `sum pi_k=1` için:

```text
M_t = sum_k pi_k M_t^(k)
```

yine test martingale'dir. Buna karşılık veriye bakıp `max_k M_t^(k)` seçmek aynı
normalizasyonu taşımaz. 25,000 null path ve 200 adımda `alpha=.05` için mixture
crossing `%3.996`, normalize edilmemiş component maximum crossing `%12.304`
çıktı.

Modern composite e-process çalışması bu hattı doğrudan genişletmektedir:

- https://doi.org/10.1214/23-EJP1019

**Hüküm:** Mekanizma doğru ve faydalı, fakat hidden gold değildir; modern alan
tarafından aktif biçimde taşınıyor.

## 6. Yakubovich — multi-constraint scalar S-procedure kill

Tarihî kaynak: V. A. Yakubovich, “S-procedure in nonlinear control theory”,
Vestnik Leningrad University, 1971, no. 1, pp. 62–77. Modern survey:

- https://epubs.siam.org/doi/pdf/10.1137/S003614450444614X

Triangle Laplacian'ı `L` ve box constraints `1-x_i^2>=0`, `i=1,2,3` olsun.
Vertex enumeration:

```text
max_{|x_i|<=1} x^T L x = 8.
```

Scalar S-certificate `diag(lambda)-L >= 0` ister. Problem permutation invariant
olduğu için feasible multiplier'ları ortalamak symmetric optimum verir. Bu
durumda `lambda >= lambda_max(L)=3`, dolayısıyla:

```text
sum_i lambda_i >= 9 > 8.
```

Exact implication vardır fakat scalar multi-S certificate'te 1 birim gap
kalır.

**Hüküm:** “Daha çok scalar multiplier ekle” yönü öldü. Yeni aday ancak cycle,
matrix-valued veya problem-graph'ına bağlı certificate dilinin complexity'sini
scalar dilden daha iyi sınırlar ise açılmalı.

## 7. Setun — balanced-ternary carry locality

Setun `{-1,0,+1}` balanced code kullanan gerçek çalışan ternary bilgisayardı:

- https://inria.hal.science/hal-01568401
- https://ternarycomp.cs.msu.ru/

Digit toplamı `s=a_i+b_i+c_i` için balanced remainder ve carry:

```text
r_i in {-1,0,1},  r_i = s (mod 3),     c_{i+1}=(s-r_i)/3.
```

60,000 adet 64-digit rastgele toplamada binary nonzero carry run ortalaması
`3.822`, balanced ternary `1.490`; oran `2.566x`. Active carry fraction
`0.493 -> 0.250`. Buna karşın iki sistemin de worst-case carry chain'i word
length ile lineerdir. Modern signed-digit carry literatürü aynı olguyu inceler.

**Hüküm:** Gerçek mekanizma, fakat tek başına teori kırılması değil. Değer ancak
carry locality'nin hata toleransı veya interval arithmetic ile yeni bir
invariant oluşturması halinde artar.

## 8. Matthes–Kerstan–Mecke — controlled-thinning void tomography

### Tarihî çekirdek

GDR point-process okulunun temel monografisi infinitely divisible point
process'leri cluster/canonical-measure perspektifinden sistematikleştirir:

- https://doi.org/10.1515/9783112737835

Independent thinning için probability generating functional dönüşümü:

```text
G_p[h] = G[1-p+ph].
```

Bu okul tarihsel olarak GDR içinde gelişmiştir; mevcut kanıt siyasi baskı veya
bilinçli gömülme iddiası kurmaya yetmez.

### Mutasyon: yalnız void gözleminden bounded cluster spectrum

Bir observation window içindeki cluster arrivals Poisson ve cluster size
`k in {1,...,K}` için intensity `mu_k` olsun. Retention `p` sonrası void
olasılığı:

```text
v(p)=P(N_p=0)
    = exp{-sum_{k=1}^K mu_k [1-(1-p)^k]}.
```

Dolayısıyla:

```text
-log v(p_i) = sum_k A_ik mu_k,
A_ik = 1-(1-p_i)^k.
```

Distinct `K` adet uygun `p_i` ile bu bir linear inverse problem'dir. Korunan
invariant log-PGFL/canonical cluster intensity'dir; individual cluster labels
gerekmez.

### Sonuç ve failure boundary

- `K=3,4,6,8` için noiseless recovery max absolute error sırasıyla yaklaşık
  `8e-16, 9e-15, 3e-13, 2e-12` oldu.
- Aynı matrix condition number'ları `174, 1.3e3, 6.5e4, 2.8e6` oldu.
- `K=4`, 250,000 window'luk binomial void observation'da relative L2 error
  `%16.6` kaldı.

Yani tanımlanabilirlik exact; istatistiksel problem yüksek order'da kırılgan.
Compound-Poisson decompounding ve thinning/PGFL işlemleri aktiftir, fakat bu
spesifik **controlled-retention + only-void + finite cluster spectrum**
formülasyonu için doğrudan collision henüz bulunmadı. Bu yokluk novelty kanıtı
değildir.

**Hüküm:** R209'un en güçlü ikinci-tur adayı. Sonraki doğru soru daha çok data
koşmak değil; `A` matrisini orthogonal/factorial-cumulant koordinata geçirerek
conditioning'i düşürürken `mu_k>=0` ve exact identifiability'yi koruyup
koruyamayacağımızdır.

## 9. Diliberto–Straus — leveling'den cycle feasibility'ye

Orijinal RAND problemi `z(x,y)` fonksiyonunu `g(x)+h(y)` ile uniform normda
yaklaştırır. Diliberto–Straus, alternating leveling ve permissible polygonal
line invariant'larını kurmuştur:

- https://msp.org/pjm/1951/1-2/pjm-v1-n2-p04-s.pdf

Finite matrix için `|F_ij-g_i-h_j|<=t`, `a_i=g_i`, `b_j=-h_j` ile iki difference
constraint'e dönüşür:

```text
a_i-b_j <= F_ij+t,
b_j-a_i <= -F_ij+t.
```

Feasibility, associated bipartite directed graph'ta negative cycle olmamasına
eşdeğerdir. Yediye sekiz gridde cycle optimum `1.8278246963`; tarihî leveling
dört iterasyonda aynı değere ulaştı. Bu örnekte rectangle alternating witness
de aynı bound'u verdi.

**Hüküm:** Güzel bir graph/certificate yeniden ifadesi, fakat tarihî teoremin
ötesinde yeni capability göstermedi.

## 10. Kaczmarz — inconsistent row-order boundary

1937 row projection kuralı normalize edilmiş `a_i` için:

```text
x <- x + (b_i-a_i^T x) a_i / ||a_i||^2.
```

Kaynak:

- https://faculty.sites.iastate.edu/esweber/files/inline-files/kaczmarz_english_translation_1937.pdf

Inconsistent 70x12 sistemde forward/reverse cyclic limit'lerin arası `0.670`;
residual'lar `4.227/4.255`, symmetric endpoint average `3.460`, least squares
`2.986` oldu. Sıra problemi gerçek, fakat extended, randomized ve block
Kaczmarz literatürü zaten geniştir.

**Hüküm:** Basit simetrizasyon gap'i azaltıyor ama çözmüyor; yeni teori yok.

## 11. Lavrentiev — bias-cancelling extrapolation

Monotone/SPD operator için standard regularized çözüm:

```text
x_alpha = (A+alpha I)^(-1)y.
```

Resolvent expansion'daki first-order bias iki scale ile iptal edilir:

```text
x_ext = 2 x_alpha - x_{2 alpha}.
```

Testte noiseless error `0.202 -> 0.164`, noisy error `0.354 -> 0.445` oldu.
Yani bias azalırken noise amplification arttı. Iterated/extrapolated
Lavrentiev regularization aktif literatürdür:

- https://arxiv.org/abs/1506.01803

**Hüküm:** Beklenen trade-off doğrulandı; hidden gold yok.

## 12. Delsarte — exact intertwiner spectral boundary

Delsarte transmutation'ın finite-dimensional çekirdeği:

```text
Q B = B P,
(I tensor Q - P^T tensor I) vec(B)=0.
```

Kaynak izi ve operator tanımı:

- https://api.pageplace.de/preview/DT0400.9780080871806_A23529104/preview-9780080871806_A23529104.pdf

`Q=SPS^{-1}` olduğunda invertible `B=S` residual'ı `3.3e-15`; disjoint spectra
durumunda intertwiner nullity sıfır çıktı. Exact invertible finite transmuter
ancak operators similar ise vardır. Noninvertible map yalnız ortak spectral
blocks taşıyabilir.

**Hüküm:** “Arbitrary operator'ları exact transmute eden learned B” yönü
cebirsel olarak öldü. Approximate/nonlinear transmutation başka problemdir ve
bu roundun sonucu değildir.

## 13. Sonraki doğru hareket

R210 bütün on adayı büyütmemelidir. Yalnız iki scoped soru hak kazandı:

1. **GDR thinning tomography:** bounded cluster spectrum inverse matrix'inin
   conditioning'ini basis/design değişikliğiyle düşürmek; nonnegativity,
   identifiability ve only-void observation'ı korumak; doğrudan prior-art
   collision taraması yapmak.
2. **Zhuravlev corrector:** affine syndrome compiler'ın ötesinde hâlâ
   polynomial-time ve exact olan daha geniş bir corrector algebra var mı?
   İlk NP-hardness veya modern stacking collision'ında durmak.

Setun ve Ivakhnenko aktif yedekte tutulmalıdır. Ville, Kaczmarz, Lavrentiev ve
Delsarte yeni exact bottleneck ortaya çıkmadan tekrar compute almamalıdır.

