# R202 — Pugaçev çok-değişkenli whitened recursive closure

## Sorduğumuz soru

R197–R198'deki sabit-pass conditional-moment fikri skaler durumda çalıştı. Açık
darboğaz, aynı closure'ın korelasyonlu bir durum ve ölçüm uzayında covariance'ı
bozmadan rekürsif taşınıp taşınamayacağıydı. Bu round ürüne zorlamadı; doğrudan
bu teorik koordinatı sınadı.

## Cebir değişikliği

Prior covariance için `P = L L^T`, lokal innovation covariance için
`S = C C^T` yazıldı. Durum hatası ve innovation sırasıyla

`e = L^-1 (x-m)` ve `r = C^-1 (y-h(m))`

koordinatlarına alındı. Sabit feature map'i deploy sırasında `E[e|r,...]`
correction'ını tek matris çarpımıyla veriyor; sonuç `m + L correction` olarak
orijinal koordinata dönüyor. Bu, dönüş ve ölçek bilgisini ayrı ayrı öğrenmek
yerine ortak whitened problem üzerinde öğreniyor.

İlk deneme `E[ee^T] - E[e]E[e]^T` formunu lineer olarak derledi. Mean RMSE iyi
olmasına rağmen rekürsif subtraction covariance'ı çökertti: nominal %90 kapsama
ancak ortalama `11.95` state-unit elips yarıçapıyla sağlandı. Bu varyant
reddedildi.

Yaşayan mutasyon, innovation düzlemini küçük hücrelere ayırıyor ve her hücrede
conditional residual outer-product'u global PSD covariance'a doğru shrink ediyor.
Deploy covariance'ı bu PSD atom sözlüğünden seçiliyor. Böylece:

- positive-definiteness parametrizasyonun içinde kalıyor;
- ikinci momentten mean-square çıkarma cancellation'ı yok oluyor;
- full particle posterior deploy sırasında gerekmiyor;
- sözlük yalnız `10 × 10` adet `2 × 2` atom tutuyor.

Bu hücre dili henüz otomatik keşfedilmiş değildir; ikinci turda kırılması gereken
bir başka koordinattır.

## Deney

- 2-boyutlu, bağlı nonlinear dinamik;
- cubic ve cross-coordinate ölçüm;
- Gaussian ve bimodal/heavy-tail process + mixture measurement noise;
- home ve değişmiş transition/cubic shift;
- `10 seed × 2 noise regime × 2 domain = 40` bağımsız case;
- case başına `55 × 58 = 3,190` rekürsif state update;
- karşılaştırmalar: EKF, UKF, doğru noise likelihood kullanan 512-particle filter;
- karar: yalnız RMSE değil, %90 coverage ve elips keskinliği de zorunlu.

## Sonuç

`R202_RESULT.json` içindeki toplu sonuç:

- mixture home: compiled closure UKF ve EKF'yi `10/10` seed geçti;
- mixture shift: UKF'yi `10/10` seed geçti;
- bütün home case'leri: particle RMSE'nin %15 içinde `20/20`;
- ortalama home vector RMSE: compiled `0.29265`, UKF `0.33016`, particle `0.28791`;
- ortalama home coverage: `0.90278`;
- ortalama %90 RMS semi-axis: compiled `0.43872`, UKF `0.49967`, particle `0.42476`;
- median deploy hızlanması: 512-particle'a karşı `31.6×`.

Gaussian rejimde compiled mean UKF'yi sistematik biçimde geçmiyor; yaklaşık aynı
seviyede. Edge özellikle modelin Gaussian olmadığı durumda çıkıyor. Dolayısıyla
doğru hüküm “genel nonlinear filtering çözüldü” değil, aşağıdaki scoped hükümdür.

## Hüküm

`WHITENED_MULTIVARIATE_RECURSIVE_CLOSURE_SURVIVES`

R198'de açık kalan **çok-değişkenli transfer darboğazı**, test edilen 2D ailede
kırıldı. Mean closure, PSD uncertainty ve rekürsif tail kalibrasyonu birlikte
ayakta kaldı. Bu novel/breakthrough kararı değildir; assumed-density filtering,
conditional density estimation ve amortized filter literatürüyle collision audit
gerekiyor.

## Açık koordinatlar

- `d > 2` iken atom sözlüğünün boyut patlaması;
- innovation hücrelerinin elle seçilmesi;
- ayrı latent/discrete regime;
- daha sert transition ve observation misspecification;
- gerçek fizik/sensör trace'i;
- ensemble, Gaussian-sum ve öğrenilmiş amortized baselines;
- offline compile maliyeti ve yeniden kalibrasyon sıklığı;
- novelty/collision audit.

## Kaynak izi

Tarihî çıkış noktası Pugaçev'in conditionally optimal nonlinear filtering
çalışmasıdır: https://www.mathnet.ru/eng/at4683 . Round tarihî ismi novelty
kanıtı olarak kullanmaz; çalışan şey burada yazılan whitened coordinate ve PSD
conditional-residual dictionary birleşimidir.

## Tekrar üretim

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\multivariate_closure.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s . -p 'test_*.py'
```
