# LabAllCompass — onarılmış çalışma laboratuvarı

15 Eylül 2026. Bu sürümde mevcut motorların hesaplamaları, ürünlerin birbirini çağırması ve çalıştırma yolları onarıldı. Eski proje ve indirilen arşivler korunuyor. Çalışma kodu `LAC_REPRO_R210/` altında; bu klasör özgün arşivin değiştirilmiş bir kopyasıdır.

## Yeni motor ve ürün onarımları

ACSA ve DREW artık açık kaynak gruplarıyla değerlendirme yapabiliyor. Aynı kişiye
ait tekrarlar birlikte örnekleniyor; iki değerlendirme bölümüne taşan kaynak
kimlikleri reddediliyor. Gerçek UCI verisinde 1.529 kayıt / 11 kaynak için standart
hata satır hesabının 11,37 katı çıktı; seçilen model ve ortalama kayıp değişmedi.
[Gerçek veri, tekrar çalıştırma ve sınırlar](examples/grouped-selection/README.md).
Bu bilinen istatistiksel yöntemlerin onarımıdır; bankacılık veya klinik saha kanıtı değildir.

DREW artık seçtiği modeli denetliyor: eşit kayıpta kullanılan getiri ölçütü
ACSA'ya da taşındı; geçersiz önemlilik eşikleri reddediliyor. Lab çalıştırıcısı,
ACSA ve MIFF'te önceden atladığı fonksiyon testlerini artık topluyor.
85 motor/ürün + 17 çalıştırıcı/bileşen testi geçti. Gerçek digits pilotu yeniden
çalıştı; basit doğrulama yöntemine üstünlük iddia edilmedi.
[Onarım ve gerçek veri kaydı](restoration/20260915-selection-identity/README.md).

P083 HEAG artık kanonik EBC + AICC motorlarını gerçekten çağırıyor: kanıtın tekrar sayılması, ek ölçüm kararına kadar izleniyor. [Çalışan maliyet duyarlılığı görünümü](examples/evidence-acquisition/verified/index.html). Gelecek ölçüm bağımsızlığı açık model girdisi; tarihî kaynak kurtarılmış sayılmaz.

SCIG, verinin çeliştiği bağımsızlık varsayımlarıyla seçim yapmıyor. BICC, geçersiz sınırlardan güven sertifikası üretmiyor. P103 artık gerçek HFAD → BICC → ACRA hesaplarını çağırıyor. Dört değişen bileşendeki **36 test geçti**; önceki geniş test çalışmasının yerine geçmez. [Sonuçlar ve kullanım](PRODUCT_REPAIRS.md).

## Yeni: otomatik Excel kaynak izi

Artık sırası/sütun başlıkları değişmiş kayıtlar da değerlerden eşleniyor. [Yayımlanmış 84 harcama kaydı üzerinde örnek ve karşılaştırmalar](examples/public-spending/verified/index.html); [değişen tutar ve bağlı formüller](examples/public-spending/verified/changed_unique_voucher/report/index.html). Değişiklikler deney için eklendi. Belirsiz eşleştirmeler görünür biçimde atlanır; benzerlik ortak köken sayılmaz. Bu eklemeyle 40 workbook/içerik testi geçti.

`Analyze-Workbook.command` ile bir dosya veya `Analyze-Workbook-Folder.command` ile bir klasör seç. Verilen Excel dosyaları arasındaki bağlantılar otomatik çözülür; ortak kökleri ve kaynak kaybının yayılmasını inceleyebilirsin. [Hazır görünümü aç](examples/dependency-demo/index.html). [Kullanım, gerçek dosya sonuçları ve sınırlar](WORKBENCH.md). R207 gerçekten kullanılıyor; güçlü toplu referansa performans üstünlüğü göstermedi. Güncel bağımlılık uygulamasının 26 testi aşağıdaki önceki onarım testlerinden ayrıdır.

## Başlat

Bu bilgisayarda **`Open-Lab.command` dosyasına çift tıkla**. Açılan yerel ekran, 293 bileşeni problem, isim ve API üzerinden aramayı; kaynak kodunu, kullanım komutlarını ve test kaydını bulmayı sağlar. Ekran bir katalogdur; hesaplamalar Python komutlarıyla çalışır.

Alternatif: `index.html` dosyasını tarayıcıda aç. Kataloğu görmek için Python veya internet gerekmez.

ZIP'i başka bir klasöre/bilgisayara taşıdıysan önce `bootstrap.command` çalıştır. Python 3.12 ve internet üzerinden sabitlenmiş bağımlılıkların kurulması gerekir. Doğrulanan ortam macOS arm64, Python 3.12.14'tür; başka platformlar burada denenmedi. Yerel `.venv` hazırdır; taşınabilir ZIP'e sanal ortam dahil edilmez.

Terminalde bu klasörün içinden:

```sh
.venv/bin/python lab.py doctor
.venv/bin/python lab.py components --query covariance
.venv/bin/python lab.py show R037
.venv/bin/python lab.py check R037
.venv/bin/python lab.py demo R002_C326_HFAD
```

`show` girdileri, kaynak dosyalarını ve varsa demo adlarını gösterir. Birden fazla demo varsa `demo ID --entry dosya.py` kullan. Demo bulunmayan bileşenler için mevcut testler ve API gösterilir; yeni bir demo varmış gibi davranılmaz.

## Neler artık daha doğru çalışıyor?

| Motor / birleşim | Onarılan davranış |
| --- | --- |
| SACPS ve kullanan ürünler | Modeli seçen doğrulama verisi ile son değerlendirme verisi ayrıldı. Son değerlendirme verisini değiştirmek artık seçilen modeli değiştirmiyor. |
| CACF / HFAD | Açık bir A → B → C zinciri döngü diye raporlanmıyor. Boş akışlar ve öz döngülerin matris davranışı düzeltildi. |
| REOC | Yalnız yüksek enerjili sensörleri sıralamak yerine ölçümlerin bağımsız yönleri kapsaması ve gözlenebilirliği kullanılıyor. |
| MAWT | Satırların sırası taşıma uzaklığını değiştirmiyor; sıfır kütle açıkça ele alınıyor. |
| REL / CSID / AICC | Geçersiz sayılar, yinelenen kimlikler ve deterministik gözlem sınırları sessizce bozuk sonuç üretmiyor. |
| Maslov R207 | Derin mantık devreleri özyineleme sınırında çökmüyor; eksik veya yanlış işlem sırası reddediliyor. |
| Foundry | Paket içi importlar düzeltildi; daha önce çalıştırıcının kapsamına almadığı ürün testleri dahil edildi. |

Ayrıntılı önce/sonra açıklamaları: [REPAIRS.md](REPAIRS.md). Dosya bazında farklar: [source.patch](restoration/source.patch).

## Elimizde ne var?

| Katman | Bileşen sayısı |
| --- | ---: |
| Ana motorlar: 19 Current + 50 Retro | 69 |
| Foundry ürün klasörleri | 145 |
| Paketlenmiş V2 ürünleri | 52 |
| Sonraki V2 referans kurtarımları | 5 |
| Aktif araştırma turları R193–R210 | 18 |
| Aktif uygulamalar | 2 |
| R401 materyal ürünleri | 2 |
| **Katalog toplamı** | **293** |

Birleşik r38 dosyasındaki **91 çekirdek sınıf** ayrıca `LAC_REPRO_R210/lab_kernels.py` üzerinden içe aktarılabilir. Bunlar katalogdaki 293 bileşene ek 91 bağımsız, doğrulanmış ürün anlamına gelmez.

```sh
PYTHONPATH=LAC_REPRO_R210 .venv/bin/python -c 'from lab_kernels import ObservabilityCoveragePlannerV0; print(ObservabilityCoveragePlannerV0)'
```

## Kurtarma sınırı

145 Foundry klasörünün **89'u genel `spec_runtime` uygulamasına**, **20'si ortak referans yeniden uygulamasına** dayanıyor. İncelenen arşivlerde bunların özgün tarihî motor birleşimleri doğrulanamadı. Genel çalıştırıcının hataları giderildi; bu işlem kayıp özgün algoritmaları geri getirmez. P103 için HFAD → BICC → ACRA, P083 için EBC → AICC çağrılarını kullanan **iki yeni yerel uygulama** yazıldı; özgün tarihî kodları kurtarılmış değildir. Kalan 34 Foundry klasörü kendi paketlenmiş kaynaklarına sahiptir; bu da tek başına bilimsel doğruluk kanıtı değildir.

Beş sonraki V2 ürünü de tam özgün kaynak yerine kurtarılmış referans kod taşır. Ekran bu ayrımları her ürünün içinde gösterir. Tam liste: [RECOVERY_LIMITS.md](RECOVERY_LIMITS.md).

Eski sonuç JSON'ları ve araştırma raporları **tarihî kayıt olarak bırakıldı**. Değişen motorlara ilişkin eski sayılar bu sürümün yeni deney sonucu sayılmamalı. Bütün araştırma deneyleri, veri pilotları ve rapor oluşturucuları yeniden çalıştırılmadı. Laboratuvarın bu onarımı, henüz gerçek bir denetim dosyasında doğrulanmış audit ürünü veya bilimsel breakthrough değildir.

## Gerçekte çalıştırılan kontroller

- **1.514 mevcut test:** geçti; sıfır hata, sıfır atlama. 306 çalıştırma hedefini kapsıyor.
- **31 yeni onarım testi:** geçti. Veri sızıntısı, sahte döngü, değişmezlik, derin devre ve sayısal sınırlar için karşı örnekler içeriyor.
- **23 laboratuvar altyapısı testi:** geçti.
- **69 paketlenmiş ana motor demosu:** sıfır çıkış hatasıyla çalıştı. Bu, demo sonuçlarının bağımsız bilimsel doğrulaması değildir.

[VALIDATION.json](VALIDATION.json), gerçek çalıştırma kayıtlarına ve ortama bağlanır. Geniş test ve onarım testleri aynı sabit paket sürümlerine sahip önceki çalışma ortamıyla yürütüldü; teslim klasörünün kendi ortamıyla da bileşen ve demo çalıştırmaları yapıldı. Kayıtlardaki özgün yollar korunur.

Gerektiğinde tekrar çalıştırmak için:

```sh
.venv/bin/python lab.py run --profile active
.venv/bin/python lab.py run --profile parents
.venv/bin/python lab.py run --profile foundry
.venv/bin/python lab.py run --profile repairs
.venv/bin/python lab.py run --profile all
.venv/bin/python -m unittest discover -s tests -v
```

`all`, sonradan eklenen onarım testlerini de kapsar; yukarıdaki 1.514 testlik kayıt ile 31 testlik onarım kaydı ayrı çalıştırmalardır. Eski `full` profili uyumluluk için eski kapsamını korur. Bir motoru değiştirdiğinde önce `check ID` ile ilgili testleri çalıştırman yeterli olabilir. Kaynak düzenlemek testleri engellemez: çalıştırılan kodun hash'leri kayda alınır, eski paket manifestine eşitlik aranmaz. Dağıtım dosyalarını ayrıca kontrol etmek istersen `lab.py run --profile active --verify-package` veya doğrudan `LAC_REPRO_R210/verify_package.py` kullan.

Test sonuçları `runs/` içinde ayrı çalıştırma klasörlerine yazılır. `demo` ve `experiment` komutları deney için kaynak kopyası oluşturur; sonuçlar `experiments/` altındadır. Bu kopyalama, işletim sistemi güvenlik izolasyonu değildir. Deneyler disk alanı kullanır; ZIP'te eski deney çalışma kopyaları yer almaz, kayıtları korunur.

## Dosyaları bul

- `index.html`, `catalog.json`: aranabilir motor/ürün envanteri.
- `LAC_REPRO_R210/`: onarılmış kaynak, mevcut testler ve tarihî kayıtlar.
- `maintenance/`, `lab.py`: çalıştırıcı, bileşen çözümleme, deney ve karşılaştırma araçları.
- `tests/restoration/`: onarımları doğrulayan yeni testler.
- `restoration/source-changes.json`: 75 mevcut dosyanın önceki ve sonraki hash'leri.
- `restoration/ORIGINAL_MANIFEST.tsv`: özgün manifest; çalışma ağacındaki manifest onarılmış sürüme aittir. Yeni `lab_kernels.py` dahil, 2.909 kayıt doğrulandı.
- `restoration/`: onarım günlükleri ve farklar. Buradaki tek seferlik onarım scriptlerini normal kullanım için çalıştırma; bazıları özgün Downloads arşivinin yerini kullanır. Tanı klasörü tekrar kullanılan çalışma alanıdır.
- `runs/`, `experiments/`: gerçek çalıştırma kayıtları; tamamlanmış kayıtlar tarihçedir.

Önceki `lab-maintenance`, `lab-rehydrated` ve audit prototipleri ayrı klasörlerinde korunur. Bu paket için onları silmek ya da taşımak gerekmez.
