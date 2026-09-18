# Kaynak bağımlılığı: çalışan ilk uygulama

## Native evidence workspace

Ana ürün yolu artık yerel PySide6 masaüstü uygulamasıdır:

```sh
./Open-Audit-Evidence.command
```

Workspace oluşturma/açma, klasör importu, unassigned evidence, revision-candidate
onay/red, artifact version geçmişi, revision triage, grup detayı ve Mission #1.1
correction işlemleri desteklenir. Widget'lar `workbench/application.py` servis
sınırını kullanır. Mevcut HTML sayfaları legacy diagnostic olarak kalır ve
desktop akışı bunları browser'da açmaz.

Gerçek Ofgem + SONI desktop doğrulaması
`examples/evidence-version-workspace/desktop-phase1-validation.json` içindedir.

## 18 Eylül: Revision Triage

Confirmed iki komşu EvidenceVersion için workspace artık otomatik olarak
`comparisons/<relationship>/triage/index.html` üretir. Artifact geçmişindeki
**open revision triage** bağlantısı ilk olarak bu özeti açar; raw comparison ve
lineage ayrı drill-down olarak korunur.

Triage; literal değer değişimi, formül metni değişimi, formula→hardcode,
hardcode→formula, eklenen/kaldırılan içerik ve karşılaştırılamayan konumları ayrı
sınıflandırır. Aynı türde ve aynı sayfada birbirine en fazla bir boş hücre
uzaklıktaki değişiklikler deterministik bölgeler halinde birleştirilir. Bu,
mevcut içerik motorunun bölge komşuluğudur; aynı business anlamı iddia etmez.

Mevcut row-alignment motoru karşılıklı tekil kayıt eşleşmesi bulduğunda taşınan
eşit hücreler movement/reorder candidate olarak özetlenir. Ham aynı-adres diff
silinmez. Eşleme belirsizse hareket etiketi verilmez; raw değişiklikler kalır.
Her grup desteklenen statik grafikte eriştiği terminal formül sayısıyla gelir ve
bu sayıya göre filtrelenip sıralanabilir. Reach, materiality/risk veya sayısal
etki değildir. Çözülemeyen formül kapsamı raporun üstünde ayrıca gösterilir;
sıfır resolved reach etkisizlik kanıtı değildir.

[Ofgem Mission #2 ölçümü](examples/evidence-version-workspace/mission-2-validation.json):
4.201 raw değişiklik, 362 grup (11,60× sıkıştırma), 83 resolved downstream
impact taşıyan grup; maksimum terminal reach 60. Ofgem çiftinde formül metni
değişimi veya formula/literal geçişi gözlenmedi. 41.738 formülün 4.742'si tam
çözüldü, 36.996'sı unresolved kaldı.

## 18 Eylül: kalıcı Evidence Version Intelligence workspace'i

Çok dosyalı bir müşteri/evidence klasörünü önce tek tek A/B çifti seçmeden
envantere almak için yerel workspace oluştur:

```sh
.venv/bin/python lab.py workbench workspace create /tmp/revenue-workspace --name "Revenue evidence"
.venv/bin/python lab.py workbench workspace import /tmp/revenue-workspace /tam/yol/musteri-klasoru
.venv/bin/python lab.py workbench workspace report /tmp/revenue-workspace
```

Workspace, analiz edilen özgün baytları SHA-256 ile kimliklenen bir `FileBlob`
ve değişmez içerik adresli tek kopya olarak saklar. Her gözlenen yol/ad/zaman ayrı
bir `FileOccurrence` kaydıdır. Import sırasında mantıksal sürüm yaratılmaz;
aynı baytlar tekrar geldiğinde yeni blob oluşmaz ve yeni occurrence aynı blob'a
bağlanır. Farklı baytlar için sayfa
yapısı, dolu hücre sayıları, ortak formül metinleri ve mevcut same-layout / kayıt
eşleme motorları kullanılarak açıklanabilir adaylar oluşturulur. Dosya adı yalnız
açıklayıcı bağlamdır ve tek başına aday yaratmaz.

`index.html` aday kimliğini, iki blob kimliğini ve neden önerildiğini gösterir.
İlişki otomatik kurulmaz. Kullanıcı hangi sürümün önce olduğunu açıkça verir:

```sh
.venv/bin/python lab.py workbench workspace confirm /tmp/revenue-workspace \
  cand_... --before blob_... --artifact-name "Revenue Schedule"

.venv/bin/python lab.py workbench workspace reject /tmp/revenue-workspace cand_...
```

Onay, seçilen tek `EvidenceArtifact` içinde her blob için birer `EvidenceVersion`
yaratır. Bir EvidenceVersion yalnız bir artifact'a aittir; aynı blob, kullanıcı
açıkça isterse başka artifact'taki ayrı bir EvidenceVersion'ı da destekleyebilir.
Onay, red, artifact üyeliği ve sürüm sırası `workspace.sqlite3` içinde kalır.
Onaylanan çift için mevcut aynı-yerleşim karşılaştırması ve statik formül etkisi
üretilir; kayıt eşleştirici taşınmış satır/sütunlar bulduysa ayrıca structural
correspondence raporu oluşturulur. `--override-no-match`, yalnız kullanıcının
dosyaların ilişkisini sistemden bağımsız bildiği durumda açık manuel bağ kurar.

Hatalı kullanıcı kararları geçmişi silmeden düzeltilebilir. Her düzeltme gerekçe
ister; eski ilişki ve karşılaştırma kaydı korunur:

```sh
.venv/bin/python lab.py workbench workspace withdraw /tmp/revenue-workspace rel_... --reason "Yanlış eşleştirme"
.venv/bin/python lab.py workbench workspace correct-order /tmp/revenue-workspace rel_... --before ev_... --reason "Sıra ters girildi"
.venv/bin/python lab.py workbench workspace reassign /tmp/revenue-workspace ev_... --artifact-name "Tax Schedule" --reason "Yanlış artifact"
.venv/bin/python lab.py workbench workspace rename-artifact /tmp/revenue-workspace art_... "Revenue Schedule" --reason "Ad düzeltmesi"
```

Schema v1 workspace'leri ilk açılışta v2'ye taşınır. Eski artifact/version
kimlikleri, onaylanan sıra, karşılaştırma yolları ve karar kayıtları korunur.

[Gerçek çok-dosyalı demo](examples/evidence-version-workspace/README.md), aynı
klasörde iki resmi Ofgem sürümü, yeniden adlandırılmış dosya, exact duplicate ve
alakasız SONI modelini kullanır. Muhtemel sürüm hiçbir zaman doğrulanmış provenance
sayılmaz; statik downstream etki sayısal etki veya audit bulgusu değildir.

## 17 Eylül: aynı yerleşimde sürüm karşılaştırması

`.venv/bin/python lab.py workbench analyze BEFORE.xlsx AFTER.xlsx --same-layout --output /tmp/version-report`

İlk dosya önceki, ikinci dosya sonraki sürümdür; bu sıra korunur. Yalnız aynı
sayfa adları ve hücre adresleri eşlenir. Aynı değerler, aynı formül metinleri,
değişen/eklenen/kaldırılan hücreler ve karşılaştırılamayan hücreler ayrı gösterilir.
Formül sonuçları hesaplanmaz; aynı formül farklı girdilerle farklı sonuç verebilir.
Değişen girdilerin ve formül metinlerinin çözülen grafikteki potansiyel nihai
etkileri gösterilir. Yeniden adlandırılan/tek tarafta bulunan sayfalar listelenir,
otomatik eşlenmez. Çıktı klasörü yeni veya boş olmalıdır.

Gerçek sürüm çiftlerinde her dosya için 150.000, koleksiyon için 300.000 dolu
hücre bütçesi vardır. Seyrek sayfalar artık yalnızca gerçek bounding box 2.000.000
hücreyi aşarsa durdurulur; dolu hücre sayısı ile fiziksel sayfa alanı birbirine
karıştırılmaz. Formül izi bu bütçeden daha büyükse içerik farkı yine üretilir ve
etki listesi yalnız çözülen statik grafik için gösterilir.
[Seçici entegrasyon ve doğrulama](restoration/20260917-salvage-fixes/README.md).

## Gerçek yayımlanmış sürüm çifti

[Ofgem ED2 PCFM V4 incelemesi](examples/published-version-review/ofgem-ed2-pcfm/README.md)
iki resmi sürümü ve hash'lerini korur. Çalıştırmada 125.169 dolu hücre okundu;
20.869 formül metni aynı, 4.054 sabit değer değişikliği, 87 ekleme ve 60 silme
bulundu. Array formula nesneleri metin ve kapsamıyla normalize edildi. Statik
grafik 416 benzersiz potansiyel downstream hedefi izledi; Excel yeniden
hesaplanmadığı için bunlar sayısal sonuç veya audit bulgusu değildir.

15 Eylül 2026. Mevcut labın R207 motoru gerçek kaynak dosyasından çağrılıyor. Uygulama, bir kaynağın farklı türevlerini aynı köke bağlayarak kaynak kaybının hangi sonuçlara yayıldığını gösteriyor. Excel dosyasında formül bağlantılarını kendisi okuyor; kullanıcıdan bağlantıları çizmesini istemiyor.

## Excel tablo başvuruları da okunuyor

`Sales[Amount]`, `[@Amount]`, başlık/toplam seçicileri ve sütun aralıkları artık dosyadaki kayıtlı tablo tanımından gerçek hücrelere çözülür. Kullanıcıdan tablo haritası istenmez. [Yayımlanmış dosyada kaynak etkisini incele](examples/public-tables/StructuredReferences-report/lineage.html): `Table!C3` kapatıldığında toplam etkilenir, ad sütunundaki iki çıktı etkilenmez.

Değiştirilmemiş iki Apache POI dosyasında daha önce çözülemeyen **10/10 formül** çözülüyor. Üçüncü büyük dosya ilk doğrulamada 20.000 dolu hücre sınırında reddedildi. 17 Eylül entegrasyonunda dolu hücre sınırını geçti; bu kez 5.000.000 hücre karşılaştırma sınırında durdu ([güncel kayıt](restoration/20260917-salvage-fixes/real-file-check.json)). Kaynak koordinatları yayımlanmış ayrıştırıcı testlerinin beklenenleriyle karşılaştırıldı; önceki **69 ilgili test** ve raporun jsdom etkileşimi geçti. [Dosyalar ve önce/sonra](examples/public-tables/README.md), [önceki doğrulama kaydı](restoration/20260915-structured-tables/validation.json). Bunlar mühendislik dosyaları; denetim saha doğrulaması değildir.

## Yeni: sırası ve başlıkları değişmiş kayıtları eşleştir

Klasör analizine eklenen kayıt eşleştiricisi, sütunları değer kümelerinden aday olarak eşler; sonra aynı kayda ait satırları hücre hücre karşılaştırır. Kullanıcının sütun haritası çizmesi gerekmez. Belirsiz satır/sütunlar eşlenmez; atlanan satır numaraları ve sütunlar raporda görünür. Bulunan farklar ilk açılışta gösterilir; çözülebilen formüllerde hangi sonuçlara bağlı oldukları listelenir.

[84 yayımlanmış harcama kaydıyla ölçüm](examples/public-spending/verified/index.html), [farkı incele](examples/public-spending/verified/changed_unique_voucher/report/index.html). HM Treasury CSV'si gerçek; sıra/başlık değişiklikleri, +123,45 tutar farkı ve SUM formülleri deney için üretildi. Başlıklar korununca basit başlık tabanlı %80 satır eşleştirmesiyle aynı sonuç alındı. Başlıklar değiştiğinde yeni eşleştirici 84/84 kayıt ve değişen tutarı buldu; başlık tabanlı referanslar uygulanamadı. Aynı faturanın benzer satırında değişen tutar belirsiz kaldı ve eşlenmedi. [Kaynak, beş deney ve yeniden üretim](examples/public-spending/README.md).

Sütunlarda en az 3 farklı anlamlı değer ve %60 örtüşme aranır; karşılıklı tekil en iyi eşleşme seçilir. Satırlarda eşlenen sütunların en az %80'i ve en az 2 farklı anlamlı değer uyuşmalıdır; en az 3 tekil satır gerekir. Eşit değer kümeleri tek başına kayıt eşleştirmez. Bunlar arama eşikleridir, güven olasılığı değildir. Aynı sayfa içindeki kopyalar, dönüştürülmüş/yuvarlanmış değerler ve eşlenemeyen alanlar kapsam dışındadır. İçerik eşleşmeleri kökeni, kopyalama yönünü veya bağımsızlığı kanıtlamaz; formül kökleri birleştirilmez.

Bu değişiklik için **40 workbook/içerik testi** geçti; üç raporda jsdom etkileşimleri doğrulandı. Gerçek tarayıcıda görsel kontrol veya denetçi saha çalışması yapılmış sayılmaz. [Doğrulama kaydı](restoration/20260914-row-matching/validation.json).

## Önceki adım: bağlantısı olmayan ortak içerikleri bul

Aynı klasör komutu artık formül içermeyen dosyalarda da rapor üretir. [Gerçek dosya sonucu](examples/content-review-verified/index.html): Apache POI'nin bağımsız yayımladığı `FormulaEvalTestData_Copy.xlsx` dosyasında `EverythingTests!T7:X19` ile `FinanceLibTests!B2:F14` arasında **63 / 65 konum aynı**. Diğer iki konumda sabit `0.666…` ve `=2/3` formülü yan yana gösterilir; formülün değeri hesaplanmış sayılmaz. Bu bir denetim müşterisinin dosyası değildir.

Yeni görünüm bölge araması, eşleşen hücrelerin yan yana listesi ve yalnız farklı/karşılaştırılamayan hücreleri gösterme seçeneği sunar. Dosyalarda çözülebilen formüller varsa kaynak kaybı görünümü ayrı bağlantıdan açılır. Eşleşen sabitlere bağlı formül sonuçları da listelenir. İçerik eşleşmeleri kaynak grafiğinde birleştirilmez.

Sabit kayma araması, türüyle birlikte aynı olan seyrek değerlerden satır/sütun kaymalarını bulur; en az 6 eşleşen hücre, 3 farklı değer ve bölge içinde %80 eşleşme ister. Bunlar inceleme eşikleridir, güven olasılıkları değildir. Formüller, önbelleğe alınmış formül sonuçları, hatalar ve yaygın 0/1 değerleri kaynak tespiti gibi kullanılmaz. Yukarıdaki yeni kayıt eşleştiricisi sıra değişikliklerini ayrıca arar. Yuvarlanmış veya dönüştürülmüş kopyalar kaçabilir. Aynı sayfa içindeki tekrarlar henüz aranmaz. Ortak köken ve kopyalama yönü bu gözlemden belirlenemez.

**Bu değişiklikte 55 test geçti:** 35 workbook/içerik testi, 8 REL testi, REL kullanan iki üründe 12 test. Raporun arama, bölge seçimi ve iki farklı/karşılaştırılamayan hücreye daraltma davranışları jsdom ile geçti; gerçek tarayıcıda görsel doğrulama yapılmadı. [Çalıştırma kaydı](runs/20260914T154500Z-rel-content/receipt.json), [arayüz kaydı](restoration/20260914-rel-content/ui-check.json).

## Yeni: bir klasördeki Excel dosyalarını birlikte incele

**`Analyze-Workbook-Folder.command` dosyasını açıp klasörü seç.** Ya da:

```sh
.venv/bin/python lab.py workbench analyze /tam/yol/excel-klasoru
.venv/bin/python lab.py workbench analyze kaynak.xlsx turev.xlsx
```

Klasörün doğrudan içindeki en fazla 20 `.xlsx`/`.xlsm` dosyası birlikte okunur. Formüllerdeki dış dosya adı veya sayısal bağlantı kimliği, yalnız verilen dosyalardaki tekil dosya adıyla eşlenir. Kayıtlı eski Windows yolu mevcut olmasa da sağlanan eşleşen dosya kullanılabilir. Başka bir dosya açılmaz veya internetten alınmaz. Eşleşme, dosyanın özgün sürümünü veya doğruluğunu kanıtlamaz.

[İki bağlantılı Apache POI dosyasının raporu](examples/linked-workbooks/index.html), ikinci dosyanın birinci dosyadaki iki kök hücreye dayandığını otomatik çıkarır. [Beş gerçek test dosyasını birlikte okuyan rapor](examples/workbook-folder/index.html), 1.338 formülün 616'sını çözer; kalan 722 formülü dışarıda bıraktığını görünür biçimde belirtir. Bu mühendislik dosyaları gerçek müşteri denetim dosyaları değildir.

Dosyalar arasındaki türevler aynı kök hücreye bağlanır; dosya adını değiştirmek onları kendiliğinden bağımsız kanıt yapmaz. Eksik dosyaların ve dosyalar arası döngülerin etkilediği formüller kapsam dışında tutulur. Aynı isimli iki verilen dosya belirsiz olduğu için reddedilir. Formülsüz kopyaların kökeni hâlâ belirlenemez. **26 test ve iki raporun DOM etkileşim kontrolleri geçti.** [Güncel kayıt](restoration/20260914-workbook-bundle/validation.json).

## Tahmin birleştirmede tekrarın etkisi

[Lab EBC ile oynatılabilir örnek](examples/borrowing/index.html), tek geçmiş gözlemin 1–20 görünümünün tahmini nasıl çarpıtabildiğini gösterir. EBC, REIG ve BAMI onarımları için [PRODUCT_REPAIRS.md](PRODUCT_REPAIRS.md). Bu hesap normal tahmin ve standart hata girdileri ister; Excel hücrelerini otomatik olasılıklara çevirmez.

## Kullan

- **Hazır örneği aç:** [Bağımlılık görünümü](examples/dependency-demo/index.html). Python veya sunucu gerekmez. Müşteri defterini devreden çıkar: üç türev birlikte etkilenir; alternatif teyit + tahsilat yolu örnek iddiayı desteklemeye devam eder. Teyidi de devreden çıkarınca bu yol da kapanır.
- **Kendi Excel dosyanı incele:** `Analyze-Workbook.command` dosyasına çift tıkla ve dosyayı seç. Formüller yerel olarak okunur; kaynak dosya değiştirilmez. Yeni rapor tarayıcıda açılır.
- **Örneği yeniden üret:** `Open-Dependency-Demo.command`.

Terminalden, bu klasörün içinde:

```sh
.venv/bin/python lab.py workbench analyze /tam/yol/dosya.xlsx
.venv/bin/python lab.py workbench demo
.venv/bin/python lab.py workbench benchmark
.venv/bin/python -m unittest discover -s tests -p test_workbench.py -v
```

Yeni kurulumda önce `bootstrap.command` çalıştır. Python 3.12, openpyxl 3.1.5 ve sabitlenen diğer lab bağımlılıkları kullanılıyor. Raporun üretilmesi ve açılması internet bağlantısı gerektirmez. Yeni çıktılar `workbench_runs/` altına yazılır; mevcut raporlar korunur. Bu klasör günceldir; önceki `../lab-restored.zip` arşivi bu uygulamadan önceki sürümdür.

Kısmi bağımlılığı sayısal olarak inceleyen yeni [kovaryans raporu](examples/correlated-evidence/report/index.html), yayımlanmış iki örneğin hesabını yeniden üretir. Bu, Excel benzerliğini otomatik istatistiksel bağımlılığa dönüştürmez.

## Motor ne yapıyor?

`R207_MASLOV_SYMBOLIC_FAVORABLE_SETS/symbolic_favorable.py` içindeki `Rule` ve `compile_circuit_acyclic`, tanımlanan AND/OR destek yollarını bir devreye derler. Yeni `R207Batch` adaptörü, aynı devre üzerinde çok sayıda kaynak kaybını bit kümeleriyle değerlendirir. Rapor, bu derlenmiş devreyi tarayıcıda da çalıştırır. Rapor üretimi bütün senaryo × sonuç tablosunu belleğe açmaz.

Aynı kaynak kimliği birden fazla kanıt görünümünde kullanıldığında hepsi birlikte kaybolur. Böylece bir kaynağın üç kopyası üç ayrı kaynak gibi davranmaz. **Bu, kaynağın doğruluğunu veya farklı kaynakların istatistiksel bağımsızlığını kanıtlamaz.** Destek örneğinin kaynak kimlikleri ve yeterlilik kuralları sentetiktir, otomatik olarak denetim belgelerinden çıkarılmamıştır.

Excel modunda kök, bir hücre adresidir. Aynı hücreye dönen farklı formüller bulunur. Eşit sabit sayılar birleştirilmez; formülsüz kopyalanan veya bağlantısı kaybolmuş aktarımların kökeni henüz bulunamaz. Açık dosya bağlantıları, verilen dosyalar arasında izlenebilir. Bu nedenle bu sürüm, bütün evidence dependency problemini çözmüş bir audit ürünü değildir.

## Gözlenen sonuçlar

[Karşılaştırma raporu](workbench_runs/20260913T233010Z-83f3db27-benchmark/index.html): 15 sentetik problem, yöntem başına 3.498 beklenen sonuç kontrolü. Dört yöntemde de sıfır hata.

| Yöntem | Problem süre medyanlarının toplamı |
| --- | ---: |
| Topolojik AND/OR referans | 49,876 ms |
| Toplu AND/OR referans | 6,477 ms |
| R207 tekil | 68,094 ms |
| R207 toplu | 10,017 ms |

Bu kısa, yerel ölçümde **R207, aynı toplu işlem tekniğini kullanan güçlü referansa üstünlük göstermedi**. İlk karşılaştırmada görünen hız kazancı R207'ye özel değildi; toplu işlemden kaynaklanıyordu. R207'yi kullandığımız gerçektir; ek performans, bilimsel yenilik veya auditor faydası gösterdiğimiz sonucu çıkmaz. Ölçümler üç tekrarın medyanlarıdır; ithalat ısıtması, girdi hazırlama ve ayrı doğruluk hesabı süreye dahil değildir. Ham tahminler, girdiler, ortam ve kod hash'leri raporla birlikte bulunur.

[Apache POI'nin gerçek test dosyaları](https://github.com/apache/poi/tree/trunk/test-data/spreadsheet) üzerinde ayrıca çalıştırıldı:

| Dosya | Çözülen / toplam formül | Kapsam |
| --- | ---: | --- |
| [shared_formulas.xlsx raporu](workbench_runs/20260913T232856Z-6b1135ce-analysis/index.html) | 40 / 40 | Paylaşımlı formüller |
| [FormulaSheetRange.xlsx raporu](workbench_runs/20260913T232856Z-77f79b7b-analysis/index.html) | 2 / 2 | Sayfalar arası 3D referanslar |
| [FormulaEvalTestData_Copy.xlsx raporu](workbench_runs/20260913T232856Z-5fa7284d-analysis/index.html) | 573 / 1.295 | 722 formül çözülemiyor; rapor bunu başta gösteriyor |

Bunlar bağımsız mühendislik örnekleridir; müşteri denetim dosyaları değildir. Formül sayıları bütün bağlantıların bağımsız doğrulaması değildir. 3D örneğin iki formülü için beklenen hücre kümeleri ayrıca test edildi. İlk sürümün reddettiği 3D referanslar, bu dosyadan görülen eksik üzerine eklendi. Sayfa sırası ve aradaki sayfalar hesaba katılır; davranış [Microsoft'un 3D referans tanımıyla](https://support.microsoft.com/en-us/excel/create-a-3-d-reference-to-the-same-cell-range-on-multiple-worksheets) uyumludur. Girdi dosyaları, hash'ler, kaynak adresleri ve Apache lisans/bildirim dosyaları `examples/public-workbooks/` içinde korunur.

İlk tek-dosya sürümünde **19 işlev testi geçti:** ortak kaynak kaybı, alternatif destek, bağımsız doğruluk hesabı, derin/faktörlü devreler, Excel kapsamı, hatalı bağlantılar ve dosyanın korunması. [Test günlüğü](restoration/workbench-tests.log).

Dört raporda JavaScript çalışması, kaynak kapatma, ortak kayıp, sıfırlama, arama ve kapsam gösterimi jsdom ile kontrol edildi. [Arayüz kontrol kaydı](restoration/workbench-ui-check.json). Gerçek Chrome başlatılması ortam tarafından engellendi; görsel tarayıcı kontrolü tamamlanmış sayılmıyor. macOS dosya seçici ve çift tıklama yolu bu ortamda otomatik doğrulanmadı; aynı Python analiz komutları çalıştırıldı.

## Sınırlar

- Statik hücre/range, tanımlı statik ad, tırnaklı sayfa adı, desteklenen işlevler ve 3D referanslar okunur. Excel hesap motoru çalıştırılmaz; makrolar çalıştırılmaz.
- `IF` içindeki kullanılmayan dal dahil bütün statik referanslar potansiyel bağımlılık sayılır. Kaynak kaybı, sayısal sonucun kesin değişeceği veya audit görüşünün bozulacağı anlamına gelmez.
- Verilmeyen dosyalara bağlantılar, dinamik referanslar (`INDIRECT`, `OFFSET`), desteklenmeyen işlevler, desteklenmeyen tablo seçicileri, spill referansları ve döngüler eksik olarak gösterilir. Bunlara bağlı formüller de kapsam dışında tutulur.
- Bütün tekli kaynak kayıpları, en fazla 512 ikili kaynak kaybı ve bütün kaynakların kaybı hesaplanır. İkili kesinti listesi büyük dosyalarda tam değildir; daha büyük asgari kesintiler aranmaz.
- Pilot sınırları: 32 MB sıkıştırılmış dosya, dosya koleksiyonunda toplam 256 MB açılmış içerik, dosya başına 150.000 ve koleksiyon başına 300.000 dolu hücre, sayfa başına 2.000.000 hücrelik sınırlayıcı alan, statik grafik için 30.000 düğüm ve 250.000 kural girdisi. Etkileşimli kaynak görünümü 4.000 kök kaynakla sınırlıdır; daha büyük grafiklerde içerik farkı ve çözülen sınırlı etki listeleri yine üretilir. Bir referans 10.000 hücreden fazla genişletilmez. Geçişli kaynak kümeleri bitset olarak taşınır; önceki 500.000 üyelik durdurma sınırı kaldırıldı.
- Ekran en fazla 150 kaynak satırını gösterir; arama bütün kaynaklarda çalışır. En fazla 200 sonuç gösterilir; JSON dosyaları tam listeyi içerir.

Sonraki ürün çalışmasının ölçütü, sadece motor çalıştırabilmek değil, gerçek bir görevde güçlü mevcut yöntemlere göre gösterilebilir faydadır. Laboratuvarın bütün motorları veya ürün iddiaları bu uygulamayla doğrulanmış değildir.

## 16 Eylül: gerçek finansal model ve formül aralığı onarımı

[SONI kamu finansal modeli](examples/soni-price-control/README.md) üzerinde 6.694 formül, 2.904 kök hücre ve 1.043 nihai çıktı çözüldü. Eski ve yeni kaynak kümesi hesabı aynı sonucu verdi. SUMIF/AVERAGEIF üçüncü aralığı ilk aralığın boyutlarına göre çözer; değişiklikler raporda gösterilir. Bu SONI dosyasında bu iki işlev bulunmadığı için onların saha doğrulaması olarak sayılmaz. Excel girdi hashleri artık doğrudan okunan baytlardan gelir. [82 test, değişiklikler ve sınırlar](restoration/20260916-lineage-semantics/README.md).
