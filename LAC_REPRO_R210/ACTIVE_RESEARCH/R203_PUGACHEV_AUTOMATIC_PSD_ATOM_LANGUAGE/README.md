# R203 — Pugaçev closure için otomatik PSD atom dili

## Soru

R202'nin iki açık darboğazı birlikte hedeflendi:

1. `10^d` büyüyen elle kurulmuş innovation hücreleri `d > 2` için kullanılabilir
   mi?
2. Hücre dilini araştırmacı seçmeden, veriden keşfedilen küçük bir dil PSD
   garantisini ve rekürsif doğruluğu koruyabilir mi?

Bu round ürün tasarlamadı. R202'nin conditional-moment closure teorisini 2, 4 ve
8 boyuta taşıyan en ucuz ayrım deneyini yaptı.

## Yaşayan cebir

Önce analytic linear update Joseph formunda hesaplanıyor:

`P0 = (I-KH) P (I-KH)^T + K R K^T = B B^T`.

Bu update nihai model olarak kabul edilmiyor; öğrenilmiş closure'ın koordinat
chart'ı oluyor. Mean ve residual covariance şu biçimde derleniyor:

`m+ = m + K(y-h(m)) + B c(phi)`

`P+ = B [sum_k w_k(r) A_k] B^T`.

- `r`, whitened innovation;
- `c(phi)`, iki sabit ridge pass'inde derlenen conditional residual mean;
- merkezler, whitened innovation örneklerinde k-means++/Lloyd ile keşfedilen
  Voronoi prototipleri;
- `w_k`, prototip uzaklıklarından gelen pozitif ve toplamı bir soft ağırlıklar;
- `A_k`, residual outer-product'lardan global covariance'a shrink edilen PSD
  atomlar.

Her `A_k` PSD ve ağırlıklar simplex üzerinde olduğu için karışım PSD'dir;
`B (.) B^T` congruence'ı bunu state koordinatında korur. Böylece projection ile
sonradan tamir edilen covariance değil, parametrizasyon gereği geçerli covariance
elde edilir.

## Kritik keşif: rekürsif destek kapanışı

İlk üç varyant başarısız oldu. Kök neden, offline prior üreticisinde uzak
Cholesky alt-köşegenlerinin yapısal olarak sıfır olmasıydı. Rekürsif transition
bu koordinatları doldurunca eğitim standart sapması `1e-8` olan feature'lar
milyon mertebesine çıktı ve mean correction patladı. Coverage kalibrasyonu büyük
elipslerle bu hatayı gizleyebiliyordu.

Yaşayan varyant:

- bu destek-kararsız Cholesky koordinatlarını feature dilinden çıkarır;
- analytic posterioru güvenli chart olarak korur;
- normalized compiled feature'ları açık bir `[-8, 8]` trust bound içinde tutar;
- covariance'ı elle eksenlenmiş grid yerine otomatik Voronoi atomlarıyla taşır.

Bu yalnız bir tuning düzeltmesi değildir: **offline feature desteğinin uygulanan
rekürsif operatör altında kapalı olması gerektiğini** deneysel bir tasarım
koşuluna dönüştürür.

## İlk-pass deney

- boyutlar: `d = 2, 4, 8`;
- Gaussian ve bimodal/heavy-tail process + mixture measurement noise;
- home ve daha kalıcı transition/daha kuvvetli cubic shift;
- `3 seed × 3 dimension × 2 regime × 2 domain = 36` case;
- case başına `28 × 50 = 1,400` recursive update;
- EKF, pozitif-ağırlıklı UKF ve doğru noise likelihood kullanan 384-particle
  filter;
- RMSE yanında %90 coverage, ellipsoid RMS semi-axis, PSD eigenvalue, memory ve
  runtime zorunlu ölçüldü.

## Sonuç

Tüm önceden yazılmış kapılar geçti:

- d=2/4/8 home coverage: `0.8975 / 0.9057 / 0.8950`;
- home per-coordinate RMSE: `0.2043 / 0.2052 / 0.2050`;
- home UKF RMSE: `0.2292 / 0.2299 / 0.2305`;
- home particle RMSE: `0.1997 / 0.2040 / 0.2349`;
- bütün home case'lerinde particle'ın %20 içinde: `18/18`;
- mixture home+shift'te UKF galibiyeti: her boyutta `6/6`, toplam `18/18`;
- Gaussian rejimde edge iddiası yok: compiled closure UKF'den yaklaşık `0.006`
  per-coordinate RMSE daha kötü;
- deployed covariance minimum eigenvalue bütün caselerde pozitif;
- d=8: 20 otomatik atom, model en fazla 24,240 byte;
- d=8 atom covariance depolaması, 10-bin Kartezyen dile göre `5,000,000×`
  küçük;
- 384-particle'a median deploy hızlanması boyuta göre `5.55×–7.01×`.

Hüküm:

`AUTOMATIC_PSD_ATOM_LANGUAGE_SURVIVES_FIRST_PASS`

## Ne kanıtlanmadı

- 384-particle d=8'de mutlak Bayes oracle değildir ve degeneracy yaşayabilir.
- 16+ boyut, farklı observation topology'si ve sensor-correlated noise henüz
  sınanmadı.
- Atom sayısının `4+2d` seçimi optimal değildir.
- Voronoi dili ile güncel mixture/ensemble/amortized filtering literatürü arasında
  novelty collision audit yapılmadı.
- Bu sonuç gerçek sensör izi veya ürün doğrulaması değildir.

## Tekrar üretim

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\automatic_psd_closure.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s . -p 'test_*.py' -v
```

