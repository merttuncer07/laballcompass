# R205 — Tarihî darboğazlar için nötr teori dalgası

## Amaç ve sınır

Bu not bir ürün belgesi, akademik makale taklidi veya tek bir nişe doğru yol
haritası değildir. Altı tarihî araştırma hattında daha önce açık kalmış altı
farklı işlemi ele alır. Hedef, tarihî metni olduğu gibi yeniden uygulamak değil,
o metnin ulaşamadığı kabiliyeti bugün hangi ek varsayım veya yeni temsil ile
elde edebildiğimizi açıkça göstermektir.

Her bölüm şu ayrımı korur:

- **çözülen:** verilen varsayımlar altında yeni sonuç;
- **çözülmeyen:** varsayım kaldırıldığında açık kalan problem;
- **yenilik durumu:** burada ispatlanan şeyin doğru olması, literatürde ilk kez
  burada bulunduğu anlamına gelmez. Ayrıntılı collision audit daha sonra yapılır.

Pugaçev hattı R204'te ikinci tur survivor olarak park edilmiştir. Bu not, o tek
koordinatı daha fazla kazmak yerine araştırma genişliğini geri getirir.

---

## 1. Markov hattı: bilinmeyen thinning oranını deney tasarımıyla tanımlamak

### Eski açık işlem

Birinci-mertebe zincirin gerçek geçiş matrisi `P` olsun. Her gerçek olay bağımsız
olarak `p=1-r` olasılıkla kaydedilirse retained olaylar arasındaki population
geçişi

\[
Q_p=pP\bigl[I-(1-p)P\bigr]^{-1}
\]

olur. `p` biliniyorsa `P` explicit olarak geri alınabilir. Yalnız `Q_p`
gözleniyorsa ise `p` genel olarak tanımlanamaz: farklı `p` değerleri farklı `P`
matrisleriyle aynı gözlenen zinciri verebilir.

Buradaki değiştirme, daha karmaşık bir estimator kurmak değil, **gözlem
düzenini** değiştirmektir. Aynı bilinmeyen retention işlemi iki kez ardışık
uygulansın:

- logger 1 gerçek zinciri `p` ile tutar ve `Q_p` üretir;
- logger 2 logger 1'in tuttuğu olayları yine aynı `p` ile tutar ve toplamda
  `Q_{p^2}` üretir.

### Önerme 1 — nested-thinning tanımlanabilirliği

`P`, `Q_p` ve `Q_{p^2}` tersinir; `P != I`; `0<p<=1` olsun. Şu dönüşümü
tanımlayalım:

\[
\mathcal A(X)=X^{-1}-I.
\]

O zaman

\[
\mathcal A(Q_p)=\frac1p\mathcal A(P),
\qquad
\mathcal A(Q_{p^2})=\frac1{p^2}\mathcal A(P),
\]

ve dolayısıyla

\[
\mathcal A(Q_{p^2})=\frac1p\mathcal A(Q_p).
\]

Population seviyesinde bilinmeyen retention doğrudan

\[
\boxed{
p=
\frac{\langle \mathcal A(Q_p),\mathcal A(Q_p)\rangle_F}
     {\langle \mathcal A(Q_{p^2}),\mathcal A(Q_p)\rangle_F}
}
\]

ile, gerçek zincir ise

\[
\boxed{P=\bigl[I+p\mathcal A(Q_p)\bigr]^{-1}}
\]

ile belirlenir.

### İspat

Tanımdan

\[
Q_p^{-1}
=\frac1p\bigl[I-(1-p)P\bigr]P^{-1}
=\frac1pP^{-1}-\frac{1-p}{p}I.
\]

Her iki taraftan `I` çıkarınca

\[
Q_p^{-1}-I=\frac1p(P^{-1}-I)
\]

elde edilir. Aynı eşitliği `p^2` için yazmak proportionality sonucunu verir.
`P!=I` olduğu için `A(Q_p)` sıfır değildir; Frobenius iç çarpımı scalar `p`yi
verir. Son eşitliği `P` için çözmek ikinci kutulu formülü verir. ∎

### Neyi çözüyor?

Tek retained sequence'te çözülemeyen retention-rate tanımlanabilirliği, aynı
sampling işleminin kontrollü biçimde iki kez uygulanabildiği durumda optimizer,
EM veya zaman damgası olmadan çözülür. Ek bilgi bir prior değil, ikinci bir
gözlem operatörüdür.

Finite sample'da iki `A` matrisinin proportionality residual'ı aynı zamanda
model kontrolüdür:

\[
\rho=\min_{c>0}
\frac{\|\mathcal A(\widehat Q_{p^2})-c\mathcal A(\widehat Q_p)\|_F}
     {\|\mathcal A(\widehat Q_{p^2})\|_F}.
\]

`rho` büyükse homogeneous Markov, bağımsız thinning veya eşit-retention
varsayımlarından en az biri bozulmuştur; inversion abstain etmelidir.

### Açık sınır

- Singular `P` için ters yerine invariant-subspace/resolvent formu gerekir.
- İkinci logger'ın retention'ı birincisiyle aynı değil ve aralarındaki ilişki
  bilinmiyorsa yalnız retention oranlarının oranı tanımlanır; mutlak ölçek yine
  açık kalır.
- State-dependent missingness bu scalar cebire uymaz.

**Hüküm:** Önceki genel tanımlanamazlık, belirli ve uygulanabilir bir multiview
gözlem tasarımında çözülmüştür.

---

## 2. Glushkov–Schützenberger hattı: bounded-degree nonlinear aggregation

### Eski açık işlem

R201, synchronized automata'nın XOR ile toplanan output'unda full Cartesian
product yerine GF(2) direct-sum reachability kullandı. Açık problem, AND/OR veya
daha genel nonlinear output aggregation'da bu küçülmenin kaybolmasıydı.

Burada soru “bütün nonlinear aggregation” olarak değil, interaction derecesi
sabit olan polynomial aggregation olarak yeniden yazılır.

`N` deterministic component aynı word'ü okusun. Component `i`nin one-hot state'i
`x_i in F^{n_i}`, symbol transition'ı `A_i(a)`, local output'u

\[
o_i=c_i^T x_i
\]

olsun. Global gözlem, bir `F` alanı üzerinde multilinear polynomial olsun:

\[
g(o_1,\ldots,o_N)
=\sum_{S\in\mathcal S} \gamma_S\prod_{i\in S}o_i,
\qquad |S|\le k.
\]

### Önerme 2 — bounded-degree tensor lift

Şu lifted state'i kur:

\[
X=\bigoplus_{S\in\mathcal S}\bigotimes_{i\in S}x_i.
\]

Her symbol için transition

\[
B(a)=\bigoplus_{S\in\mathcal S}\bigotimes_{i\in S}A_i(a)
\]

ve uygun linear output vector'ü `C` seçildiğinde, her word `w` için

\[
\boxed{g(o_1(w),\ldots,o_N(w))=C^T B(w)X}
\]

eşitliği exact'tır. Lifted dimension

\[
D=\sum_{S\in\mathcal S}\prod_{i\in S}n_i
\]

olur. Eğer `n_i<=n` ve bütün derece-`<=k` monomial'ler izinliyse

\[
D\le\sum_{j=0}^k {N\choose j}n^j=O((Nn)^k)
\]

ve sabit `k` için full product `n^N` yerine polynomial büyür.

### İspat

Her monomial için

\[
\prod_{i\in S}o_i(w)
=\prod_{i\in S}c_i^TA_i(w)x_i
=\left(\bigotimes_{i\in S}c_i\right)^T
 \left(\bigotimes_{i\in S}A_i(w)\right)
 \left(\bigotimes_{i\in S}x_i\right).
\]

Monomial bloklarını direct sum içinde yan yana koyup `gamma_S` katsayılarını
linear output'a almak sonuç eşitliğini verir. Dimension bound, derece `j`
monomial sayısını ve her tensor bloğunun en fazla `n^j` boyutunu sayar. ∎

### Sonuç

İki global state'in bütün word'ler altında observational equivalence problemi,
bu `D` boyutlu linear representation'ın reachable-span testine iner. XOR,
karakteristik ikide derece-1 özel durumdur. Pairwise nonlinear aggregation
derece-2 lift ile exact çözülebilir.

### Açık sınır

- Bütün component output'larının AND'i derece `N`dir; bound yeniden üstel olur.
- Asynchronous clocks ve hidden shared state tensor bloklarını birbirine bağlar.
- Boolean OR'un multilinear polynomial derecesi genel olarak fan-in ile büyür.
- Sonuç exact bir temsil teoremidir; en küçük temsil olduğunu söylemez.

**Hüküm:** “Nonlinear aggregation direct-sum'u tamamen öldürür” sonucu fazla
güçlüdür. Gerçek sınır nonlinearity değil, interaction derecesidir.

---

## 3. Preisach hattı: arbitrary dense density ile exact hızlı output

### Eski açık işlem

R200 scalar Preisach relay state'ini `O(n^2)` Boolean matristen `O(n)` staircase
frontier'e exact indirdi. Output'u `O(nr)` yapmak için density'yi rank-`r`
varsaydı. Dense random density bu varsayımı bozdu.

Fakat state sıkıştırması ile density sıkıştırması aynı problem değildir. Dense
density zaten depolanacaksa, exact output için low-rank gerekmez.

`beta_j` satırındaki on relay'lerin `alpha` sırasına göre prefix oluşturduğunu
ve frontier'in `f_j` olduğunu yazalım:

\[
s_{ij}=1\iff i\le f_j.
\]

Dense Preisach ağırlığı `w_{ij}` olsun.

### Önerme 3 — dense-prefix output teoremi

Her satır için bir kez

\[
W_{j,k}=\sum_{i\le k}w_{ij},\qquad W_{j,-1}=0
\]

prefix toplamları kurulursa, herhangi bir geçerli frontier state'inin output'u

\[
\boxed{y=\sum_j W_{j,f_j}}
\]

ile exact ve `O(n)` zamanda hesaplanır. Relay matrisini yeniden kurmak gerekmez.

### İspat

Frontier özelliği nedeniyle

\[
y=\sum_j\sum_i w_{ij}s_{ij}
 =\sum_j\sum_{i\le f_j}w_{ij}
 =\sum_jW_{j,f_j}.
\]

Her satır tek table lookup ve toplama gerektirir. ∎

### Neyi çözüyor?

- scalar Preisach state: `O(n)`;
- arbitrary dense density ile per-step exact output: `O(n)`;
- preprocessing: `O(n^2)`;
- density/prefix storage: `O(n^2)`.

Dolayısıyla R200'de low-rank'a bağlanan **hesap** sınırı kaldırılır. Low-rank
yalnız density belleğini de küçültmek istenirse gereklidir.

### Açık sınır

- `O(n^2)` arbitrary density bilgisinin kendisi kayıpsız olarak genel durumda
  `o(n^2)` parametreye indirilemez; ek yapı veya approximation gerekir.
- Vector-input hysteresis'te satır-prefix frontier özelliği yoktur.
- Continuous density için quadrature/discretization hatası ayrı problemdir.

**Hüküm:** Dense Preisach'ta exact hızlı output darboğazı çözülür; dense density
representation darboğazı çözülmez. İkisini tek sorun saymak önceki notun hatasıydı.

---

## 4. Volterra hattı: dense kernel kurmadan doğrudan rank-`r` tanımlama

### Eski açık işlem

R196, quadratic Volterra kernel'ini dense `H` fit ettikten sonra rank-truncate
etti. Deploy ucuzladı fakat training hâlâ `O(m^2)` kernel'i kurdu. Açık problem,
factor'ları dense matrise hiç uğramadan tanımlamaktır.

Burada passive regression yerine tarihî sistem-identification ruhuna daha uygun
bir ek kabiliyet kullanılır: resetlenebilir sistem ve aktif probe input'ları.

İkinci derece response

\[
y(z)=b+\ell^Tz+z^THz,
\qquad H=H^T,quad \operatorname{rank}(H)=r
\]

olsun. `z`, bir deneyde hazırlanan lag/input-history vector'üdür.

Önce odd ve constant parçaları symmetric probing ile kaldır:

\[
q(z)=\frac{y(z)+y(-z)-2y(0)}2=z^THz.
\]

Polarization ile bilinear oracle elde edilir:

\[
\mathcal B(u,v)=\frac{q(u+v)-q(u-v)}4=u^THv.
\]

### Önerme 4 — active low-rank Volterra recovery

`Omega in R^{m x s}` sürekli bir dağılımdan seçilsin ve `s>=r` olsun. Şu matrisi
bilinear probe'larla kur:

\[
Y=H\Omega,
\qquad Y_{ij}=\mathcal B(e_i,\omega_j).
\]

Olasılık 1 ile `range(Y)=range(H)` olur. `U=orth(Y)` ve

\[
M_{ab}=\mathcal B(u_a,u_b)
\]

seçilirse

\[
\boxed{H=UMU^T}
\]

exact'tır. Gerekli bilinear sorgu sayısı `ms+r^2`; `s=r` ile
`O(mr+r^2)` olur ve dense `m^2` kernel hiç kurulmaz.

### İspat

Symmetric rank-`r` matris için `H=U_* Lambda U_*^T` yazılabilir. O zaman

\[
Y=U_*\Lambda(U_*^T\Omega).
\]

Random `Omega` için `U_*^T Omega` satır-rank `r` olur; dolayısıyla
`range(Y)=range(U_*)=range(H)`. `U` aynı range'in ortonormal basis'idir ve
`H=UU^THUU^T`. Orta blok `U^THU` tam olarak bilinear probe'lardan gelen `M`dir.
∎

### Neyi çözüyor?

Quadratic, symmetric, düşük-rank ve aktif olarak probe edilebilen Volterra
sisteminde direct factor identification problemi çözülür. Çözüm nonconvex factor
optimization yapmaz; önce range'i bulur, sonra yalnız `r x r` core'u ölçer.

### Açık sınır

- Passive tek trajectory'de gereken probe vector'ları üretilemeyebilir.
- Reset yoksa lag histories birbirine karışır.
- Noise altında exact rank yerine randomized numerical-rank ve confidence
  analizi gerekir.
- Higher-order Volterra tensorleri için bilinear polarization yeterli değildir.

**Hüküm:** R196'nın “direct factor training açık” problemi aktif-identification
sınıfında teorik olarak kapanır; passive genel problem açık kalır.

---

## 5. Pitrat hattı: elle schema yazmadan sound failure transfer

### Eski açık işlem

R200, exact nogood yerine symmetry-quotient failure schema taşıdı ve aramayı
azalttı; fakat schema biçimi—aynı structural class'taki değişkenlerin farklı
değer alması—kodda elle verilmişti. Açık problem, failure schema dilini sistemin
kendisinin bulmasıydı.

Bir CSP instance'ı `I`, onun variable/value/constraint incidence yapısını koruyan
automorphism grubu `G` olsun. Bir partial assignment ile constraint subset'inin
birlikte oluşturduğu minimal failure core'u `C` ile gösterelim.

### Önerme 5 — orbit-canonical failure learning

`C` unsatisfiable ve `g in G` ise `g(C)` de unsatisfiable'dır. Dolayısıyla

\[
\operatorname{can}(C)=\min_{g\in G}\operatorname{encode}(g(C))
\]

canonical orbit temsilcisi sound bir failure schema'dır. Aynı canonical forma
sahip yeni bir core, değişken veya value isimleri farklı olsa bile çözüm
aramadan reddedilebilir.

### İspat

Tersini varsayalım ve `g(C)`yi sağlayan assignment `a` olsun. `g`, instance'ın
automorphism'i olduğundan `g^{-1}(a)`, `C` içindeki bütün mapped constraint ve
assignment literal'larını sağlar. Bu `C`nin unsatisfiable olmasıyla çelişir. ∎

### Schema dili nasıl otomatikleşir?

1. CSP, variable/value/constraint tiplerini renk olarak taşıyan incidence graph'a
   çevrilir.
2. Graph automorphism motoru `G`nin generator'larını bulur.
3. Her learned minimal core bu generator'lar altında canonicalize edilir.
4. Cache tekil isimleri değil canonical orbit temsilcisini saklar.

Burada “schema” önceden yazılmış bir mantıksal template değildir; instance'ın
gerçek symmetry group'u altında core orbit'idir. Soundness, benzerlik skorundan
değil automorphism'ten gelir.

### Açık sınır

- Automorphism olmayan yaklaşık analojiler otomatik olarak sound değildir.
- Canonicalization'ın worst-case maliyeti search kazancını aşabilir.
- İki farklı problem instance'ı arasında transfer için automorphism değil,
  isomorphism/embedding certificate gerekir.
- Symmetry'si az olan problemler fazla schema paylaşmaz.

**Hüküm:** Elle yazılmış structural-class schema ihtiyacı, exact symmetry'nin
yeterli olduğu sınıfta kaldırılır. Genel metaknowledge discovery çözülmüş değildir.

---

## 6. Aizerman–Braverman–Rozonoer hattı: exact query-domain support compression

### Eski açık işlem

Potential-function classifier/regressor

\[
f(q)=\sum_{i=1}^N \alpha_i K(x_i,q)
\]

yeni örneklerle support büyütür. R197'nin moment-preserving merge'i iyi çalıştı
ama basit centroid merge'e üstün değildi. Sorun, input-space momentlerini korumanın
asıl korumak istediğimiz şey—karar fonksiyonu—için doğru invariant olmamasıydı.

Şimdi korunacak nesne doğrudan bir query/audit domain'indeki predictions olsun.
Anchor sorgular `q_1,...,q_m` ve her support'un response vector'ü

\[
v_i=(K(x_i,q_1),\ldots,K(x_i,q_m))\in\mathbb R^m
\]

olarak tanımlansın.

### Önerme 6 — signed Carathéodory potential compression

Katsayıları positive ve negative olarak ayır:

\[
I_+=\{i:\alpha_i>0\},\qquad I_-=\{i:\alpha_i<0\}.
\]

Herhangi bir `N` için, original support içinden seçilen en fazla

\[
\boxed{2(m+1)}
\]

potential ve yeni signed ağırlıklarla bütün anchor predictions exact korunabilir:

\[
f'(q_j)=f(q_j),\qquad j=1,\ldots,m.
\]

Eğer bütün katsayılar aynı işaretliyse `m+1` support yeterlidir.

### İspat

`A_+=sum_{i in I+} alpha_i` olsun. Positive katkı vector'ü

\[
s_+=\sum_{i\in I_+}\alpha_i v_i
=A_+\sum_{i\in I_+}\frac{\alpha_i}{A_+}v_i
\]

olduğundan `s_+/A_+`, `{v_i:i in I+}` convex hull'undadır. Carathéodory
teoremine göre aynı nokta en fazla `m+1` vector'ün convex combination'ıyla
yazılabilir. Negative kısma aynı argümanı mutlak ağırlıklarla ayrı uygula ve
iki sparse temsili çıkar. ∎

### Domain genelleme sınırı

`K(x,.)` bütün `x`ler için `L`-Lipschitz olsun. Her yeni query `q`, bir anchor
`q_j`ye en fazla `epsilon` uzaklıktaysa ve compression positive/negative toplam
kütlelerini koruyorsa

\[
\boxed{
|f(q)-f'(q)|\le 2L\epsilon\sum_i|\alpha_i|
}
\]

elde edilir. Çünkü iki model anchor'da eşittir; anchor ile `q` arasındaki iki
değişim ayrı ayrı Lipschitz bound ile sınırlanır.

### Neyi çözüyor?

Support, input-space centroid veya second moment'i yaklaşık korumak yerine,
seçilmiş karar/query domain'inde **exact prediction invariantı** ile sıkıştırılır.
Boyut support geçmişine değil korunacak query sayısı `m`ye bağlıdır.

### Açık sınır

- Bütün sürekli domain'i exact korumak için genel finite `m` yetmez.
- Query cover büyürse support budget da büyür.
- Kernel evaluations'ın kendisi pahalıysa anchor response vector'lerini kurmanın
  maliyeti ayrıca ele alınmalıdır.
- Bu sonuç modern kernel coreset/convex geometry literatürüyle güçlü biçimde
  çakışabilir; tarihî isim novelty sağlamaz.

**Hüküm:** Heuristic moment merge yerine, açıkça tanımlanmış bir query domain'i
için exact ve constructive support bound elde edilir.

---

## 7. Altı sonucun ortak yapısı

Bu dalgada tek bir matematik modası uygulanmadı. Her darboğaz farklı yerden
kırıldı:

| Tarihî hat | Eski engel | Değiştirilen şey | Yeni sonuç türü |
|---|---|---|---|
| Markov | bilinmeyen observation rate ile identifiability | estimator değil gözlem operatörü; nested view | explicit identifiability theorem |
| Glushkov/Schützenberger | nonlinear aggregation'da product explosion | bounded interaction-degree tensor lift | exact polynomial-size representation |
| Preisach | dense density'de output maliyeti | density compression yerine row-prefix integral | exact `O(n)` evaluation |
| Volterra | dense kernel kurulmadan factor learning yok | passive fit yerine symmetric active probing | exact `O(mr+r^2)` identification |
| Pitrat | schema dili elle verilmiş | core'u problem automorphism orbit'ine quotient et | automatically generated sound schema |
| Aizerman | support merge yanlış invariantı koruyor | input moments yerine query predictions | exact finite-domain coreset |

Ortak metodolojik ders “her şeyi cebire çevir” değildir. Daha genel ders:

> Önce korunması gereken invariantı ve elde bulunmayan bilgiyi ayır. Sonra ya
> temsili, ya gözlem düzenini, ya deney tasarımını, ya da geçerlilik sınıfını
> değiştir. Eski algoritmayı yalnız hızlandırmak çoğu zaman gerçek darboğazı
> çözmez.

## 8. Şimdiki nötr değerlendirme

Bu altı sonuç aynı olgunlukta değildir:

- **En temiz yeni teoremler:** nested-thinning Markov identifiability ve
  bounded-degree automata aggregation.
- **En açık kaçırılmış computational ayrım:** dense Preisach prefix evaluation;
  mevcut R200 hükmünü doğrudan düzeltir.
- **En güçlü deney-tasarımı sonucu:** active low-rank Volterra recovery.
- **En sağlam fakat sınıfı dar representation sonuçları:** orbit-canonical
  Pitrat cores ve query-domain Carathéodory compression.

Hiçbiri bu aşamada bir ürüne, sektöre veya “breakthrough” etiketine bağlanmaz.
Bir sonraki bilimsel adım daha fazla benchmark değil:

1. kısa sanity counterexample'larıyla formülleri çürütmeye çalışmak;
2. surviving sonuçların tarihî ve modern collision sınırını birincil kaynaklarla
   kontrol etmek;
3. aynı dönemin yeni adaylarını tarayıp bu altı sonucun yanına eklemek;
4. yalnız bundan sonra hangi teorilerin daha derin ikinci tura değdiğine karar
   vermek.

## Tarihî başlangıç izleri

- Markov yayın listesi ve unobserved-event çalışmaları:
  https://www.mathnet.ru/php/person.phtml?option_lang=eng&personid=39732
- Glushkov, *The Abstract Theory of Automata* (1961):
  https://www.mathnet.ru/eng/rm6668
- Schützenberger/weighted automata linear representations:
  https://www-igm.univ-mlv.fr/~perrin/Livres/RationalSeries9April2010.pdf
- Preisach, *Über die magnetische Nachwirkung* (1935):
  https://doi.org/10.1007/BF01349418
- Volterra, *The Theory of Permutable Functions* (1915):
  https://commons.wikimedia.org/wiki/File:The_theory_of_permutable_functions_(IA_theoryofpermutab00voltrich).pdf
- Pitrat, *Artificial Beings* (2009):
  https://doi.org/10.1002/9780470611791
- Aizerman, Braverman, Rozonoer, potential functions (1964):
  https://www.mathnet.ru/eng/at11723

