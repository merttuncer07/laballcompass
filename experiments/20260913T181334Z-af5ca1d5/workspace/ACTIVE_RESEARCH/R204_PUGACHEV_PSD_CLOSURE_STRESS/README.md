# R204 — otomatik PSD closure ikinci tur stress ve ablation

## Amaç

R203'ün ilk-pass galibiyetini daha çok seed ile tekrar etmek yeterli değildi.
İkinci tur üç ayrı itirazı ayırdı:

1. boyut büyüdüğünde otomatik atom dili gerçekten ölçekleniyor mu (`d=16`)?
2. sonuç yalnız home topology ve bağımsız measurement noise'a mı ait?
3. kazancı PSD chart mı, learned mean mi, yoksa koşullu atomlar mı getiriyor?

## Frozen test

- boyutlar: `2, 4, 8, 16`;
- seed: 6;
- noise: Gaussian ve bimodal/heavy-tail + outlier mixture;
- domain:
  - home;
  - daha kalıcı transition + daha kuvvetli cubic + daha büyük process noise;
  - eğitimde görülmeyen dense stable transition + `%32` eş-korelasyonlu
    measurement noise;
- toplam `4 × 6 × 2 × 3 = 144` case;
- case başına 22 trajectory × 58 recursive update;
- baselines: EKF, positive-weight UKF, 512-particle;
- ablations:
  - tek global covariance atomu;
  - identity/Joseph atomu;
  - learned nonlinear mean kapalı.

Her covariance varyantının tail radius'u aynı tür bağımsız home calibration iziyle
yeniden kalibre edildi. Böylece büyük covariance veya büyük tail radius ile sahte
coverage kazanımı, RMS semi-axis ölçüsüyle ayrıldı.

## Sonuç

Önceden yazılan dokuz kapının tamamı geçti:

- home coverage, stress coverage, sharpness;
- particle yakınlığı;
- mixture-vs-UKF;
- learned-mean ablation;
- conditional-atom ablation;
- PSD;
- scaling.

Toplu güçlü sonuçlar:

- mixture, bütün boyut ve üç domain'de UKF'yi `72/72` geçti;
- home case'lerde 512-particle RMSE'nin %20 içinde `48/48`;
- mixture-home'da learned mean kapalı varyantı `24/24` geçti;
- deployed minimum covariance eigenvalue her case'te pozitif;
- d=16 home per-coordinate RMSE: compiled `0.20969`, UKF `0.23340`,
  particle512 `0.31143`;
- d=16 stress RMSE: compiled `0.21688`, UKF `0.23472`;
- d=16: 36 atom, 151,344-byte model, 10-bin Cartesian covariance atom
  storage'a karşı `2.78e14×` azalma;
- particle512'ye median hızlanma: d=2/4/8/16 için yaklaşık
  `6.84× / 7.45× / 6.64× / 3.77×`.

Hüküm:

`AUTOMATIC_PSD_CLOSURE_SURVIVES_SECOND_PASS`

## Ayrılmış katkılar

- Learned nonlinear/non-Gaussian mean düzeltmesi mixture-home'da zorunlu ve
  tekrarlanabilir bir katkı yaptı (`24/24`).
- Conditional atomlar tek global atoma göre d=2/4/8 home ellipsoidlerini daha
  keskin yaptı.
- d=16'da conditional atom semi-axis'i `1.06133`, global atomunki `1.05470`:
  atom conditioning bu boyutta artık fayda göstermedi. Atom ablation kapısı
  dört boyutun üçünde geçti; d=16 başarısı gizlenmedi.
- 512-particle d=16'da degeneracy nedeniyle oracle değildir. d=16 mean iddiası
  particle galibiyetine değil, UKF ve ablation karşılaştırmalarına dayanır.

## Yeni açık koordinat

Dense transition + correlated measurement-noise shift altında coverage boyutla
düşüyor; d=16 stress ortalaması `0.84291`. Önceden yazılmış geniş stress kapısını
geçse de nominal %90 değildir. Dolayısıyla sıradaki teorik soru atom sayısını
artırmak değil:

**measurement whitening yanlış olduğunda correlation bilgisini online, PSD ve
sabit-pass biçimde nasıl geri kazanırız?**

En doğrudan mutasyon, scalar `R = sigma^2 I` chart'ını satır/kolon ölçeklerinden
ve birkaç signed correlation moment'inden derlenen low-rank-plus-diagonal PSD
innovation metric ile değiştirmektir. Bu bir R205 hipotezidir; R204 sonucu olarak
sunulmaz.

## Sınırlar

- Sentetik nonlinear state-space ailesidir; gerçek trace değildir.
- Closure her dimension için offline yeniden derlendi; tek universal model
  değildir.
- `4+2d` atom sayısı teorik optimum değildir.
- Güncel covariance-regression, mixture filter, learned Kalman ve amortized
  inference literatürüyle novelty/collision audit hâlâ gereklidir.

## Tekrar üretim

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\stress_suite.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s . -p 'test_*.py' -v
```

