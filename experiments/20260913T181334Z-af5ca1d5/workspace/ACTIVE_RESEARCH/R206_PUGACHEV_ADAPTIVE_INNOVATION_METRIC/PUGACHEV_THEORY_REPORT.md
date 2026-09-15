# Pugaçev-esinli derlenmiş koşullu moment kapanışı

## R197–R206 nihai teori, mekanizma ve deney raporu

## 1. Kısa hüküm

Bu çalışma hattı bitmiş bir araştırma paketi olarak dondurulabilir. Çözülen
problem şudur:

> Belirli bir nonlinear/non-Gaussian state-space ailesinde, her ölçümde particle
> posterior veya iteratif optimizer çalıştırmadan conditional mean ve geçerli
> uncertainty nasıl rekürsif, sabit sayıda işlemle taşınabilir?

Elde edilen çözüm tek bir numara değildir. Beş koordinat birlikte kapanmıştır:

1. pahalı conditional mean işlemi whitened koordinatta offline derlendi;
2. conditional covariance, çıkarma yoluyla değil convex PSD atomlarla kuruldu;
3. nominal tail coverage, recursion covariance'ından ayrıldı;
4. otomatik innovation dili `d=16`ya kadar lineer sayıda atomla taşındı;
5. yanlış measurement metric ve aşırı nonlinear update için online adaptasyon ve
   güvenli fallback eklendi.

Bu sonuç **genel Bayesian filtering çözümü değildir**. Gerçek veri doğrulaması,
universal model ve literatür yeniliği de kanıtlanmamıştır. Buna karşılık çalışan
mekanizma, matematik, kod, pozitif ve negatif deneyler artık bağımsız olarak
incelenebilir durumdadır.

---

## 2. Tarihî problem gerçekte neydi?

Pugaçev, Sinitsyn ve Shin'in 1987 çalışması nonlinear stochastic systems için
istatistiksel analiz ve real-time conditionally-optimal filtering problemlerini
birlikte ele alır. Temel pratik gerilim açıktır: optimal nonlinear posterior
genellikle yüksek veya sonsuz boyutlu bir nesnedir; real-time estimator ise her
adımda hesaplanabilecek kadar basit olmalıdır. Kaynak da real-time şartının
admissible estimator sınıfını ciddi biçimde kısıtladığını açıkça vurgular.

Birincil kaynak:
https://www.mathnet.ru/eng/at4683

Tarihî hattın yaklaşık çözümü momentler veya parametrik bir dağılım ailesiyle
sonlu bir state taşımaktır. Bunun darboğazları:

- nonlinear beklentilerin her adımda tekrar hesaplanması;
- moment hiyerarşisinin kapanmaması;
- yaklaşık covariance'ın geçerliliğini kaybetmesi;
- recursion'ın tek-adımlı approximation hatasını büyütmesi;
- non-Gaussian tail ile second moment'in aynı koordinata zorlanması;
- yüksek boyutta conditional table/grid patlamasıdır.

Bu alan “unutulmuş ve kimsenin kullanmadığı” bir alan değildir. Pugaçev
conditionally-optimal filtering hattında autocorrelated observation noise dahil
yeni çalışmalar 2024'te de yayımlanmıştır:
https://www.mathnet.ru/eng/ia920

Dolayısıyla tarihî isim yalnız çıkış ipucudur. R197–R206'da elde edilen mimariyi
“Pugaçev'in kayıp teorisini bulduk” diye sunmak yanlış olur.

---

## 3. Problem ve notasyon

Discrete state-space sistemi düşünelim:

\[
x_{t+1}=f_t(x_t,w_t),
\qquad
y_t=h_t(x_t)+v_t.
\]

Update öncesi elimizde yaklaşık prior

\[
x_t\mid y_{1:t-1}\approx(m_t^-,P_t^-)
\]

olsun. Amaç yalnız bir nokta tahmini değil, şu üç nesneyi rekürsif taşımaktır:

\[
m_t^+\approx E[x_t\mid y_{1:t}],
\qquad
P_t^+\approx\operatorname{Cov}(x_t\mid y_{1:t}),
\qquad
q_{.90}\text{ (tail coordinate)}.
\]

`P` dinamik recursion için second-moment scale'dir. `q_.90` ise coverage için
ayrı bir standardized-residual quantile'dır. Bu ikisinin ayrılması R198'in kritik
değişikliğidir.

---

## 4. Nihai update mimarisi

### 4.1 Analytic chart

Önce observation Jacobian'ı ve innovation hesaplanır:

\[
H_t=\nabla h_t(m_t^-),
\qquad
\nu_t=y_t-h_t(m_t^-).
\]

Online measurement metric tahmini `\widehat R_t` ile

\[
S_t=H_tP_t^-H_t^\top+\widehat R_t,
\qquad
K_t=P_t^-H_t^\top S_t^{-1}.
\]

Tam lineer adım yerine güvenli fraction `\alpha_t\in[0,1]` kullanılabilir:

\[
m_t^0=m_t^-+\alpha_tK_t\nu_t.
\]

Effective gain `\widetilde K_t=\alpha_tK_t` için Joseph covariance:

\[
P_t^0=(I-\widetilde K_tH_t)P_t^-(I-\widetilde K_tH_t)^\top
      +\widetilde K_t\widehat R_t\widetilde K_t^\top.
\]

\[
P_t^0=B_tB_t^\top
\]

Cholesky factorı, learned closure'ın güvenli coordinate chart'ıdır. Analytic
update nihai doğruluk iddiası değildir; learned parçanın üzerinde çalışacağı
geçerli tabanı sağlar.

### 4.2 Whitened conditional problem

Innovation ve analytic posterior hatası normalize edilir:

\[
r_t=S_t^{-1/2}\nu_t,
\qquad
e_t=B_t^{-1}(x_t-m_t^0).
\]

Böylece compiler'ın hedefi doğrudan farklı ölçek ve dönüşlerdeki state'i
öğrenmek değil,

\[
c(r_t,\phi_t)\approx E[e_t\mid r_t,\phi_t]
\]

ve

\[
A(r_t,\phi_t)\approx
\operatorname{Cov}(e_t\mid r_t,\phi_t)
\]

olur. `\phi_t` prior mean, log-Cholesky diagonalı, whitened innovation'ın tekli
ve ikili terimleri, bounded odd transforms ve local Jacobian bilgisini taşır.

Feature sayısı

\[
F(d)=1+7d+\frac{d(d+1)}2+d^2
    =1+\frac{15}{2}d+\frac32d^2
\]

olur. Gözlenen değerler `d=2,4,8` için `22,55,157`dir.

### 4.3 Conditional mean compiler

Offline simulation örneklerinde standardized target `e_i` ve feature `\phi_i`
oluşturulur. İlk ridge pass:

\[
\widehat\Beta_1=
(\Phi^\top\Phi+\lambda I)^{-1}\Phi^\top E.
\]

Residual normlarından gelen bounded ağırlıklarla ikinci ve son pass:

\[
\widehat\Beta=
(\Phi^\top W\Phi+\lambda I)^{-1}\Phi^\top WE.
\]

Deploy'da optimizer yoktur:

\[
\widehat c_t=\phi_t^\top\widehat\Beta,
\qquad
m_t^+=m_t^0+B_t\widehat c_t.
\]

R197 ablation'ı robust ikinci pass'in ana edge olmadığını gösterdi. Ana kazanç,
raw `(m,s,y)` polinomundan whitened conditional geometry'ye geçişti.

### 4.4 Convex PSD atom closure

Training innovation örneklerinde k-means++/Lloyd ile `K=4+2d` merkez keşfedilir.
Her merkez için mean correction sonrası residual outer-product'lar global
covariance'a shrink edilerek

\[
A_k\succeq0
\]

atomları elde edilir. Deploy ağırlıkları pozitif ve normalize edilir:

\[
w_k(r)=
\frac{\exp[-\|r-\mu_k\|^2/(2\tau_k)]}
     {\sum_j\exp[-\|r-\mu_j\|^2/(2\tau_j)]}.
\]

\[
A(r)=\sum_{k=1}^K w_k(r)A_k,
\qquad
P_t^+=B_tA(r_t)B_t^\top.
\]

#### PSD önermesi

`A_k\succeq0`, `w_k\ge0` ve `\sum_kw_k=1` ise

\[
A(r)\succeq0.
\]

Her `z` için

\[
z^\top P_t^+z=(B_t^\top z)^\top A(r_t)(B_t^\top z)\ge0.
\]

Dolayısıyla covariance deploy'dan sonra projection ile “tamir” edilmez; PSD
parametrizasyonun içindedir.

### 4.5 Tail coordinate

Standardized recursive error radius

\[
\rho_t=
\sqrt{(x_t-m_t^+)^\top(P_t^+)^{-1}(x_t-m_t^+)}
\]

ayrı calibration trajectories üzerinde hesaplanır ve `q_.90` alınır. Reported
ellipsoid

\[
\mathcal E_{.90}=
\{x:(x-m_t^+)^\top(P_t^+)^{-1}(x-m_t^+)\le q_{.90}^2\}
\]

olur. `q_.90`, recursion'da kullanılan `P_t^+`yi değiştirmez. Bu nedenle
coverage düzeltmek için covariance'ı şişirip sonraki mean update'lerini bozma
mekanizması ortadan kalkar.

---

## 5. Rekürsif destek kapanışı

R203'te üç iyi görünen varyant boyut büyüdükçe çöktü. Kök neden training prior
üreticisindeki bazı Cholesky koordinatlarının yapısal olarak sıfır olmasıydı.
Recursive transition bu koordinatları doldurunca

\[
\frac{\phi_j-\mu_j}{\sigma_j}
\]

içinde `\sigma_j\approx10^{-8}` olan feature'lar milyon mertebesine çıktı.

Bu deneyden çıkan genel koşul:

> Offline compiler feature desteği, deploy'da tekrar uygulanan prediction-update
> operatörü altında yaklaşık kapalı olmalıdır; değilse coordinate silinmeli,
> yeniden ölçeklenmeli veya learned parça destek dışında kapanmalıdır.

Yaşayan R203 dili yalnız recursion altında destek kazanan kararsız Cholesky
koordinatlarını çıkardı, normalized feature'ları bounded tuttu ve analytic chart'ı
korudu.

Bu koşul yalnız filtering'e özgü değildir. Offline-learned bir operator kendi
çıktısını tekrar input olarak tüketiyorsa tek-adımlı train/test coverage yeterli
değildir; reachable recursive support sınanmalıdır.

---

## 6. R206: bilinmeyen measurement correlation

R204'te dense transition + correlated measurement noise altında d=16 coverage
`0.84291`e düştü. Sorun daha çok atom eklemek değildi; whitening metric'i
`R=\sigma^2I` diye yanlış kuruluyordu.

### 6.1 Innovation residual moment

Prior first two momentleri doğruysa

\[
E[\nu_t\nu_t^\top\mid\mathcal F_{t-1}]
=H_tP_t^-H_t^\top+R_t.
\]

Dolayısıyla

\[
U_t=\nu_t\nu_t^\top-H_tP_t^-H_t^\top
\]

için

\[
E[U_t\mid\mathcal F_{t-1}]=R_t.
\]

R206 clipped EWMA state'i taşır:

\[
M_t=(1-\eta)M_{t-1}
 +\eta\,\operatorname{clip}(U_t/\sigma^2).
\]

Bu eşitlik yalnız **one-step unbiased moment** sonucudur. Approximate recursive
prior kullanıldığında `M_t`nin gerçek `R`ye tutarlı yakınsadığı kanıtlanmamıştır.
Deneyde metric'in filtering'i iyileştirmesi, covariance identification'ın tam
olduğu anlamına gelmez.

### 6.2 Structured compound metric

Tek-parametreli aile:

\[
C(\rho)=(1-\rho)I+\rho\mathbf1\mathbf1^\top.
\]

Eigenvalue'lar

\[
1-\rho\quad(d-1\text{ kez}),
\qquad
1+(d-1)\rho
\]

olduğu için

\[
-\frac1{d-1}<\rho<1
\]

aralığında pozitif definiteness doğrudan korunur. Off-diagonal `M_t`
ortalamasından `\rho_t` çıkarılır, güvenli aralığa kırpılır ve

\[
\widehat R_t=\sigma^2C(\rho_t)
\]

bir sonraki update'te kullanılır. Güncel innovation kendi metric'ini geriye dönük
fit etmez; adaptasyon bir adım gecikmeli ve causaldır.

Bu yol az parametreli olduğu için tek stream'de çalıştı. d=2'de yalnız tek pair
bulunduğundan kazanç güvenilir değildir; fayda özellikle d=8 ve d=16'da çıktı.

### 6.3 General full metric

Arbitrary symmetric `M` önce spectral positive part'a, sonra unit diagonal'a
çekilir:

\[
M=V\Lambda V^\top,
\quad
M_+=V\max(\Lambda,\epsilon I)V^\top,
\]

\[
C=D^{-1/2}M_+D^{-1/2},
\qquad D=\operatorname{diag}(M_+).
\]

Son shrinkage:

\[
\widehat C=(1-\gamma)I+\gamma C
\]

olduğu için `\widehat C\succ0` kalır. Bu map nearest-correlation projection diye
sunulmaz; tek spectral-pass PSD retraction'dır.

Fakat `d(d-1)/2` korelasyonu 55 scored time point'lik tek stream'den çıkarmak
örneklem olarak yetersiz kaldı. Aynı noise modelini paylaşan 20 paralel stream
üzerinden ortak moment tutulduğunda signed rank-one yapı çalıştı. Bu sonuç çok
önemlidir:

> PSD parametrizasyon validity'yi çözer; identifiability ve sample complexity'yi
> çözmez.

---

## 7. R206: bounded nonlinear anchor

True measurement covariance verilmiş olsa bile d=16, güçlü cubic, seed-2
vakasında ilk EKF correction bir koordinatta `13.55` birim sıçradı. Learned
reliability o anda yaklaşık sıfırdı; yani çöküş learned mean'den değil analytic
anchor'dan geliyordu.

Linear ray üzerinde sabit aday kümesi seçildi:

\[
\mathcal A=\{0,1/16,1/8,1/4,1/2,3/4,1\}.
\]

Her `\alpha` için nonlinear local posterior objective:

\[
J_t(\alpha)=
(\alpha K_t\nu_t)^\top(P_t^-)^{-1}(\alpha K_t\nu_t)
+[y_t-h_t(m_t^-+\alpha K_t\nu_t)]^\top
\widehat R_t^{-1}
[y_t-h_t(m_t^-+\alpha K_t\nu_t)].
\]

Riskli olmayan update'te doğrudan `\alpha=1` kullanılır. Riskli update'te

\[
\alpha_t=\arg\min_{\alpha\in\mathcal A}J_t(\alpha).
\]

#### Güvenlik önermesi

`0\in\mathcal A` olduğu için

\[
J_t(\alpha_t)\le J_t(0).
\]

Bu global posterior optimum garantisi değildir; fakat seçilen ray üzerinde
prior noktasından daha kötü local objective alınmamasını garanti eder.

Aynı risk sinyali learned correction ve learned covariance atomlarını sürekli
olarak kapatır; limitte update Joseph analytic chart'a döner. Exact failure
izinde bu mekanizma update'lerin yalnız `0.0714%`'ünde açıldı, çöküşü kaldırdı ve
RMSE `0.17888` oldu.

---

## 8. Round-by-round gelişim

### R197 — tek-adımlı compiler

- 18 home case'in tamamında 2,048-sample posterior oracle'ın %12 RMSE bandı;
- non-Gaussian home'da EKF ve UKF'ye karşı `12/12`;
- raw degree-4 polynomial regression'a karşı `18/18`;
- açık problem: recursive variance/shape closure.

### R198 — recursive mean, scale ve tail ayrımı

- 30 case;
- home non-Gaussian'da UKF ve EKF'ye karşı `10/10`;
- home case'lerde particle512'nin %15 bandında `15/15`;
- home coverage `0.90037`;
- particle'a median hızlanma `54.25×`;
- açık problem: multivariate covariance ve shift-tail.

### R202 — 2D whitened PSD closure

- 40 case;
- mixture home ve shift'te UKF'ye karşı `20/20` toplam;
- home particle RMSE'nin %15 bandında `20/20`;
- home coverage `0.90278`;
- particle512'ye median hızlanma `31.6×`;
- açık problem: elle `10×10` innovation grid'i ve boyut patlaması.

### R203 — otomatik PSD atom dili

- `d=2,4,8`, 36 case;
- mixture home+shift'te UKF'ye karşı `18/18`;
- home particle'ın %20 bandında `18/18`;
- coverage yaklaşık `0.895–0.906`;
- d=8'de 20 atom ve 24,240 byte model;
- 10-bin Cartesian covariance grid'ine karşı `5,000,000×` atom-storage
  azalması;
- üç recursive support varyantı reddedildikten sonra yaşayan dil bulundu.

### R204 — ikinci tur stress ve ablation

- `d=2,4,8,16`, 144 case;
- mixture üç domain'de UKF'ye karşı `72/72`;
- home particle512'nin %20 bandında `48/48`;
- learned-mean ablation `24/24` mixture-home;
- d=16: 36 atom, 151,344 byte;
- bütün covariance'lar PSD;
- açık koordinat: dense correlated shift altında d=16 coverage `0.84291`;
- conditional covariance atomlarının d=16'da global atoma keskinlik avantajı
  kalmadı.

### R206 — adaptive metric ve güvenli anchor

128 case, toplam 179,200 recursive update:

| Grup | Legacy RMSE | Structured RMSE | Shared-full RMSE | True-metric RMSE |
|---|---:|---:|---:|---:|
| independent | 0.20746 | 0.21058 | 0.20990 | 0.20922 |
| equicorrelated | 0.21866 | 0.20906 | 0.20724 | 0.20610 |
| signed rank-one | 0.21956 | 0.22194 | 0.20958 | 0.20789 |

| Grup | Legacy coverage | Structured coverage | Shared-full coverage | True-metric coverage |
|---|---:|---:|---:|---:|
| independent | 0.90082 | 0.88955 | 0.88466 | 0.89903 |
| equicorrelated | 0.85793 | 0.88736 | 0.88572 | 0.86710 |
| signed rank-one | 0.85659 | 0.83943 | 0.88528 | 0.87767 |

Yorum:

- structured aile doğru olduğunda tek-stream adaptation işe yarıyor;
- signed yapı compound model tarafından temsil edilemiyor ve beklenildiği gibi
  yaşamıyor;
- full shared metric signed yapıda legacy'yi RMSE bakımından `27/32`, nominal
  coverage'a yakınlıkta `26/32` case'te geçti;
- unrestricted full-local varyant undercoverage nedeniyle reddedildi;
- true metric bile her zaman nominal coverage vermiyor, çünkü tail quantile ve
  residual atomları independent training dağılımında derlenmiştir;
- online metric bazen true correlation'ı eksik tahmin ederken daha konservatif
  covariance üretiyor. Bu yüzden sonuç “R doğru identify edildi” diye okunamaz.

Runtime microbenchmark'ında 1,400 update için:

| d | Legacy | Compound | Full-shared | Compound / legacy | Full / legacy |
|---:|---:|---:|---:|---:|---:|
| 2 | 0.0187 s | 0.0274 s | 0.0294 s | 1.46× | 1.57× |
| 4 | 0.0320 s | 0.0478 s | 0.0495 s | 1.50× | 1.55× |
| 8 | 0.1733 s | 0.2271 s | 0.2358 s | 1.31× | 1.36× |
| 16 | 0.8776 s | 1.0648 s | 1.0631 s | 1.21× | 1.21× |

---

## 9. Negatif sonuçlar ve nedenleri

1. **Raw polynomial compiler:** aynı degree'de whitened conditional basis'ten
   kötüydü. Sorun kapasite değil koordinattı.
2. **Second moment eksi learned mean-square:** subtraction/cancellation recursive
   covariance'ı bozdu; coverage ancak dev elipslerle sağlandı.
3. **Cartesian innovation grid:** `10^d` atom üretti; d büyümesine kapalıydı.
4. **Dense learned mean:** recursive feedback d=4 ve d=8'de patladı.
5. **Learned covariance replacement:** sonraki gain'leri training dışına itti.
6. **Support-unstable Cholesky feature'ları:** offline structural zero, online
   nonzero olduğu için normalization patladı.
7. **Conditional atoms d=16:** global atomdan daha keskin değildi; atom sayısını
   artırmak çözüm diye kabul edilmedi.
8. **Full correlation / one short stream:** PSD kaldı ama yanlış correlation
   öğrenerek undercoverage üretti. Validity, statistical adequacy değildir.
9. **Ungated true-metric analytic anchor:** doğru `R` bile güçlü nonlinear
   observation'da EKF overshoot'u engellemedi.
10. **Gaussian home:** learned mean'in klasik sigma-point filtreye karşı genel
    edge'i yoktur. Edge non-Gaussian/outlier conditional geometry'dedir.

---

## 10. Literatür çarpışması ve yenilik sınırı

### Adaptive covariance

Innovation veya residual statistics'ten bilinmeyen `Q/R` öğrenmek yeni değildir.
Sage ve Husa 1969'da unknown prior statistics için adaptive Bayes filtreleri
geliştirdi:
https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/AD703954.xhtml

Mehra 1970'te unknown process ve measurement covariance identification ile
adaptive Kalman filtering'i doğrudan ele aldı:
https://doi.org/10.1109/TAC.1970.1099422

Bu nedenle R206 residual-moment update'i tek başına novelty değildir.

### Learned/hybrid filters

KalmanNet, model-based Kalman akışında gain'i RNN ile öğrenir ve unknown second
moments'i implicit state içinde takip eder:
https://arxiv.org/abs/2107.10043

ML-EnCMF, conditional mean'in projection özelliğinden yararlanarak machine
learning ile conditional mean update'i kurar ve posterior mean/covariance
ilişkisini inceler:
https://arxiv.org/abs/2106.07908

Dolayısıyla “conditional mean'i datadan derlemek” tek başına novelty değildir.

### Covariance regression

Covariance'ı predictor'a bağlı ve yapısal olarak PSD parametrize etmek geniş bir
alandır. Hoff–Niu modeli örneğin

\[
\Sigma_x=A+Bxx^\top B^\top
\]

ile positive-definiteness'i yapıya gömer:
https://doi.org/10.5705/ss.2010.051

Convex PSD atom fikri bununla aynı formül değildir, fakat aynı geniş prior-art
ailesi içindedir.

### Dürüst novelty hükmü

Şu anda savunulabilecek iddia:

> Whitened analytic chart + fixed-pass conditional mean compiler + convex PSD
> residual atoms + separate recursive tail + support closure + adaptive metric +
> bounded nonlinear fallback birleşimi, bu laboratuvarda çalışan ve kapsamı
> ölçülmüş bir mimaridir.

Savunulamayacak iddia:

> Bu bileşim literatürde kesinlikle ilk, genel optimal veya mevcut learned/
> assumed-density/adaptive filters'dan üstündür.

Yayın iddiasından önce daha dar bir theorem statement, güncel baseline
implementasyonları ve systematic prior-art review gerekir.

---

## 11. Neyi çözdük, neyi çözmedik?

### Çözülen scoped kabiliyet

- test edilen nonlinear/non-Gaussian ailede pahalı conditional update deploy'da
  fixed-pass hale geldi;
- recursive mean ve uncertainty birlikte taşındı;
- covariance bütün testlerde PSD kaldı;
- d=16'ya kadar Cartesian patlama kaldırıldı;
- düşük-parametreli unknown correlation online adapte edildi;
- genel correlation yeterli shared sample varsa kullanılabildi;
- catastrophic nonlinear anchor failure otomatik ve seyrek fallback ile
  engellendi;
- hangi bileşenin nerede fayda sağlamadığı ablation ile ayrıldı.

### Çözülmeyenler

- arbitrary nonlinear dynamics/observation için theorem-level error bound;
- approximate-prior altında online `R_t` estimator consistency;
- tek kısa stream'den arbitrary full correlation identification;
- latent/discrete regime switching;
- gerçek sensör izi ve sim-to-real transfer;
- universal dimension-independent compiler;
- KalmanNet, ML-EnCMF, Gaussian-sum, ensemble ve modern amortized filters'a karşı
  aynı benchmark üzerinde karşılaştırma;
- global novelty ve patentability.

Bu maddeler projenin “yarım kaldığı” anlamına gelmez. Bunlar başka bir araştırma
veya ürün doğrulama projesinin başlangıç koşullarıdır. Mevcut teori hattı,
iddiasını daha fazla genişletmeden burada kapanmıştır.

---

## 12. Yeniden üretim ve bağımsız kontrol

Ana dosyalar:

- `R197_THEORY_BOTTLENECK_PORTFOLIO_WAVE2/theory_wave2.py`
- `R198_PUGACHEV_RECURSIVE_MOMENT_CLOSURE/recursive_closure.py`
- `R202_PUGACHEV_MULTIVARIATE_WHITENED_CLOSURE/multivariate_closure.py`
- `R203_PUGACHEV_AUTOMATIC_PSD_ATOM_LANGUAGE/automatic_psd_closure.py`
- `R204_PUGACHEV_PSD_CLOSURE_STRESS/stress_suite.py`
- `R206_PUGACHEV_ADAPTIVE_INNOVATION_METRIC/adaptive_metric.py`
- `R206_PUGACHEV_ADAPTIVE_INNOVATION_METRIC/third_pass.py`
- `R206_PUGACHEV_ADAPTIVE_INNOVATION_METRIC/runtime_benchmark.py`

Nihai sonuç dosyaları:

- `R204_RESULT.json`: 144-case ikinci tur;
- `R206_RESULT.json`: 128-case correlation/failure-boundary turu;
- `R206_RUNTIME.json`: runtime microbenchmark;
- `R206_DECISION.json`: kısa hüküm;
- bu rapor: bütün bağlam ve matematik.

Nihai status:

`PUGACHEV_INSPIRED_COMPILED_CLOSURE_SCOPED_PROJECT_COMPLETE`
