# R210 — İkinci Tur Teori Kapanışı

## 1. GDR thinning tomography: exact identifiability neden stable recovery değildir?

R209'da bounded cluster intensities `mu_1,...,mu_K` için log-void observation
operator'ü çıkarılmıştı:

```text
F_mu(p) = -log P(N_p=0)
        = sum_{s=1}^K mu_s [1-(1-p)^s],       0<=p<=1.
```

Distinct `K` retention noktası noiseless durumda `mu`'yu tanımlar. R210 sorusu
hangi `p_i` tasarımının bu inverse problemi stable yaptığıydı.

### 1.1 Bütün retention tasarımlarını geçen kör yön

`K=2r` olsun. Cluster-size coefficient perturbation'ını yalnız
`s=r,...,2r` üzerinde tanımla:

```text
delta_{r+j}=(-1)^j C(r,j),      j=0,...,r.
```

Binomial identity ile:

```text
sum_s delta_s = 0,

F_delta(p)
= sum_{j=0}^r (-1)^j C(r,j)[1-(1-p)^(r+j)]
= -(1-p)^r sum_{j=0}^r (-1)^j C(r,j)(1-p)^j
= -(1-p)^r p^r.
```

Bu eşitlik seçilmiş probe noktalarına değil **bütün `p in [0,1]` aralığına**
aittir. Maximum ayrım:

```text
sup_p |F_delta(p)| = 4^(-r) = 2^(-K),
```

çünkü maximum `p=1/2`'dedir. Öte yandan:

```text
||delta||_1 = sum_j C(r,j)=2^r.
```

Dolayısıyla void-curve inverse operator için L1 amplification en az:

```text
||delta||_1 / ||F_delta||_infinity
= 2^r / 2^(-K)
= 2^(3K/2).
```

Bu yalnız signed ve fizik dışı bir yön değildir. Her bileşende
`b_s=|delta_s|+a`, `a>0` alıp:

```text
mu^+ = b+delta,      mu^- = b-delta
```

yazılırsa iki spectrum da nonnegative'dir. Aralarındaki L1 mesafe büyükken
log-void eğrileri exponential ölçüde yakındır.

### 1.2 Daha güçlü eşleşme

Finite-difference identity nedeniyle:

```text
sum_s delta_s s^ell = 0,       ell=0,...,r-1.
```

Yani iki nonnegative spectrum yalnız total cluster intensity'de değil ilk
`r-1` raw cluster-size momentinde de aynıdır. Kör yön, basit mean/variance
ambiguity'sinden daha güçlüdür.

### 1.3 Executable witness

`K=12, r=6` için:

- spectrum L1 mesafesi: `128`;
- bütün retention aralığında maximum log-void curve farkı: `0.00048828125`;
- inverse amplification lower bound: `262,144`;
- moment degrees `0,...,5`: exact zero fark.

Çift `K=4,6,...,20` için lower bound sırasıyla
`64, 512, 4096, ..., 1,073,741,824` büyüdü; tam olarak `2^(3K/2)`.

### 1.4 Karar

Bu sonuç R209'daki “daha iyi retention noktaları bulalım” yönünü kapatır.
Full finite spectrum'u noisy **void-only real thinning** altında stable ve
uniform biçimde çıkarmak mümkün değildir; problem design hatası değil moment
inversion yapısıdır.

Tutulabilecek daha dar nesneler:

- düşük-order aggregate/factorial moments;
- önceden küçük olduğu bilinen `K`;
- smooth/sparse/parametric cluster spectrum;
- void dışında count histogram veya cluster-sensitive observation.

Bunlar yeni problemdir. R210 full-spectrum iddiasını kurtarmak için varsayım
eklemeyecektir.

## 2. Zhuravlev: affine corrector'dan bounded-degree compiler'a

R209 yalnız XOR/affine corrector'ı çözmüştü. Base recognition output'ları
`h_1,...,h_m in GF(2)^n` olsun. Degree `d` square-free Boolean monomial dili:

```text
Phi_d = { product_{j in S} h_j : S subset {1,...,m}, |S|<=d }.
```

Feature sayısı:

```text
M_d(m)=sum_{s=0}^d C(m,s).
```

Target control error vector `t` degree-`d` corrector ile temsil edilebiliyorsa
ve ancak şu sistem çözülebiliyorsa:

```text
Phi_d c = t  (mod 2).
```

Bu nedenle fixed `d` altında representability polynomial-time linear algebra
ile compile edilir; sistem inconsistent ise exact abstention vardır. `d=m`
olduğunda dil `2^m` boyuta döner ve genel Boolean algebra'nın üstel tavanı geri
gelir.

### 2.1 Empirical generator quotient

Control sample üzerinde base columns'ın GF(2) rank'ı `r<m` ise `r` generator
seçilebilir. Her `h_j` bu generator'ların linear combination'ıdır. En fazla `d`
linear formun çarpımı yine generator'larda degree en fazla `d` polynomial'dir.
Dolayısıyla exact control-sample feature space:

```text
rank(Phi_d(h_1,...,h_m)) <= M_d(r).
```

Bu `m` yerine empirical algebra generator rank'ını kullanan exact quotient'tır.

### 2.2 Executable witness

- 300 control row ve 18 base algorithm;
- affine features: 19, rank 19, planted target temsil edilemedi;
- quadratic features: 172, rank 172, aynı target exact temsil edildi;
- dependent 17 raw generator'ın rank'ı 8 olduğunda raw quadratic count 154,
  quotient upper bound 37 oldu.

Ancak `m=40` için feature counts:

```text
d=1: 41
d=2: 821
d=3: 10,701
d=4: 102,091
d=5: 760,099.
```

### 2.3 Collision ve generalization sınırı

Boolean function'ların GF(2) algebraic normal form'u ve bounded-degree
evaluation spaces Reed–Muller code cebrinin standart nesneleridir. Bu nedenle
compiler özdeşliği yeni matematik iddiası taşımaz. Örnek kaynaklar:

- Zhuravlev control-sample corrector:
  https://www.mathnet.ru/eng/zvmmf5406
- Boolean polynomial/ANF:
  https://cis.temple.edu/~beigel/papers/bb-fourier-ijfcs.html
- GF(2) sparse polynomial interpolation:
  https://epubs.siam.org/doi/10.1137/0220019

Daha önemlisi, `rank(Phi_d)=n` olduğunda her control target interpolated
edilebilir. Exactness bu noktada öğrenme değil ezberdir. Off-sample yapıyı
koruyan ek invariant olmadan Zhuravlev corrector genişlemesi yeni bir learner
değildir.

## 3. R210 sonucu

| Aday | İkinci-tur hükmü |
|---|---|
| GDR thinning tomography | Full-spectrum, void-only güçlü biçimi `2^(3K/2)` inverse amplification lower bound ile öldü |
| Zhuravlev bounded-degree corrector | Scoped exact compiler var; fixed-degree polynomial, unbounded-degree exponential; ANF/Reed–Muller collision güçlü |

R209'un iki liderinden hiçbiri breakthrough eşiğini geçmedi. Buna rağmen iki
kalıcı çıktı vardır: bir **impossibility boundary** ve bir **compile-or-abstain
bounded-degree theorem**. Yeni aday dalgası bunları ürün diye zorlamadan devam
etmelidir.

