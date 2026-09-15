# R206 — Pugaçev hattının kapanışı: adaptive innovation metric ve güvenli nonlinear anchor

## Sonuç

R197'de başlayan Pugaçev-esinli conditional-moment compiler hattı bu round ile
ayrı bir araştırma paketi olarak kapatıldı. Sonuç genel nonlinear filtering
çözümü veya kanıtlanmış literatür yeniliği değildir. Elde edilen şey, kapsamı ve
başarısızlık sınırları açık bir rekürsif filtre mimarisidir:

- analytic prediction/update çekirdeği;
- whitened koordinatta önceden derlenmiş conditional mean düzeltmesi;
- convex PSD atom sözlüğüyle conditional covariance;
- recursion'dan ayrılmış tail calibration;
- structured veya shared-sample online measurement-correlation adaptation;
- destek dışında learned parçayı kapatan ve aşırı nonlinear analytic adımı
  sınırlayan bounded-ray fallback.

Tam matematik, round geçmişi, deneyler ve collision sınırı:

`PUGACHEV_THEORY_REPORT.md`

## R206 üçüncü tur

Frozen deney:

- boyutlar `2, 4, 8, 16`;
- 4 seed;
- Gaussian ve heavy-tail/outlier mixture;
- bağımsız home, dense equicorrelation `rho=.32`, daha sert equicorrelation
  `rho=.55`, işaretleri birbirini götüren rank-one correlation;
- toplam 128 case, case başına `20 × 70 = 1,400` rekürsif update;
- legacy diagonal closure, structured single-stream adaptation, unrestricted
  single-stream adaptation, shared-stream full adaptation, true-metric oracle,
  diagonal/oracle UKF karşılaştırmaları.

Ana sonuçlar:

- bütün güvenli varyantlarda `128/128` finite ve PSD;
- equicorrelated grupta legacy RMSE `0.21866`, structured adaptation `0.20906`,
  shared-full `0.20724`, true-metric closure `0.20610`;
- equicorrelated grupta coverage `0.85793 -> 0.88736` (structured);
- signed rank-one grupta legacy RMSE `0.21956`, shared-full `0.20958`,
  true-metric closure `0.20789`;
- signed grupta shared-full RMSE `27/32`, coverage-distance `26/32` case'te
  legacy'den iyi;
- unrestricted full correlation tek kısa akışta undercoverage üretti
  (`0.81206` equicorrelated, `0.80906` signed): bu varyant reddedildi;
- strong-cubic d=16 seed-2 vakasında ungated true-metric anchor `LinAlgError`
  ile çöktü; bounded-ray + support fallback aynı izi finite bitirdi ve yalnız
  update'lerin `0.0714%`'ünde açıldı;
- online metric maliyeti son 1,400-update ölçümünde d=16'da legacy'nin yaklaşık
  `1.21×`ı.

## Doğru hüküm

`PUGACHEV_INSPIRED_COMPILED_CLOSURE_SCOPED_PROJECT_COMPLETE`

Structured correlation düşük parametreli olduğunda tek akıştan adaptasyon
çalışıyor. Serbest korelasyon için kısa tek akış yeterli değil; aynı sensör
istatistiğini paylaşan çoklu akış veya ayrı calibration gerekiyor. Bu sınır
gizlenmedi ve yeni aday listesine taşınacak bir “daha çok tuning” işi değildir.

## Tekrar üretim

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\third_pass.py 4
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\runtime_benchmark.py
```
