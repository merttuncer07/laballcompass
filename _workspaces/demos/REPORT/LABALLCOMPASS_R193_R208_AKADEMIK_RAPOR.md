# LabAllCompass Tarihî Darboğazları Yeniden Ziyaret Programı

## R193-R208 Aktif Teori Portföyü: Matematiksel Mekanizmalar, Kırılan Darboğazlar, Negatif Sonuçlar ve Araştırma Sınırları

**Teknik araştırma raporu**  
**Sürüm:** R208 freeze  
**Tarih:** 31 Ağustos 2026  
**Kapsam:** Aktif Lab tarihi R193-R208  
**Durum:** Bağımsız incelemeye hazır çalışma kaydı; hakemli yayın veya küresel yenilik iddiası değildir.

---PAGEBREAK---

# Öz

Bu rapor LabAllCompass laboratuvarında R193-R208 arasında yürütülen tarihî-darboğaz yeniden ziyaret programının tek belgede dondurulmuş genel teknik kaydıdır. Programın amacı eski teorileri bugünün standart akademik kalıplarına yeniden paketlemek veya onları erken bir ürüne zorlamak değildir. Her tarihî hatta önce korunması gereken matematiksel invariant, kayıp bilgi, temsil patlaması veya hesaplama darboğazı ayrıştırılmış; sonra algoritmanın kendisi yerine gerektiğinde koordinat, gözlem operatörü, deney tasarımı, cebirsel temsil ya da geçerlilik sınıfı değiştirilmiştir.

Aktif portföy Markov'un gözlenmeyen olay zincirlerinden Bongard tipi küçük-örnek kavram indüksiyonuna; Turing tipi sonlu-alan mod seçimi, Steinbuch Lernmatrix, Choquet kapasitesi, Volterra kalıtsal serileri, Pugaçev koşullu-optimal filtreleme, Aizerman potansiyel fonksiyonları, Tsetlin sonlu otomatları, Glushkov-Schützenberger bileşimi, ekstremal moment problemleri, Pitrat metabilgisi, Preisach histerezisi, Maslov ters çıkarımı ve Döblin'in mühürlü Kolmogorov manuskriptine kadar uzanır.

Raporun ana bulgusu tek bir “homerun teori” değildir. Bunun yerine farklı olgunluklarda bir mekanizma portföyü elde edilmiştir. En güçlü kapsamlı hat, koşullu moment işlemini whitened koordinatta derleyen; covariance'ı konveks PSD atomlarla kuran; tail kalibrasyonunu recursion covariance'ından ayıran; d=16'ya kadar otomatik atom dili kullanan ve yanlış measurement metric ile aşırı nonlinear update için adaptif güvenlik katmanı ekleyen Pugaçev-esinli closure'dır. En temiz yeni temsil sonuçları arasında nested thinning altında Markov tanımlanabilirliği, bounded-degree automata aggregation için tensor lift, active low-rank Volterra recovery, dense Preisach prefix evaluation, orbit-canonical failure transfer ve Maslov favorable-set'lerinin monotone proof circuit'e derlenmesi vardır.

Her sonuç kapsamıyla birlikte verilmiştir. Bilinen literatürle çakışan yeniden keşifler “breakthrough” diye etiketlenmemiş; başarısız varyantlar ve hangi varsayım kaldırıldığında sonucun öldüğü açıkça korunmuştur. Bu rapor yeni deney içermez. Sayısal tablolar ve doğrulama hükümleri yalnızca daha önce tamamlanmış round kayıtlarından aktarılmıştır.

**Anahtar sözcükler:** tarihî teori yeniden ziyareti, cebirsel derleme, invariant koruma, Markov zincirleri, nonlinear filtering, automata, hysteresis, proof circuits, stochastic comparison.

# 1. Kapsam, iddia düzeyi ve rapor sözleşmesi

Bu belgenin kapsadığı aktif araştırma tarihi R193 ile R208 arasındadır. R179-R192'den discard edilmiş branch, Bridge mimarisi veya laboratuvarı yöneten eski scaffolding bu raporun konusu değildir. R192 aday haritası yalnız aktif damarların başlangıç taksonomisini sağladığı ölçüde kullanılmıştır.

Raporda üç iddia sınıfı ayrılır:

1. **Özdeşlik veya teorem:** Belirtilen varsayımlar altında cebirsel olarak gösterilen sonuç.
2. **Çalışan mekanizma:** Mevcut kod ve daha önce tamamlanmış testlerde doğrulanan fakat evrensel teorem olmayan sonuç.
3. **Araştırma hipotezi:** Henüz kapsamlı collision audit, gerçek veri veya genel hata sınırı gerektiren yön.

Tarihî bir ismin kullanılması, o sonucun tarihî bilim insanı tarafından aynı biçimde bulunduğu veya bugün yeni olduğu anlamına gelmez. Buradaki katkı çoğu zaman tarihî çekirdeği doğru darboğazla eşleyip başka bir temsil altında yeniden kurmaktır.

# 2. Genel metodoloji

## 2.1 Darboğaz-merkezli yeniden ziyaret

Her aday için aynı nötr sorular kullanılmıştır:

1. Tarihî metnin gerçek matematiksel çekirdeği nedir?
2. Teoriyi pratikte durduran işlem hangisidir: tanımlanamazlık, üstel temsil, iteratif çözüm, geçersiz covariance, bilgi kaybı, support büyümesi veya yanlış koordinat mı?
3. Korunması gereken invariant nedir?
4. Darboğaz algoritma değiştirilerek mi, yoksa gözlem düzeni, koordinat, cebir veya problem sınıfı değiştirilerek mi kırılabilir?
5. Sonucu öldürecek en ucuz karşı-örnek nedir?
6. Sonuç modern literatürde zaten hangi ad altında vardır?

Bu yöntem “eski formülü daha hızlı çalıştırma” ile sınırlı değildir. Örneğin Markov hattında estimator değil gözlem operatörü; Volterra'da passive fit değil aktif probe tasarımı; Aizerman'da input momenti değil query prediction invariantı; Pugaçev'de covariance'ın değeri değil PSD parametrizasyonu değiştirilmiştir.

## 2.2 Ortak matematiksel şema

Portföyde tekrar eden genel yapı aşağıdaki gibi özetlenebilir. Tarihî modelin gözlenebilir çıktısını y = F(θ, x) yazalım. Darboğaz çoğu kez θ'yı doğrudan çıkarmak değil, F'nin yanlış koordinatta veya yanlış gözlem altında ele alınmasıdır. Yeni temsil T, gözlem operatörü O ve korunan invariant I seçilerek şu hedef aranır:

:::eq
I(F(θ, x)) = Ĩ(T(θ), O(x)),   maliyet(T, O) ≪ maliyet(F'nin doğrudan çözümü).
:::

Başarılı bir mutasyon dört şartı birlikte sağlamalıdır: eşdeğerlik veya kontrollü hata; açık kapsam; failure boundary; modern collision sınırı. Sentetik bir home-field galibiyeti tek başına teori veya yenilik değildir.

## 2.3 Kanıt ve deney ayrımı

Bu rapordaki deney sayıları yeni koşulardan gelmez. Önceden tamamlanmış round sonuçları, teoremin veya mekanizmanın hangi sınıfta yaşadığını göstermek için özetlenmiştir. Bir sayısal sonuç aşağıdaki rollerden yalnız birini taşır:

- algebraic identity için sanity check;
- representation separation için executable witness;
- ablation ile hangi bileşenin katkı yaptığını ayırma;
- failure boundary'yi görünür kılma;
- scoped capability'nin tekrar edilebilirliğini ölçme.

# 3. Portföyün toplu görünümü

| Hat | Kırılan veya daraltılan darboğaz | Güncel hüküm |
|---|---|---|
| Markov omitted events | Bilinen retention ile de-thinning; nested view ile bilinmeyen retention tanımlama | Temiz scoped özdeşlik; singular/state-dependent sınırlar açık |
| Bongard invariant induction | Atomları elle vermeden affine-invariant sparse relation bulma | Çalışan abstaining primitive; vanishing-ideal prior art güçlü |
| Turing polynomial dispersion | Continuous search ve incumbent lock | Test edilen even-polynomial sınıfta exact finite candidate compiler |
| Steinbuch Lernmatrix | 1-bit kalıcı doygunluk | 2-bit evidence state sorunu çözüyor; signed edge kanıtlanmadı |
| Sparse Choquet | 2^d kapasite tablosu | Sparse 2-additive sınıfta O(d+s) ve exact monotonicity |
| Volterra | O(m²) quadratic kernel ve dense training | Low-rank deploy; active probe altında dense H kurmadan recovery |
| Pugaçev closure | Pahalı conditional update, invalid covariance, recursive tail ve metric shift | R197-R206 arasında tamamlanmış güçlü scoped mimari |
| Aizerman potentials | Büyüyen support ve yanlış moment invariantı | m anchor için en çok 2(m+1) support ile exact prediction |
| Tsetlin response | Binary feedback bilgi kaybı | Kayıp kırıldı; modern policy edge çıkmadı |
| Glushkov-Schützenberger | Cartesian product explosion | XOR direct sum; bounded-degree polynomial tensor lift |
| Extremal moments | Bound var, karar eşiği ve witness yok | Finite support'ta threshold + adversarial atomic witness |
| Pitrat metaknowledge | Exact failure'ın isimlere bağlı kalması | Automorphism orbit'inde sound canonical schema |
| Preisach | O(n²) relay state ve output | Scalar frontier ve dense prefix ile exact O(n) update/output |
| Maslov inverse method | Explicit minimal favorable-set patlaması | Acyclic proof circuit; cyclic sınırda BDD ve order riski |
| Döblin comparison | Sürekli order'ın discretization'da kaybı | Lamperti koordinatında step-certified pathwise order |

# 4. Markov omitted-event zincir derleyicisi

## 4.1 Tarihî çekirdek ve gözlem modeli

Gerçek birinci-mertebe geçiş matrisi P olsun. Her gerçek olay bağımsız olarak p = 1-r olasılıkla kaydedildiğinde iki retained kayıt arasındaki gerçek adım sayısı geometriktir. Gözlenen geçiş matrisi:

:::eq
Qₚ = pP[I-(1-p)P]⁻¹.
:::

Bu resolvent toplamından gelir:

:::eq
Qₚ = Σₖ₌₁^∞ p(1-p)ᵏ⁻¹Pᵏ.
:::

p biliniyorsa doğrudan ters:

:::eq
P = [(pI + (1-p)Qₚ)]⁻¹Qₚ.
:::

R193'te population identity finite-sample simplex projection, likelihood ile seçilen shrinkage ve support floor ile çalışan primitive'e çevrilmiştir. Kullanılan regularized estimator şematik olarak:

:::eq
P̂ₛ = ΠΔ[(1-s)Q̂ + sP̂inv],   0 ≤ s < 1.
:::

Burada ΠΔ satırları olasılık simplex'ine taşır; küçük 1-s bileşeni inverse'in yanlış false-zero üretmesini engeller.

## 4.2 Bilinmeyen retention için nested-thinning teoremi

Tek Qₚ görünümü altında p genel olarak tanımlanamaz. R205 estimator'ı zorlamak yerine gözlem düzenini değiştirmiştir. Aynı bilinmeyen p işlemi ardışık iki kez uygulanır ve Qₚ ile Qₚ² görünür. Dönüşüm:

:::eq
𝒜(X) = X⁻¹-I.
:::

Resolvent özdeşliği:

:::eq
𝒜(Qₚ) = p⁻¹𝒜(P),   𝒜(Qₚ²) = p⁻²𝒜(P).
:::

Dolayısıyla:

:::eq
𝒜(Qₚ²) = p⁻¹𝒜(Qₚ).
:::

P ≠ I ve gerekli matrisler tersinir olduğunda p Frobenius oranından explicit çıkar:

:::eq
p = ⟨𝒜(Qₚ),𝒜(Qₚ)⟩F / ⟨𝒜(Qₚ²),𝒜(Qₚ)⟩F.
:::

Ardından:

:::eq
P = [I+p𝒜(Qₚ)]⁻¹.
:::

Finite-sample model kontrolü proportionality residual'ıdır:

:::eq
ρ = min(c>0) ||𝒜(Q̂ₚ²)-c𝒜(Q̂ₚ)||F / ||𝒜(Q̂ₚ²)||F.
:::

ρ büyükse homogeneous Markov, bağımsız thinning veya eşit-retention varsayımından en az biri bozulmuştur ve inversion abstain etmelidir.

## 4.3 Sonuç ve sınır

R193'te regularized compiler naive gözlenen zinciri true-step held-out log-loss bakımından 70/72 rejimde geçmiştir. Stationary law sonuçlarının zayıf olması beklenen negatif kontroldür; P ve Qₚ aynı stationary dağılımı taşır. Nested-thinning sonucu daha önemlidir: tek görünümdeki yapısal tanımlanamazlık, kontrollü ikinci gözlem operatörüyle optimizer olmadan kalkar.

Sonuç singular P, state-dependent missingness veya iki logger retention oranlarının ilişkisiz olduğu durumu çözmez. Random-time Markov observation literatürü nedeniyle geniş yenilik iddiası yoktur.

# 5. Bongard tipi affine-invariant sparse relation keşfi

## 5.1 Temsil değişikliği

Amaç küçük pozitif/negatif sahnelerden atomları elle vermeden bir ilişki bulmaktır. Bir sahnedeki ölçüm slotları x₀,...,xₙ olsun. Translation ve ortak pozitif scale nuisance'ı şu quotient ile kaldırılır:

:::eq
dᵢ = (xᵢ-xref) / sqrt[(1/n)Σⱼ(xⱼ-xref)² + ε].
:::

Bu koordinattan sabit bir monomial lift ψ(d) kurulur. Pozitif örneklerde aranılan yasa:

:::eq
cᵀψ(d) ≈ 0,   ||c||₂ = 1,   ||c||₀ küçük.
:::

Her candidate support J için pozitif design matrisi Φ₊,J'nin en küçük singular vector'ü katsayı yönünü verir:

:::eq
cJ = argmin(||c||₂=1) ||Φ₊,J c||₂.
:::

Separation yalnız pozitif residual küçüklüğü değildir. Negatif örneklerde residual büyük olmalı; coefficient direction bağımsız pozitif split'lerde kararlı kalmalıdır:

:::eq
stability = |c(1)ᵀc(2)|,
score = median|Φ₋c| - median|Φ₊c|.
:::

Audit-positive normalized residual eşik üstündeyse veya coefficient stability bozulursa sistem yanlış yasa üretmek yerine abstain eder.

## 5.2 Sonuç ve sınır

Beş relation family ve üç gürültü düzeyindeki 60 vakadan 41'i kabul edilmiş; kabul edilenlerin tamamı iki regression baseline'ını geçmiş, 37/41'de exact minimal support bulunmuştur. Eşitlik taşımayan 24 kontrolde 24/24 abstention elde edilmiştir. Yüksek gürültüde coverage düşmesi saklanmamıştır.

Bu bir “genel kavram anlama” teoremi değildir. Polynomial relation family, slot correspondence ve lift önceden sınırlandırılmıştır. Approximate vanishing ideals, symbolic regression ve SINDy ailesiyle güçlü collision vardır. Tutulan katkı affine quotient + sparse nullspace + independent stability + explicit abstention birleşimidir.

# 6. Turing tipi polynomial dispersion compiler

## 6.1 Sonlu aday cebiri

Even-polynomial dispersion:

:::eq
g(k) = c₀+c₁k²+c₂k⁴+...+cₚk²ᵖ.
:::

Sonlu domain modları kₙ = bn/L ve q=(b/L)² ile:

:::eq
gₙ(q) = Σⱼ₌₀ᵖ cⱼ n²ʲ qʲ.
:::

Hedef mod t'nin en kötü rakibe karşı marjı:

:::eq
M(q) = min(r≠t)[gₜ(q)-gᵣ(q)].
:::

Compact q aralığında bu lower envelope'in maksimumu yalnız sonlu bir aday kümesindedir: aralık uçları, target/rival crossing kökleri, her margin polinomunun türev kökleri ve aktif rakiplerin yer değiştirdiği kökler. Bu nedenle continuous grid search, gradient optimizer veya rastgele başlangıç gerekmez.

Seçilen noktada additive quench:

:::eq
uquench = -[gₜ(q*) + max(r≠t)gᵣ(q*)]/2.
:::

Böylece target ve en güçlü rakip quench sonrası eşit büyüklükte zıt işaretli rate alır.

## 6.2 Belirsizlik altında robust difference

Katsayılar kutu belirsizliği cⱼ∈[cⱼ⁻,cⱼ⁺] içindeyse ortak offset'i ayrı ayrı bound etmek aşırı muhafazakâr olur. Bunun yerine target-rival farkı doğrudan ele alınır:

:::eq
Δₜᵣ(q,c) = Σⱼ cⱼ(t²ʲ-r²ʲ)qʲ.
:::

Her terimin işaretine göre kutu üzerindeki exact minimum katsayı ucu seçilir; sonra robust lower envelope yine sonlu kök adaylarından derlenir. Geometri bu shape certificate ile seçilir. Mutlak rate'ler iki kısa modal micro-probe ile ölçülür ve quench orta noktadan kalibre edilir.

## 6.3 Sonuç ve sınır

144-case exact-design benchmark'ında compiler 100.001 noktalı dense oracle'dan geri kalmamış; bütün point quenches sign separation sağlamıştır. Coefficient noise altında point design kırılırken robust-shape kabul ettiği bütün 1% ve 3% noise vakalarında certificate korunmuştur. Pseudospectral PDE doğrulamasında asıl edge güçlü incumbent lock rejiminde ortaya çıkmıştır.

Sonuç non-polynomial/complex dispersion, 2D degenerate eigenspace, mode-dependent actuator veya gerçek cihaz dinamiğini kapsamaz. Global novelty açık, fiziksel deney gereklidir. Fakat test edilen finite-domain even-polynomial sınıfta continuous-search darboğazı gerçekten sonlu cebire indirilmiştir.

# 7. Steinbuch Lernmatrix: latch'ten ölçülebilir kanıt hücresine

Binary Lernmatrix hücresi bir kez hit aldıktan sonra kalıcı olarak 1 olduğunda yüksek load altında bilgi taşımayı bırakır. Sınıf c ve bit j için within-class rate p̂cj, outside-class rate q̂cj olsun. Standardized evidence:

:::eq
zcj = (p̂cj-q̂cj) / sqrt[p̂cj(1-p̂cj)/Nc + q̂cj(1-q̂cj)/N¬c + ε].
:::

Signed ternary hücre:

:::eq
wcj = +1  if zcj≥τ;   -1 if zcj≤-τ;   0 otherwise.
:::

Score basit dot product'tır:

:::eq
scorec(x) = Σⱼ wcj xj.
:::

Bu dönüşüm 1-bit irreversible latch'i yeniden ölçülebilir küçük evidence state'ine yükseltir ve doygunluğu kırar. Fakat eşit bellekli unsigned dört-seviyeli count baseline signed modeli geçmiştir. Doğru sonuç “signed anti-evidence üstün” değil, “tek-hit latch yerine 2-bit kanıt state'i yeterli düzeltme”dir.

# 8. Sparse 2-additive Choquet kapasitesi

Genel discrete kapasite 2ᵈ-2 serbest değer taşır. 2-additive Möbius formunda:

:::eq
Cμ(x) = Σᵢ aᵢxᵢ + Σ(i,j∈E) bᵢⱼ min(xᵢ,xⱼ).
:::

Bir koordinatın en kötü marginal contribution'ı subset enumeration olmadan bulunur:

:::eq
minS Δᵢμ(S) = aᵢ + Σ(j:bᵢⱼ<0) bᵢⱼ.
:::

Monotonicity için gerekli ve 2-additive modelde yeterli certificate:

:::eq
aᵢ + Σ(j:bᵢⱼ<0)bᵢⱼ ≥ 0   her i için.
:::

Seçilen sparse edge kümesi |E|=s ise temsil O(d+s)'dir. R196 testlerinde sparse model exact monotonicity'yi bütün vakalarda korumuş ve additive baseline'ı 27/32 geçmiştir. Dense-interaction stress'te full model 6/6 kazanmıştır. Böylece genel Choquet patlaması değil, sparse 2-additive alt sınıfın patlaması kırılmıştır. Gerçek bir uygulamada önce sparsity adequacy testi gerekir; aksi halde yöntem abstain etmelidir.

# 9. Volterra kalıtsal sistemleri

## 9.1 Separable quadratic representation

Memory vector zₜ için ikinci-derece Volterra response:

:::eq
yₜ = b + ℓᵀzₜ + zₜᵀHzₜ.
:::

H symmetric rank-r ise eigendecomposition:

:::eq
zᵀHz = Σₐ₌₁ʳ λₐ(vₐᵀz)².
:::

Deploy maliyeti O(m²)'den O(mr)'ye iner. Bağımsız segment başlangıçlarında lag state sıfırlanır; aksi halde bir önceki rejimden sahte hereditary memory taşınır. R196'da low-rank sınıfta separable model dense modelin %10 bandında bütün vakalarda kalmış; dense-rank stress'te açık biçimde ölmüştür.

## 9.2 Dense H kurmadan active recovery

R205 training darboğazını active probing ile değiştirmiştir. Önce constant ve odd terimler symmetric probe ile kaldırılır:

:::eq
q(z) = [y(z)+y(-z)-2y(0)]/2 = zᵀHz.
:::

Polarization bilinear oracle verir:

:::eq
ℬ(u,v) = [q(u+v)-q(u-v)]/4 = uᵀHv.
:::

Ω∈Rᵐˣˢ random ve s≥r seçilsin. Standart basis eᵢ ile:

:::eq
Y = HΩ,   Yij = ℬ(eᵢ,ωⱼ).
:::

Olasılık 1 ile range(Y)=range(H). U=orth(Y) ve core:

:::eq
Mab = ℬ(uₐ,uᵦ).
:::

Sonuç:

:::eq
H = UMUᵀ.
:::

Sorgu sayısı ms+r², s=r ile O(mr+r²)'dir; dense m² kernel kurulmaz. Bu exact sonuç resetlenebilir, aktif probe edilebilir, quadratic symmetric rank-r sınıfına aittir. Passive noisy trajectory ve higher-order tensorler açık kalır.

# 10. Pugaçev-esinli derlenmiş koşullu moment kapanışı

## 10.1 Problem

Discrete nonlinear state-space sistemi:

:::eq
xₜ₊₁ = fₜ(xₜ,wₜ),   yₜ = hₜ(xₜ)+vₜ.
:::

Prior approximation:

:::eq
xₜ | y₁:ₜ₋₁ ≈ (mₜ⁻,Pₜ⁻).
:::

Amaç her observation'da particle posterior veya iterative optimizer çalıştırmadan conditional mean, recursion covariance ve tail coordinate'i taşımaktır:

:::eq
mₜ⁺ ≈ E[xₜ|y₁:ₜ],   Pₜ⁺ ≈ Cov(xₜ|y₁:ₜ),   q.90 ayrı tail state.
:::

## 10.2 Analytic chart ve Joseph covariance

Observation Jacobian ve innovation:

:::eq
Hₜ = ∇hₜ(mₜ⁻),   νₜ = yₜ-hₜ(mₜ⁻).
:::

Adaptif measurement metric R̂ₜ altında:

:::eq
Sₜ = HₜPₜ⁻Hₜᵀ+R̂ₜ,   Kₜ = Pₜ⁻HₜᵀSₜ⁻¹.
:::

Güvenli ray katsayısı αₜ ile:

:::eq
mₜ⁰ = mₜ⁻+αₜKₜνₜ,   K̃ₜ=αₜKₜ.
:::

Joseph form:

:::eq
Pₜ⁰=(I-K̃ₜHₜ)Pₜ⁻(I-K̃ₜHₜ)ᵀ+K̃ₜR̂ₜK̃ₜᵀ = BₜBₜᵀ.
:::

Bu analytic update nihai model değil, learned closure için geçerli bir koordinat chart'ıdır.

## 10.3 Whitened conditional compiler

Innovation ve analytic posterior hatası normalize edilir:

:::eq
rₜ=Sₜ⁻¹/²νₜ,   eₜ=Bₜ⁻¹(xₜ-mₜ⁰).
:::

Compiler şu conditional nesneleri öğrenir:

:::eq
c(r,φ)≈E[e|r,φ],   A(r,φ)≈Cov(e|r,φ).
:::

Feature sayısı kullanılan dilde:

:::eq
F(d)=1+7d+d(d+1)/2+d² = 1+(15/2)d+(3/2)d².
:::

İki sabit ridge pass:

:::eq
Β̂₁=(ΦᵀΦ+λI)⁻¹ΦᵀE,
:::

:::eq
Β̂=(ΦᵀWΦ+λI)⁻¹ΦᵀWE.
:::

Deploy update:

:::eq
ĉₜ=φₜᵀΒ̂,   mₜ⁺=mₜ⁰+Bₜĉₜ.
:::

R197 ablation'ı edge'in ikinci robust pass'ten çok conditional geometry ile normalize edilen basis'ten geldiğini göstermiştir.

## 10.4 Convex PSD atom dili

Whitened innovation uzayında K=4+2d merkez veriden keşfedilir. Her merkez için residual outer-product'lardan PSD atom Aₖ⪰0 oluşturulur. Soft weights:

:::eq
wₖ(r)=exp[-||r-μₖ||²/(2τₖ)] / Σⱼ exp[-||r-μⱼ||²/(2τⱼ)].
:::

Conditional covariance:

:::eq
A(r)=Σₖwₖ(r)Aₖ,   Pₜ⁺=BₜA(rₜ)Bₜᵀ.
:::

wₖ≥0 ve Σwₖ=1 olduğundan A(r) konveks PSD kombinasyondur. Her z için:

:::eq
zᵀPₜ⁺z=(Bₜᵀz)ᵀA(rₜ)(Bₜᵀz)≥0.
:::

Covariance sonradan projection ile tamir edilmez; validity parametrizasyonun içindedir.

## 10.5 Mean, variance ve tail koordinatlarının ayrılması

Standardized recursive error radius:

:::eq
ρₜ = sqrt[(xₜ-mₜ⁺)ᵀ(Pₜ⁺)⁻¹(xₜ-mₜ⁺)].
:::

Bağımsız calibration trajectories üzerinde q.90 alınır. Raporlanan ellipsoid:

:::eq
E.90={x:(x-mₜ⁺)ᵀ(Pₜ⁺)⁻¹(x-mₜ⁺)≤q.90²}.
:::

q.90 recursion'da kullanılan Pₜ⁺'yi değiştirmez. Böylece coverage için covariance şişirip sonraki gain'i bozma mekanizması kaldırılır.

## 10.6 Rekürsif destek kapanışı

Offline feature standardizasyonu (φⱼ-μⱼ)/σⱼ, training'de yapısal olarak sıfır fakat recursion'da nonzero olan koordinatlarda patlamıştır. Çıkan genel koşul:

:::eq
supp(φoffline) yaklaşık olarak prediction-update operatörü altında kapalı olmalıdır.
:::

Yaşayan dil support-unstable Cholesky koordinatlarını çıkarır, normalized feature'ları [-8,8] trust bound içinde tutar ve analytic chart'ı fallback olarak korur. Bu, tek-adım train/test coverage yerine reachable recursive support'un sınanması gerektiğini gösterir.

## 10.7 Bilinmeyen measurement correlation

Doğru prior first two moments altında:

:::eq
E[νₜνₜᵀ|Fₜ₋₁] = HₜPₜ⁻Hₜᵀ+Rₜ.
:::

Residual moment:

:::eq
Uₜ=νₜνₜᵀ-HₜPₜ⁻Hₜᵀ,   E[Uₜ|Fₜ₋₁]=Rₜ.
:::

Causal clipped EWMA:

:::eq
Mₜ=(1-η)Mₜ₋₁+η clip(Uₜ/σ²).
:::

Structured compound metric:

:::eq
C(ρ)=(1-ρ)I+ρ11ᵀ.
:::

Eigenvalue'lar 1-ρ (d-1 kez) ve 1+(d-1)ρ olduğundan pozitif definiteness aralığı:

:::eq
-1/(d-1) < ρ < 1.
:::

Arbitrary symmetric moment için tek-pass PSD retraction:

:::eq
M=VΛVᵀ,   M₊=V max(Λ,εI)Vᵀ,
:::

:::eq
C=D⁻¹/²M₊D⁻¹/²,   D=diag(M₊),   Ĉ=(1-γ)I+γC.
:::

Bu map validity'yi korur fakat kısa tek stream'de d(d-1)/2 korelasyonun tanımlanabilirliğini çözmez. Structured düşük-parametreli metric tek stream'de yaşamış; full metric ancak shared-sample ile çalışmıştır.

## 10.8 Bounded nonlinear anchor

Ray aday kümesi:

:::eq
𝒜={0,1/16,1/8,1/4,1/2,3/4,1}.
:::

Her α için local nonlinear posterior objective:

:::eq
Jₜ(α)=(αKₜνₜ)ᵀ(Pₜ⁻)⁻¹(αKₜνₜ)
      +[yₜ-hₜ(mₜ⁻+αKₜνₜ)]ᵀR̂ₜ⁻¹[yₜ-hₜ(mₜ⁻+αKₜνₜ)].
:::

Riskli update'te:

:::eq
αₜ=argmin(α∈𝒜) Jₜ(α).
:::

0∈𝒜 olduğundan scoped güvenlik garantisi:

:::eq
Jₜ(αₜ)≤Jₜ(0).
:::

Bu global posterior optimum değildir; yalnız seçilen ray üzerinde prior noktasından kötü local objective seçilmemesidir.

## 10.9 Kümülatif kanıt

R197 tek-adımlı mean compiler; R198 recursive mean/scale/tail ayrımı; R202 2D whitened PSD closure; R203 otomatik atom dili; R204 d=16 stress ve ablation; R206 adaptif metric ile bounded anchor aşamalarını tamamlamıştır. Aktif lineage'da 15 test geçmiştir.

Önemli donmuş sonuçlar:

- R198 home coverage 0.90037 ve particle512'ye median 54.25x hızlanma;
- R202 home coverage 0.90278 ve 2D particle512'ye 31.6x hızlanma;
- R204 mixture üç domain'de UKF'ye karşı 72/72; d=16'da 36 atom ve 151,344 byte model;
- R206 equicorrelated RMSE 0.21866'dan 0.20906'ya, coverage 0.85793'ten 0.88736'ya;
- signed rank-one shared-full RMSE 0.21956'dan 0.20958'e, coverage 0.85659'dan 0.88528'e;
- 128/128 güvenlik vakasında finite ve PSD covariance;
- adaptif update overhead'i d=16'da yaklaşık 1.21x.

Bu mimari genel Bayesian filtering çözümü değildir. Approximate-prior altında R̂ consistency, gerçek sensör trace'i, universal compiler, modern learned-filter karşılaştırmaları ve küresel yenilik açık kalır.

# 11. Aizerman-Braverman-Rozonoer potential compression

Kernel/potential model:

:::eq
f(q)=Σᵢ₌₁ᴺ αᵢK(xᵢ,q).
:::

R197 input-space momentlerini koruyan merge'in basit centroid merge'e üstün olmadığını göstermiştir. R205 korunacak nesneyi query-domain predictions olarak değiştirmiştir. Anchor q₁,...,qₘ ve support response vector'ü:

:::eq
vᵢ=(K(xᵢ,q₁),...,K(xᵢ,qₘ))∈Rᵐ.
:::

Positive ve negative katsayıları ayır. Positive toplam A₊=Σ(i∈I₊)αᵢ ise:

:::eq
s₊/A₊ = Σ(i∈I₊)(αᵢ/A₊)vᵢ ∈ conv{vᵢ:i∈I₊}.
:::

Carathéodory teoremine göre m+1 vector yeterlidir. Negative kısma ayrı uygulanınca en fazla 2(m+1) original support ile:

:::eq
f'(qⱼ)=f(qⱼ),   j=1,...,m.
:::

Kernel response'ları L-Lipschitz ve query domain anchor'larla ε-cover ise:

:::eq
|f(q)-f'(q)| ≤ 2LεΣᵢ|αᵢ|.
:::

Bu sonuç finite query domain'de exact, cover dışında kontrollüdür. Tüm continuous domain'i finite m ile exact korumaz ve modern kernel coreset literatürüyle çakışabilir.

# 12. Tsetlin finite response automaton

Binary favourable/unfavourable feedback, ödül büyüklüğünü kaybeder. R199 her action için 8-bit bounded state s∈{0,...,255} tutup reward rank'ına doğru sonlu geçiş kullanmıştır:

:::eq
sₜ₊₁ = clip[sₜ + sign(rank(rₜ)-sₜ), 0, 255].
:::

Bu şema doğrudan reward toplamı değil, quantized target level'a yaklaşan finite-state dynamics'tir. Rank response binary response'u 85/96 vakada geçmiş; mean regret'i ciddi azaltmıştır. Ancak rejim başına tune edilmiş UCB/EWMA ailesine karşı yalnız 7/96 kazanmıştır. Dolayısıyla bilgi kaybı kırılmış fakat modern online policy-selection darboğazı kırılmamıştır.

# 13. Glushkov-Schützenberger automata composition

## 13.1 Vector observation factorization

Global output component output vector'ünü koruyorsa full Cartesian product gereksizdir. Her component için characterization word set'i Wᵢ bulunur. State fingerprint:

:::eq
fingerprint(x₁,...,xN) = ( (oᵢ(Aᵢ(w)xᵢ))w∈Wᵢ )ᵢ₌₁ᴺ.
:::

R199 bu certificate'i vector-observable composition'da exact doğrulamış; XOR aggregation'a yanlış taşındığında simetrik cancellation karşı-örneğini açıkça bulmuştur.

## 13.2 XOR direct-sum reachability

Deterministic component state'i one-hot vector, transition'ı GF(2) lineer operatör olsun. İki global state arasındaki initial difference:

:::eq
v₀ = ⊕ᵢ[onehot(lᵢ) XOR onehot(rᵢ)].
:::

Bir word için:

:::eq
v(w)=A(w)v₀,   different(w)=cᵀv(w) mod 2.
:::

Global transition tensor product değil block-diagonal direct sum'dır. Reachable set'in GF(2) span'i component state boyutları toplamından büyük değildir. Gaussian elimination yeni independent image'ları ekler; cᵀv=1 bulunursa actual word witness'tır, tüm span'de sıfırsa iki state bütün word'lerde XOR-equivalent'tır.

64 component x 8 state stress'te full product 58 decimal digit iken direct-sum dimension 512, gözlenen maksimum reachable span 12 olmuştur. Küçük oracle'da 4,320/4,320 agreement sağlanmıştır.

## 13.3 Bounded-degree nonlinear aggregation

Local output oᵢ=cᵢᵀxᵢ ve global observation derece-k multilinear polynomial olsun:

:::eq
g(o₁,...,oN)=Σ(S∈𝒮) γS Π(i∈S)oᵢ,   |S|≤k.
:::

Lifted state:

:::eq
X = ⊕(S∈𝒮) ⊗(i∈S)xᵢ.
:::

Symbol transition:

:::eq
B(a)=⊕(S∈𝒮) ⊗(i∈S)Aᵢ(a).
:::

Uygun C ile exact lineer output:

:::eq
g(o₁(w),...,oN(w)) = CᵀB(w)X.
:::

Dimension:

:::eq
D=Σ(S∈𝒮)Π(i∈S)nᵢ ≤ Σⱼ₌₀ᵏ C(N,j)nʲ = O((Nn)ᵏ),   k sabit.
:::

Gerçek sınır “nonlinearity” değil interaction degree'dir. Tüm N output'un AND'i gibi derece-N aggregation üstel büyümeyi geri getirir. Weighted automata ve linear representation literatürü nedeniyle novelty iddiası yoktur.

# 14. Ekstremal moment decision compiler

Finite support grid {x₁,...,xN}, mean μ ve second moment m₂ verilsin. Feasible dağılımlar polytope'u:

:::eq
pᵢ≥0,   Σᵢpᵢ=1,   Σᵢpᵢxᵢ=μ,   Σᵢpᵢxᵢ²=m₂.
:::

Tail objective bir linear programdır:

:::eq
supₚ Σ(i:xᵢ≥t)pᵢ.
:::

Üç eşitlik kısıtı nedeniyle extreme point en çok üç atom taşır. Compiler feasible üç-atomlu temsilleri enumerate ederek yalnız bound değil şu üçlüyü birlikte verir:

:::eq
(minimum safe threshold t*, worst-case tail probability, atomic witness).
:::

Interior rejimde Cantelli ile iyileşme yoktur; support boundary Cantelli extremizer'ını dışladığında daha sıkı threshold elde edilir. Bu finite-support moment LP'nin bilinen teorisini executable karar ve adversarial witness'a çevirir; broad novelty değildir.

# 15. Pitrat metabilgisi: failure core'un symmetry quotient'i

Exact assignment nogood'ları farklı isimli fakat aynı yapılı sorgular arasında nadiren taşınır. CSP instance I ve incidence yapısını koruyan automorphism group G olsun. Minimal unsatisfiable core C için her g∈G altında g(C) de unsatisfiable'dır.

Canonical schema:

:::eq
can(C)=min(g∈G) encode[g(C)].
:::

İspat çelişkiyledir: g(C)'yi sağlayan assignment varsa g⁻¹ ile geri taşınarak C sağlanır; bu unsatisfiability ile çelişir. Böylece schema benzerlik skorundan değil exact automorphism'ten sound olur.

R200'de elle yazılmış structural-class schema node sayısını yaklaşık %38.5 azaltmıştır. R205 onu incidence graph automorphism orbit'ine kaldırarak schema dilinin en az exact-symmetry sınıfında otomatik üretilmesini sağlamıştır. Approximate analogy, düşük symmetry ve cross-instance embedding açık kalır.

# 16. Preisach histerezis frontier cebiri

Scalar Preisach gridinde relay'ler (αᵢ,βⱼ), αᵢ>βⱼ üçgeninde yaşar. Her β satırında on-state relay'ler α yönünde prefix oluşturur:

:::eq
sᵢⱼ=1 ⇔ i≤fⱼ.
:::

Bu nedenle O(n²) Boolean state yerine n elemanlı frontier f taşınır.

Low-rank density:

:::eq
wᵢⱼ=Σₐ₌₁ʳ UᵢₐVⱼₐ,   αᵢ>βⱼ.
:::

U prefix sums ile output O(nr)'dir. Ancak R200 dense random density'de rank-4 approximation'ın öldüğünü göstermiştir. R205 state compression ile density compression'ı ayırmıştır. Arbitrary dense density için satır prefix tablosu:

:::eq
Wⱼ,k=Σ(i≤k)wᵢⱼ,   Wⱼ,-1=0.
:::

Exact output:

:::eq
y=ΣⱼWⱼ,fⱼ.
:::

Per-step output O(n), state O(n), preprocessing ve density storage O(n²)'dir. Böylece dense density'nin hesaplama darboğazı çözülür; kayıpsız temsil darboğazı çözülmez. Vector-input hysteresis'te scalar staircase özelliği yoktur.

# 17. Maslov inverse method ve symbolic favorable sets

## 17.1 Absorptive support-family cebiri

Bir hedef v için minimal proof support ailesi ℳ(v) olsun. Alternatif proof'lar ve ortak premise'ler:

:::eq
𝒜⊕ℬ = min⊆(𝒜∪ℬ),
:::

:::eq
𝒜⊗ℬ = min⊆{A∪B:A∈𝒜,B∈ℬ}.
:::

Absorption:

:::eq
A⊆B ⇒ A⊕B=A.
:::

Ancak minimal antichain kendisi üstel olabilir.

## 17.2 Upward closure'ı circuit olarak derleme

Her support'u ayrı saklamak yerine monotone Boolean function:

:::eq
Fv(S)=1 ⇔ ∃A∈ℳ(v): A⊆S.
:::

Base fact x için Fx=x. Rule u₁,...,uₖ→v için:

:::eq
Fv ← Fv OR (Fu₁ AND ... AND Fuₖ).
:::

Finite acyclic ground rule hypergraph'ta bu circuit, support upward closure semantics'ini exact taşır. Hash-consing ile boyut:

:::eq
O(|X|+|R|+Σ(r∈R)|body(r)|),
:::

ve |ℳ(v)|'den bağımsızdır.

## 17.3 Üstel ayrım ve cyclic sınır

n bağımsız seçim bloğu:

:::eq
pᵢ←aᵢ,   pᵢ←bᵢ,   goal←p₁,...,pₙ.
:::

Minimal support sayısı 2ⁿ iken circuit:

:::eq
Fgoal = AND(i=1...n)(aᵢ OR bᵢ).
:::

R207'de n=16 için 65,536 support ve 1,048,576 support atomuna karşı 49 circuit node; n=4096 için örtük 2⁴⁰⁹⁶ support'a karşı 12,289 node elde edilmiştir.

Cyclic finite rule graph'ta least fixed point için canonical ROBDD kullanılmıştır. Ancak aynı function interleaved variable order'da 34 node, split order'da 131,072 node üretmiştir. Dolayısıyla BDD evrensel sıkıştırma değildir. Tutulan mimari acyclic bölgede variable-order-free factored circuit, küçük cyclic boundary'de canonical diagram ve diagram büyüdüğünde açık abstention'dır.

First-order unification, infinite term generation ve ucuz general circuit equivalence çözülmemiştir. Provenance semiring, Datalog circuit ve ZDD literatürüyle güçlü collision vardır.

# 18. Döblin karşılaştırma saati ve ayrık-zaman invariantı

## 18.1 Tarihî mekanizma

Döblin'in 1939-1940 mühürlü manuskripti local drift removal ve accumulated variance clock kullanır:

:::eq
Mₜ=Xₜ-X₀-∫₀ᵗa(Xs,s)ds,
:::

:::eq
Aₜ=∫₀ᵗσ²(Xs,s)ds,   Tτ=inf{t:Aₜ>τ}.
:::

Metin aynı diffusion ve ordered drift'ler için CDF comparison ispatı sırasında kesilir:

:::eq
Fa⁻(x,y;s,t) ≥ Fa(x,y;s,t) ≥ Fa⁺(x,y;s,t).
:::

Continuous-time clock Dambis-Dubins-Schwarz, comparison sonucu modern 1D SDE theory tarafından özümsenmiştir. Açık computational soru discretization'ın pathwise order certificate'ını koruyup korumadığıdır.

## 18.2 Raw Euler failure

:::eq
dXₜʲ=bⱼ(Xₜʲ)dt+σ(Xₜʲ)dWₜ,   b₋≤b₀≤b₊.
:::

Raw Euler:

:::eq
Xₖ₊₁ʲ=Xₖʲ+h bⱼ(Xₖʲ)+σ(Xₖʲ)sqrt(h)Zₖ.
:::

States ayrıldıktan sonra noise multiplier'ları farklıdır; ortak Zₖ update map'ini monotone yapmaz ve paths cross edebilir.

## 18.3 Lamperti koordinatı ve ayrık karşılaştırma teoremi

Pozitif smooth ortak diffusion için:

:::eq
H(x)=∫ˣdu/σ(u),   Y=H(X).
:::

Ito dönüşümü:

:::eq
dYₜʲ=βⱼ(Yₜʲ)dt+dWₜ.
:::

βⱼ(y)=g(y)+oⱼ ve o₋≤o₀≤o₊ olsun. Transformed Euler:

:::eq
Yₖ₊₁ʲ=Yₖʲ+hβⱼ(Yₖʲ)+sqrt(h)Zₖ.
:::

qₕ(y)=y+hg(y) monotone nondecreasing ise induction ile:

:::eq
Yₖ⁻≤Yₖ⁰≤Yₖ⁺   her k için.
:::

H⁻¹ artan olduğundan aynı sıra X koordinatına taşınır. Test ailesinde:

:::eq
X=sinh(cY)/c,   σ(X)=sqrt(1+c²X²),
:::

:::eq
βⱼ(y)=-κ tanh(y)+oⱼ.
:::

Yeterli step condition:

:::eq
qₕ'(y)=1-hκ sech²(y)≥0,   dolayısıyla hκ≤1.
:::

Önceden tamamlanan 50,000-path deneyde raw Euler order failure h=0.1/0.05/0.02 için %6.272/%2.664/%0.080 iken transformed scheme bütün beş step size'ta sıfır ihlal vermiştir. Bu consistency karşı-örneği değil finite-step invariant kaybıdır. Discontinuous/vanishing diffusion, local-time correction ve multidimensional partial order açık kalır.

# 19. Negatif sonuçlar: portföyün korunan sınırları

Program yalnız yaşayan mekanizmaları değil aşağıdaki yanlış yolları da korur:

1. Markov stationary law de-thinning için kazanım metriği değildir; Q ve P aynı stationary law'u taşır.
2. Bongard scout validation ayrılmadan non-relation örneklerinde sahte yasalar üretmiştir.
3. Turing point quench küçük coefficient noise altında kırılgandır; robust difference ve probe olmadan certificate yoktur.
4. Steinbuch signed ternary, eşit bellekli unsigned count'u geçmemiştir.
5. Sparse Choquet dense interaction sınıfında açıkça ölür.
6. Rank-3 Volterra dense-rank stress'te ölür; reset yoksa segmentler arası sahte memory oluşur.
7. Pugaçev raw polynomial basis whitened conditional basis'ten kötüdür.
8. Pugaçev E[eeᵀ]-E[e]E[e]ᵀ subtraction'ı recursive covariance'ı çökertebilir.
9. Cartesian innovation grid 10ᵈ büyür; otomatik atom dili gereklidir.
10. Support-unstable feature standardizasyonu recursive feedback altında patlar.
11. Conditional covariance atomları d=16'da global atoma sharpness üstünlüğü göstermemiştir.
12. Full correlation tek kısa stream'de PSD kalırken istatistiksel olarak yetersizdir.
13. Aizerman second-moment merge basit centroid merge'e edge üretmemiştir.
14. Tsetlin rank feedback modern UCB/EWMA policy ailesini geçmemiştir.
15. Glushkov vector certificate XOR aggregation'a doğrudan taşınamaz.
16. Extremal moment compiler interior support'ta Cantelli'den güçlü değildir.
17. Pitrat exact name-bound nogood'ları yapısal transfer sağlamaz.
18. Preisach low-rank density arbitrary dense density'yi temsil etmez.
19. Maslov explicit antichain ve kötü BDD order üstel kalabilir.
20. Döblin raw Euler coarse finite step'te continuous order'ı bozabilir.

Bu sınırlar başarısızlık değil, teori sözleşmesinin parçasıdır.

# 20. Teoriler arası sentez

## 20.1 Korunacak invariantı değiştirmek

Aizerman hattında input momentleri yerine query predictions; Pugaçev hattında arbitrary covariance entries yerine convex PSD atoms; Pitrat hattında literal isimler yerine symmetry orbit; Maslov hattında support listesi yerine upward-closure decision semantics korunmuştur. Bu değişimler hesaplamayı ucuzlatırken neyin kayıpsız kaldığını açıklar.

## 20.2 Kayıp bilgiyi estimator ile değil gözlem tasarımıyla geri getirmek

Markov nested thinning ve Volterra symmetric active probing aynı üst düzey fikri farklı alanlarda gösterir. Tek view altında tanımlanamaz veya pahalı olan nesne, kontrollü ikinci view/probe ile explicit cebire dönüşür:

:::eq
tek görünüm + daha karmaşık optimizer  →  iki kontrollü görünüm + explicit inverse.
:::

## 20.3 Validity, identifiability ve accuracy farklı problemlerdir

Pugaçev full metric PSD retraction covariance'ı geçerli tutar fakat kısa stream'de doğru correlation'ı identify etmez. Choquet projection monotonicity'yi garanti eder fakat dense truth altında accuracy'yi garanti etmez. Maslov BDD canonical equality sağlar fakat küçük representation garanti etmez. Bu ayrım portföyün en genel derslerinden biridir.

## 20.4 Üstel patlamayı kaldırmanın üç yolu

1. **Kısıtlı interaction degree:** Glushkov-Schützenberger tensor lift.
2. **Factored semantics:** Maslov monotone proof circuit.
3. **Geometrik state invariantı:** Preisach staircase frontier.

Üçü de “daha iyi optimizer” değildir. Her biri üstel nesnenin tamamının hangi görev için gereksiz olduğunu gösterir.

## 20.5 Rekürsif sistemlerde tek-adım doğruluk yeterli değildir

Pugaçev support closure ve Preisach frontier bunu iki farklı biçimde gösterir. Bir operator kendi çıktısını tekrar input olarak tüketiyorsa valid feature/state setinin operator altında kapalı olması gerekir. Aksi halde küçük tek-adım hata recursion'da yapısal patlamaya dönüşebilir.

# 21. Olgunluk ve potansiyel değerlendirmesi

Bu bölüm ürün seçmez; yalnız mevcut teorilerin hangi tür değeri taşıdığını sınıflandırır.

## 21.1 En güçlü tamamlanmış scoped mimari

Pugaçev-esinli closure en fazla bileşeni birbirine bağlı, ablation ve failure boundaries'i en açık hattır. Potential değeri sabit-pass nonlinear/non-Gaussian state estimation, PSD uncertainty ve seyrek safety fallback birleşimindedir. Gerçek dünya değeri ancak gerçek sensör trace'i ve modern learned-filter baseline'larıyla ayrı bir doğrulama projesinde ölçülebilir.

## 21.2 En temiz teorik dönüşümler

- Markov nested-thinning identifiability;
- bounded-degree automata tensor lift;
- active low-rank Volterra recovery;
- dense Preisach prefix evaluation;
- orbit-canonical failure learning;
- query-domain signed Carathéodory compression.

Bunların avantajı kısa ve yanlışlanabilir theorem statement'larıdır. Dezavantajı çoğunun komşu modern literatürle güçlü collision olasılığı taşımasıdır.

## 21.3 Güçlü fakat collision-heavy yeniden keşifler

Maslov proof circuits, Bongard vanishing relations, Glushkov XOR linear reachability ve Döblin/Lamperti order preservation teknik olarak gerçek mekanizmalardır; fakat modern provenance, algebraic discovery, weighted automata ve SDE numerics literatürleriyle doğrudan temas eder. Bunlar ürün diye zorlanmamalı, bağımsız problem bu mekanizmayı gerektirdiğinde tekrar kullanılmalıdır.

## 21.4 Düşük öncelikli veya öldürülmüş iddialar

Steinbuch signed advantage, Tsetlin modern policy edge, genel dense sparse-Choquet iddiası, arbitrary dense Volterra rank compression ve Aizerman second-moment merge mevcut kanıtla sürdürülmemelidir.

# 22. Yenilik, yayın ve bağımsız doğrulama sınırı

Bu raporun matematiksel içeriği bir yayın taslağına temel olabilir; ancak yayın iddiasından önce her theorem için şu işler ayrıdır:

1. varsayımların standart notasyonla en dar statement'a çekilmesi;
2. komşu literatürde eşdeğer teorem araması;
3. proof'un bağımsız uzman tarafından kontrolü;
4. synthetic mechanism testinden ayrı gerçek veri veya fizik doğrulaması;
5. modern güçlü baseline'ların aynı budget altında uygulanması;
6. kod ve veri üretim protokolünün bağımsız yeniden çalıştırılması.

Özellikle “tarihî olarak bastırılmış” veya “unutulmuş” anlatısı matematiksel yenilik kanıtı değildir. Tarihî provenance yalnızca doğru başlangıç sorusunu bulmaya yardımcı olur.

# 23. Sonuç

R193-R208 programı, tek bir eski teoriyi yeniden canlandırmaktan daha geniş bir sonuç üretmiştir: tarihî teorilerden bugüne taşınabilecek değer çoğu zaman formülün kendisinde değil, formülün korumaya çalıştığı invariant ile döneminde erişilemeyen temsil veya gözlem düzeni arasındaki gerilimdedir.

Programın en önemli somut çıktıları şunlardır:

- missing-event Markov zincirleri için explicit de-thinning ve nested-view identifiability;
- affine nuisance'ı quotient eden abstaining relation discovery;
- finite-domain even-polynomial mode selection için sonlu root/envelope compiler;
- sparse Choquet, low-rank Volterra ve scalar Preisach için doğru sınıfta compact exact temsiller;
- nonlinear/non-Gaussian filtering için R197-R206 boyunca kapanmış fixed-pass, PSD ve adaptif Pugaçev mimarisi;
- automata aggregation, query-domain support, failure symmetry ve favorable-set semantics için yeni temsil teoremleri;
- continuous stochastic order'ı finite-step numerics içinde koruyan scoped Lamperti update.

Portföyde henüz küresel breakthrough olduğu kesinleşmiş tek bir teori yoktur. Buna karşılık artık elimizde belirsiz tarihî fikirler değil; formülleri, kapsamları, karşı-örnekleri, negatif sonuçları ve test edilmiş mekanizmaları belli bir aktif teori koleksiyonu vardır. Bu, daha sonra yapılacak bağımsız collision audit, yayın seçimi veya maddi ürün çalışması için kaybolmaması gereken bilimsel çekirdektir.

# Ek A. Round ve artifact haritası

| Round | Ana çıktı |
|---|---|
| R193 | Markov omitted-event compiler ve identifiability boundary |
| R194 | Bongard affine sparse invariant scout |
| R195 | Polynomial dispersion compiler, robust difference ve quench |
| R196 | Steinbuch, sparse Choquet, separable Volterra |
| R197 | Pugaçev conditional mean compiler; Aizerman bounded support ablation |
| R198 | Recursive mean/scale/tail closure |
| R199 | Tsetlin rank response, Glushkov vector factorization, extremal moment compiler |
| R200 | Pitrat quotient schema ve Preisach frontier |
| R201 | XOR direct-sum automata equivalence |
| R202 | 2D whitened multivariate PSD closure |
| R203 | Automatic PSD atom language ve recursive support closure |
| R204 | d=16 stress, ablation ve correlated-noise failure boundary |
| R205 | Altı theorem-level mutation ve yeni source scout |
| R206 | Adaptive innovation metric, PSD retraction, bounded anchor; Pugaçev freeze |
| R207 | Maslov symbolic favorable-set compiler |
| R208 | Döblin/Lamperti order-preserving discretization |

# Ek B. Seçilmiş kaynakça

[1] A. A. Markov. Bağımlı denemeler ve gözlenmeden bırakılan olaylar üzerine yayın hattı, MathNet bibliyografyası.

[2] F. Barsotti, Y. De Castro, B. Espinasse, P. Rochet. Estimating the transition matrix of a Markov chain observed at random times, 2014.

[3] M. M. Bongard. Pattern Recognition, 1967; küçük örnekten yapısal kavram indüksiyonu hattı.

[4] R. Livni, D. Lehavi, S. Schein, H. Nachlieli, N. Shalev-Shwartz, A. Globerson. Vanishing Component Analysis, 2013.

[5] A. M. Turing. The Chemical Basis of Morphogenesis, 1952; Turing morphogenesis archive.

[6] K. Steinbuch. Die Lernmatrix, Kybernetik 1, 36-45, 1961.

[7] G. Choquet. Theory of Capacities, Annales de l'Institut Fourier 5, 131-295, 1954.

[8] V. Volterra. The Theory of Permutable Functions, 1915.

[9] V. S. Pugaçev, I. N. Sinitsyn, V. I. Shin. Conditionally optimal filtering for nonlinear stochastic systems, 1987.

[10] M. A. Aizerman, E. M. Braverman, L. I. Rozonoer. Potential-function methods in pattern recognition, 1964.

[11] M. L. Tsetlin. Finite Automata and Models of Simple Forms of Behaviour, 1963.

[12] V. M. Glushkov. The Abstract Theory of Automata, 1961.

[13] M. P. Schützenberger ve takip eden weighted/rational series literatürü.

[14] J. Pitrat. Artificial Beings: The Conscience of a Conscious Machine, 2009.

[15] F. Preisach. Über die magnetische Nachwirkung, Zeitschrift für Physik 94, 277-302, 1935.

[16] S. Yu. Maslov. The inverse method of establishing deducibility in the classical predicate calculus, 1964.

[17] T. J. Green, G. Karvounarakis, V. Tannen. Provenance semirings, PODS 2007.

[18] W. Döblin. Sur l'équation de Kolmogoroff, manuskript 1939-1940, açılış/yayın 2000.

[19] K. E. Dambis; L. E. Dubins, G. Schwarz. Continuous local martingales ve time-change representation, 1965.

[20] Sage-Husa ve Mehra adaptive covariance filtering çalışmaları, 1969-1970.

[21] Hoff ve Niu. Covariance regression, Statistica Sinica, 2012.

[22] KalmanNet ve ML-EnCMF: learned/hybrid conditional filtering literatürü, 2021 ve sonrası.

---PAGEBREAK---

# Kaynak URL'leri (Ek C)

1. https://www.mathnet.ru/php/person.phtml?option_lang=eng&personid=39732
2. https://arxiv.org/abs/1405.0384
3. https://proceedings.mlr.press/v28/livni13.html
4. https://turingarchive.kings.cam.ac.uk/morphogenesis
5. https://bibbase.org/network/publication/steinbuch-dielernmatrix-1961
6. https://www.numdam.org/articles/10.5802/aif.53/
7. https://www.mathnet.ru/eng/at4683
8. https://www.mathnet.ru/eng/at11723
9. https://www.mathnet.ru/eng/rm6373
10. https://www.mathnet.ru/eng/rm6668
11. https://doi.org/10.1002/9780470611791
12. https://doi.org/10.1007/BF01349418
13. https://www.mathnet.ru/php/getFT.phtml?jrnid=dan&option_lang=rus&paperid=30298&what=fullt
14. https://www.cs.ucdavis.edu/~green/papers/pods07.pdf
15. https://djalil.chafai.net/docs/M2/history-brownian-motion/CRAS%20Doeblin%20-%202000%20-%20French/Doeblin-Partie-II-Equation-de-Kolmogoroff.pdf
16. https://www.pnas.org/doi/10.1073/pnas.53.5.913
17. https://doi.org/10.1109/TAC.1970.1099422
18. https://arxiv.org/abs/2107.10043
19. https://arxiv.org/abs/2106.07908
20. https://doi.org/10.5705/ss.2010.051
