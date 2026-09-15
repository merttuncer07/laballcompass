# R202 freeze frontier ve yön-korumalı devam kaydı

## Dondurulan an

R199–R202 tamamlandı, testler geçti ve `R192.../CANDIDATE_MAP.md` R202'ye kadar
güncellendi. Bu noktada ürün seçilmiyordu. Çalışma, yüksek tavanlı survivor'ların
açık teorik koordinatlarını sırayla kırma aşamasındaydı.

## Freeze öncesi belirlenmiş sıradaki iş

Bir sonraki doğal araştırma hedefi R202'nin şu iki sınırıydı:

1. 2D innovation grid'inin `d>2` iken üstel hücre patlaması;
2. PSD covariance atom/hücre dilinin elle verilmesi.

Yani resume, bu raporlardan yeni ürün fikri çıkarmakla veya eski bütün adayları
yeniden sıralamakla başlamaz. İlk ucuz test, Cartesian grid yerine boyutla üstel
büyümeyen, positive-semidefinite kalmayı parametrizasyon içinde garanti eden bir
conditional-residual representation denemesidir.

## İlk R203 hipotezi için minimum sözleşme

- `d=2` sonucunu bozmadan `d=4` ve mümkünse `d=8`e taşınmalı.
- Temsil belleği `b^d` olmamalı; açıkça ölçülmeli.
- Covariance her update'te PSD olmalı; sonradan sadece eigenvalue clip etmek ana
  mekanizma sayılmamalı.
- Mean RMSE, %90 coverage ve elips keskinliği birlikte geçmeli.
- Gaussian başarı tek başına yetmez; non-Gaussian home ve dynamics/observation
  shift birlikte test edilmeli.
- UKF/EKF ve doğru noise modelini bilen particle baseline kalmalı.
- Eğer representation yalnız mean'i koruyup uncertainty'yi şişiriyorsa aday
  ölür; R202'nin ilk başarısız covariance varyantı tekrarlanmaz.

## Freeze raporlarının yön yetkisi yoktur

`01` ve `02` dosyalarının görevi hatırlatmak ve taşınabilirliktir. İçlerindeki
potansiyel kullanım alanları research priority değildir. Resume sırasında karar,
R202 öncesinde seçilmiş yukarıdaki bottleneck ve yeni deney sonuçlarıyla verilir.

