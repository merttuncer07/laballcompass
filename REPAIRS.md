# Motor ve ürün onarımları

14 Eylül 2026. Değişiklikler mevcut kaynak üzerinde yapıldı; yalnızca katalog veya test çalıştırıcısı eklenmedi. 75 mevcut kaynak dosyası değişti, bir ortak import giriş dosyası eklendi. [Dosya farkları](restoration/source.patch), [hash değişimleri](restoration/source-changes.json) ve [çalıştırma kayıtları](VALIDATION.json) birlikte incelenebilir.

## Hesaplama hataları

| Bileşen | Önceki hata | Yeni davranış ve kontrol |
| --- | --- | --- |
| SACPS; SANP, SACAPL, SACDLW çağrıları | `holdout_returns` hem modeli seçiyor hem seçilen modelin riskini raporluyordu. | Ayrı `validation_returns` seçim için, holdout yalnız son değerlendirme için. Holdout değişimi seçilen kovaryansı değiştirmiyor. Doğrulama verisi yoksa en küçük kabul edilebilir shrinkage seçiliyor. Aynı/paylaşılan doğrulama ve holdout verisi reddediliyor. |
| CACF ortak uygulaması | Tüm akışların kareleri dolaşım enerjisi diye sayılıyordu; açık zincir de döngü görünüyordu. | Akış, incidence matrisi üzerinden divergence-free çevrim uzayına yansıtılıyor. Açık zincir sıfır; 10 birimlik üçgen çevrim 300 enerji. Kontrol edilen alt grafiğin çevrim enerjisi ayrıca hesaplanıyor. Bu ölçü zaman sıralı para iadesini ya da hileyi kanıtlamaz. |
| MAWT ortak uygulaması | Konum sırası değişince taşıma uzaklığı değişebiliyordu. | Konum ve kütle birlikte sıralanıyor. Sonuç satır permütasyonuna değişmez; boş kütle tarafı için uzaklık `None` ve açıklayıcı durum. Net kütle yaratımı/yıkımı, işlem bazında nedensel açıklama değildir. |
| HFAD | Öz döngü incidence sütunu yanlış kuruluyor; boş akışta maksimum alma çöküyordu. | Incidence ekleme/çıkarma ile kuruluyor, öz döngü sütunu sıfır. Boş akış artık geçerli; matris boyutu, kenar ve sonlu sayı kontrolleri mevcut. |
| REOC / V2P057 referansı | Büyük sensör enerjileri sıralanıyor, aynı yönü ölçen iki sensör seçilebiliyordu. | Risk ağırlıklı ölçüm matrisinde gerçek `ObservabilityCoveragePlannerV0` kullanılıyor. İki paralel ve bir bağımsız sensör karşı örneğinde bağımsız yön seçiliyor. Tam tarihî REOC/RECS pipeline'ının kurtarılması iddia edilmiyor. |
| V2P056 referansı | Maskelenmiş kovaryans belirsiz/negatif tanımlı olabiliyor; tek değişken boyutu bozulabiliyordu. | Tek değişken de matris. Maskeye uygun kovaryans diyagonale doğru daraltılarak PSD hale getiriliyor; robust merge geçersiz kovaryansı reddediyor. Kullanılan grid yaklaşımı yeni bir optimalite teoremi değildir. |
| Maslov R207 | Derin DAG'ler Python recursion sınırında çöküyordu; eksik başlık sırası sessizce eksik devre üretebiliyordu. | Erişilebilir DAG iteratif topolojik sırada değerlendiriliyor; 1.500 katmanlı karşı örnek geçiyor. Eksik, yinelenen, döngülü veya geriye bağımlı derleme sıraları reddediliyor. BDD boyut patlaması sınırı ortadan kalkmış değildir. |

## Sayısal ve API sözleşmeleri

- **REL:** yinelenen ilişki adlarının birbirinin üstüne yazması kaldırıldı; boş kayıt, geçersiz ad, NaN/sonsuz değer, tolerans ve colluding-party sınırları doğrulanıyor. Sonuç hâlâ model varsayımları altındaki koşullu sonuçtur; gerçek hile olasılığı olarak kalibre edilmedi.
- **CSID:** sonuç, maliyet, kapsam ve bütçede sonlu sayılar; benzersiz adlar. Aynı aile içindeki azami kapsam yaklaşımı korunuyor.
- **AICC:** kanalların boyutları, simetrik PSD kovaryans, maliyet/gürültü ve quadrature girdileri doğrulanıyor. Sıfır tahmin varyansında tutarlı gözlem hiçbir güncelleme yapmıyor, çelişkili gözlem hata veriyor; sıfıra bölünmüyor.
- **r38 çekirdekleri:** SharedCapacityAllocator, TruncatedPoolRank ve ObservabilityCoveragePlannerV0 sınırları düzeltildi; boş tahsis ve sıfır sensör bütçesi çalışıyor. `lab_kernels.py`, r38'in 91 sınıfına kararlı import sunuyor. 91 sınıfın tamamı için yeni matematiksel doğrulama yapılmış değildir.
- **Kurtarılmış V2P054–058:** boş/geçersiz sayısal girdiler, kovaryans maskeleri, ölçek ve tolerans kontrolleri. Önceden yalnız doğrudan çalıştırmada çağrılan kurtarma kontrolleri gerçek bir pytest testine bağlandı.

## Ürün birleşimleri ve çalıştırma

Foundry'de ilk tanı çalıştırması 146 test dosyasının 18'inde import/collection hatası buldu. Paket ve bağımsız script kullanımı için yerel `parents` ve kardeş modül importları düzeltildi. Testlerde yalnız import yolları değiştirildi; mevcut beklenen sonuçlar zayıflatılmadı. Ana motorların ürünlere kopyalanmış REL, CSID, AICC ve SACPS sürümleri de ilgili düzeltmeleri aldı.

`spec_runtime` artık zorunlu skorları eksikse sessizce sıfıra veya başka skora dönmüyor; açık boolean değerler, sonlu sayılar ve geçerli çalışma modu istiyor. Tahsis, bütün alt kümeleri kaba kuvvetle üretmek yerine tam Pareto sınırı üzerinde 0/1 knapsack kullanıyor. Küçük örnekler kapsamlı aramayla karşılaştırıldı; 100 öğeli örnek de çalıştırıldı. Sınır 100.000 frontier durumudur ve aşılması açık hata verir. Bu genel runtime düzeltmesi, 91 tarihî ürünün özgün mekanizmalarını geri getirmez.

Eski `run_reproduction.py` ve Foundry `run_regression.py` yolları ortak çalıştırıcıya bağlandı. Daha önce hariç bırakılan P134/REIG testleri de kapsama alındı. `lab.py check ID`, `show ID`, `demo ID` tarihî uzun klasörleri bilmeden çalışır. Test, hata, atlama ve timeout gerçek statüsüyle kaydedilir; boş test paketi başarılı sayılmaz. Normal geliştirme çalıştırmaları değiştirilmiş kaynakla ilerler ve o kaynağın hash'lerini kaydeder. Sabit paket manifestini zorunlu tutan kontrol `--verify-package` ile ayrıca istenir; bir motoru düzenlemek testleri bloke etmez.

## Kanıtın kapsamı

[İlk onarım öncesi 16 karşı örnek](restoration/engine-before.log) hata veriyordu; [onarım sonrası 31 test](restoration/engine-after.log) geçti. [Geniş çalıştırma](runs/20260913T174915Z-4c89fad5/receipt.json) 1.514 mevcut testi kapsadı. Ayrıca son çalıştırıcı değişikliğiyle 23 altyapı testi ve 69 demo yürütüldü.

Testler kod davranışının belirtilen örneklerde düzelmesini gösterir. Tarihî raporlardaki performans üstünlüğünü, bütün araştırma iddialarını veya gerçek audit dosyalarında faydayı doğrulamaz. Değişen motorların eski dondurulmuş sonuçları yeni sonuç gibi sunulmadı. Kaynağı eksik ürünler [RECOVERY_LIMITS.md](RECOVERY_LIMITS.md) içinde tek tek listelenir.
