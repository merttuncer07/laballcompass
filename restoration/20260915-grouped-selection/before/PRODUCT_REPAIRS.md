# Motor ve ürün onarımları — 14 Eylül 2026

## P083 HEAG: açıklanan motorları gerçekten çağıran ürün

P083'ün önceki kaynak kodu, açıklamasındaki EBC + AICC birleşimini çalıştırmıyordu; genel puan sıralayıcısına gidiyordu. Yeni yerel uygulama, kanonik EBC sonucunu açık bir normal çalışma dağılımı olarak AICC'ye geçiriyor. Önceki kod ve tarihî sonuç belgesi korundu; kayıp tarihî algoritmanın geri bulunduğu iddia edilmiyor.

Geçmiş kanıtın bağımlılığı yeni ölçüm seçimine kadar taşınıyor. Aynı gözlemin beş kopyası örneğinde bilgi değeri **0,16287** yerine bağımsızlık varsayımıyla **0,11516** oluyor; aynı **0,15** maliyette ek ölçüm seçimi değişiyor. Kopya sayısı 1–20 arasında değişince doğru kimlik modeli sabit kalıyor. [İnteraktif örnek ve yayımlanmış veri karşılaştırması](examples/evidence-acquisition/verified/index.html).

**13 ürün testi geçti.** Her iki motorun fiilen çağrılması, cap=0 karşılaştırması, güçlü çatışma, aynı/güncel gözlemin tekrarları, ayrı gözlemlerde aynı sayılar ve açık kovaryansın seçime taşınması sınandı. Yayımlanmış 56 tahminde doğrudan GLS + iki-eylem kapalı-form referansı aynı sonucu verdi. Bu bir bileşim onarımı; mevcut doğru referansa üstünlük veya denetçi saha faydası iddiası değildir. [Kayıt](runs/20260914T192829Z-heag/receipt.json).

```sh
.venv/bin/python lab.py evidence-acquisition examples/evidence-acquisition/verified/declared_copies-input.json --review
```

Gelecek ölçüm hatasının kullanılan kanıttan bağımsız olduğu açıkça verilmelidir. Paylaşılan gelecek hata için daha geniş ortak model gerekir; bu adaptör böyle bir beyanı bağımsız varsayarak çalıştırmaz. EBC'nin uyarlanan çalışma dağılımı kalibre posterior sayılmaz; fayda ve maliyet girdidir. [API, kapsam ve yeniden üretim](examples/evidence-acquisition/README.md).

## AICC: yanlış ölçüm seçimi ve aynı gözlemi yeniden sayma

AICC'nin 31 noktalı integrali, normal dağılımlı iki eylem örneğinde bilgi değerini **0,38836** buluyordu; analitik değer **0,39894**. Maliyet **0,393** olunca faydalı ölçümü reddediyordu. Hesap, yayımlanmış knowledge-gradient yöntemindeki karar sınırları üzerinden analitik integrale geçirildi. QAIG ürünündeki benzer maliyet sınırı da artık doğru tarafta karar veriyor. [İncelenen gerçek araştırma kodu](research/aicc-knowledge-gradient/OBSERVATIONS.md).

Yeni isteğe bağlı ortak gözlem modunda, kanal adlarıyla sıralanmış hata kovaryansı verilir. AICC, kalan kanalların ortalama, varyans ve durumla kovaryansını gözlemler geldikçe birlikte günceller. Aynı gözlemin kopyası yeni bilgi katmaz; kısmi pozitif/negatif bağımlılık ve ortak hatanın farkta iptali desteklenir. Varsayılan API her çağrıyı yeni bağımsız ölçüm saymaya devam eder. Bağımlılık, eşit sayı veya dosya benzerliğinden çıkarılmaz.

**36 hedefli test geçti:** AICC 17, QAIG 7, SPIA 6, DPAI 6. Analitik iki-eylem referansı, bağımsız sayısal integral, doğrudan toplu Gaussian koşullama, sıra değişmezliği, kopya değişmezliği ve ürün maliyet sınırı kapsandı. Üç üründeki gömülü AICC kopyaları aynı onarımı içeriyor. [Çalıştırma kaydı](runs/20260914T191000Z-aicc/receipt.json).

[Gerçek motor çıktısıyla sayısal örnek](examples/information-selection/index.html): ilk gözlemden sonra varyans 0,5; kopyadan sonra yine 0,5; bağımsız ölçümden sonra 1/3. Varsayımlar ve veriler sentetiktir; denetim faydası veya yeni bir bilimsel yöntem iddiası değildir.

```sh
.venv/bin/python lab.py select-information examples/information-selection/input.json
```

Bu bir adımlık, Gaussian inanç ve doğrusal eylem faydaları altında bilgi seçimidir. Fayda/maliyet ve kovaryans kullanıcı modelinin girdileridir; global çok-adımlı en iyi politika veya denetim görüşü üretmez.

## Son ek: kısmen bağımlı tahminlerde açık kovaryans

EBC artık `borrow_correlated_evidence` ile geçmiş tahminlerin birbirleriyle **ve güncel tahminle** kovaryansını hesaba katabiliyor. `covariance_names`, matris sırasını açıkça doğrular. Aynı gözlemin kopyaları yine tek sayılır; aynı kimlik için çelişen kovaryans satırları reddedilir. Uygun olmayan matrisler otomatik “düzeltilerek” farklı bir modele çevrilmez.

Kovaryans, BAMI ve REIG girişlerinden sonuca kadar taşınır. **49 test geçti:** EBC 23, BAMI 9, REIG 17. [Kayıt](runs/20260914T190000Z-correlated-ebc/receipt.json). Birim güçler ve etkisiz sınır altında sonuç ayrı GLS referansıyla aynı; köşegen kovaryans altında mevcut EBC'ye indirgeniyor. Yeni uyarlanan koşullu ağırlık politikası kalibre olasılık veya yenilik iddiası taşımaz.

[Yayımlanmış verilerle sonuç raporu](examples/correlated-evidence/report/index.html): 56 gözlem/11 bölge örneğinde kovaryanslı hesap **0,18472 / SE 0,08457**; kovaryansı yok sayan hesap **0,12760 / SE 0,04580**. Yayımlanmış yuvarlanmış kovaryans parametreleri sabit kullanıldı; REML yeniden fit edilmedi. Ortak kontrol örneğinde ise farkın varyansı kovaryans korununca **0,13109**, yok sayılınca **0,24419**. Bağımlılığın belirsizliğe etkisi, yapılan işleme göre yön değiştirebilir.

```sh
.venv/bin/python lab.py borrow-evidence examples/correlated-evidence/report/input.json --review
.venv/bin/python examples/correlated-evidence/reproduce.py --output yeni-sonuc-klasoru
```

API ve CLI aynı sonucu verdi. Arayüzün model değiştirme ve bölge ağırlıklarını gösterme davranışları jsdom ile geçti. Gerçek tarayıcı görsel doğrulaması, denetçi kullanım faydası, bilinmeyen kovaryansı bulma ve REL'in farklı kontrolleri arasındaki genel bağımlılık açık işlerdir. Excel benzerliğinden kovaryans uydurulmaz. Farklı niceliklere ait tahminler tek ortak nicelikmiş gibi birleştirilmez. [Matematik ve kaynaklar](research/ebc-dependency.md), [kod farkı](restoration/20260914-correlated-ebc/source.patch).

## Son onarım: aynı gözlemi tekrar sayan EBC

**34 test geçti:** EBC 11, BAMI 8, REIG 15. [Kayıt](runs/20260914T170000Z-ebc/receipt.json), [kod farkları](restoration/20260914-ebc/source.patch), [oynatılabilir hesap](examples/borrowing/index.html).

Eski EBC aynı temel tahmini farklı adlarla ayrı bilgiler gibi topluyordu. Güncel tahmin 0/SE1, geçmiş tahmin 1/SE1 örneğinde tek görünüm sonucu **0,472251 / SE 0,726464**, beş görünüm sonucu **0,666667 / SE 0,577350** idi. Yeni bilgi olmadan hem merkez hem belirsizlik değişiyordu.

Yeni `HistoricalEstimate.observation_id`, **aynı temel tahminin** açık kimliğidir. Kimliği aynı ve tahmin/SE değerleri aynı olan tekrarlar bir kez sayılır; farklı izin verilen ağırlıklarda en yüksek `maximum_power` kullanılır, ağırlıklar toplanmaz. Kimliği veya sayısı aynı olmayan gerçek ayrı tahminler otomatik birleştirilmez. `current_observation_id` mevcut gözlemin geçmişte yeniden sayılmasını da engeller. Aynı kimlik altında farklı tahmin/SE, kısmi örtüşme olabilir; kovaryans modeli olmadan birleştirilmez.

Kimlik P134 REIG'de hem REL kayıt/ilişki hesabından hem EBC aşamasından geçer. Aynı gözlemin kayıtları aynı REL değeri ve öncülünü taşımalıdır. P004 BAMI de kimliği korur. Tekrar eklemek artık bu varsayımlar altında birleştirilmiş tahmini, standart hatayı veya BAMI default çarpanını değiştirmez. Bu sonuç, ayrı bir kapalı form ve tam bağımlı tekrarlara ait GLS kovaryans hesabıyla doğrulandı.

```sh
.venv/bin/python lab.py borrow-evidence examples/borrowing/linked-estimates.json --review
```

`--output yeni.json` sonucu mevcut dosyaya yazmadan saklar. Girdi normal tahminleri ve standart hataları içerir; sıradan audit hücrelerinden bunlar otomatik uydurulmaz. Eski `confidence_low/high` ve `posterior_*` alanları uyumluluk için korunur; çıktıdaki `interval_semantics`, bunların veriden seçilen ağırlıklara bağlı model hesapları olduğunu belirtir. Nominal güven kapsamı, Bayesian kalibrasyon, kaynak doğruluğu ve genel bağımsızlık kanıtlanmış değildir. Kısmi örtüşmede açık kovaryans sağlanabiliyorsa yukarıdaki yeni API kullanılabilir; kovaryansın belgeden otomatik ve geçerli biçimde çıkarılması hâlâ açık iştir.

## Son onarım: REL, RECS ve REIG

REL'in aday uzayı “hiçbir kayıt değiştirilmedi” durumunu dışladığı için, uyuşan kayıtlarda bile bir şüpheli seçiyordu. Null aday eklendi. Aynı iki kaydın aynı toleransla kontrolü farklı adlarla veya ters yönde tekrar verilirse artık tek gözlem olarak ağırlıklandırılır. Aynı çift için farklı toleranslar, ortak gözlem modeli olmadığı için ayrı bağımsız kontroller sayılmaz ve açık hata verir.

Bu onarım, **P017 RECS** ve **P134 REIG** içindeki iki ayrı REL kopyasına da uygulandı. Tekrarlanan kontroller artık safeguard dağılımını veya historical borrowing cezasını değiştirmiyor. RECS'teki eski >%95 testi null adayı dışlayan modele dayanıyordu; yeni test bağımsız kapalı form hesabıyla **0.9469562647** sonucunu doğrular. Seçilen safeguard değişmedi.

[Önce/sonra gözlemleri](restoration/20260914-rel-content/rel-observations.json): uyuşan kayıtlarda eski motor `a` kaydını seçerken yenisi boş kümeyi seçer. Aynı uyuşmazlığı 100 kez tekrarlamak, yeni motorun ağırlıklarını hiç değiştirmez. Ayrı kayıt çiftleri ve kayıt öncülleri arasındaki bağımsızlık hâlâ model varsayımıdır; genelleştirilmiş bağımlılık veya kalibre fraud olasılığı çözülmüş değildir. `posterior` alanı uyumluluk için korunur, koşullu model anlamı çıktıdaki `model` bölümündedir.

Bu üç bileşenin 20 testi ve workbook uygulamasının 35 testi geçti. [55 testin kaydı](runs/20260914T154500Z-rel-content/receipt.json), [kod farkı](restoration/20260914-rel-content/source.patch). Katalog üretimini durduran girinti hatası da düzeltildi. Önceki kodlar `restoration/20260914-rel-content/before/` içinde saklıdır.

## Önceki tamamlanan onarımlar


Dört değişen bileşendeki **36 test geçti**. ACRA kullanan iki ek üründeki 20 test de geçti ([kayıt](restoration/20260914-product-repairs/acra-consumers.log)). Bu, bütün labın güncel doğrulaması veya gerçek denetim faydası kanıtı değildir. [Çalıştırma kaydı](runs/20260914T131915Z-product-repairs/receipt.json), [test çıktısı](restoration/20260914-product-repairs/tests-20260914.log), [kod farkları](restoration/20260914-product-repairs/source.patch). Önceki kodlar `restoration/20260914-product-repairs/before/` içinde korunur.

| Bileşen | Önce | Şimdi |
| --- | --- | --- |
| SCIG | Destek maskesi ve köşegenleştirme güçlü gözlenen bağımlılığı silebiliyordu; güçlü negatif korelasyon ortak hata ailesine çevrilebiliyordu. | Bu durumlarda çelişen bağlantıları raporlar ve portföy seçmez. Sabit sütunlar ve geçersiz eşikler reddedilir. |
| BICC | Verilen etki sınırı gözlenen örneklerde aşılsa bile sayısal güven sınırı dönebiliyordu. | İhlalde McDiarmid yarıçapı ve kuyruk garantisi `None` olur. Deterministik/bağımlı senaryolar için yeni `scenario_pairs` modu yalnız gözlenen etkiyi verir. |
| P103 CFAI | HFAD + BICC + ACRA yazmasına rağmen genel puan seçicisini çağırıyordu. | Gerçek HFAD ayrıştırması → BICC bağlantı etkisi → ACRA bütçe dağılımı çalışır. |
| ACRA | Sonlu olmayan girişler ve yinelenen adlar açıkça denetlenmiyordu. | Geçersiz değerler ve belirsiz bölge/seçenek kimlikleri reddedilir. |

SCIG'nin yeni `objective_improvement_under_assumed_partition` alanı eski `gain_vs_declared_family_removal_control_under_adjusted_reality` alanının yerine geçti. Bu, kurulan varsayımsal modeldeki amaç farkıdır; bağımsız gözlenen gerçek dünya kazancı değildir. Aktif çağrılar güncellendi; tarihî JSON sonuçları korunur. Korelasyon, ortak belge kökenini veya bağımsızlığı kanıtlamaz; doğrusal olmayan bağımlılıkları kaçırabilir. Eşikler güven aralığı değildir ve kalan aileler arasındaki CSID çarpımı hâlâ koşullu bağımsızlık varsayımına dayanır.

BICC'nin `product_iid` modu, bağımsız ürün dağılımını çağıranın beyanı olarak korur. Yeni `sampling_model='scenario_pairs'` deterministik veya bağımlı karşılaştırmaları kabul eder; Efron–Stein varyans üst sınırı vekili ve olasılıksal sertifika üretmez. Tek senaryo, bağımsız veri varmış gibi çoğaltılmaz.

## P103'ü çalıştır

Lab klasöründen:

```sh
.venv/bin/python lab.py flow-review examples/circular-flow/input.json
```

Kendi yapılandırman için:

```sh
.venv/bin/python lab.py flow-review /tam/yol/akis-yapilandirmasi.json --output yeni-sonuc.json
```

`--output yeni-sonuc.json` ekleyerek kaydet; mevcut dosyaya yazılmaz. Girdi, bağlantıları ve akışları zaten bilinen graf yapılandırmasıdır; genel muhasebe dosyasından otomatik graf çıkarma henüz yoktur.

[Örnek girdi](examples/circular-flow/input.json) ve [üretilmiş sonuç](examples/circular-flow/result.json): üçgende 10 birimlik akışlar, açık köprüde 1.000 birim vardır. Belirtilen değiştirme senaryosunda enerji etkileri **166,667; 19,667; 9,917; 0** çıkar. Bir birim bütçe `cycle_a` bağlantısına ayrılır. En büyük tutarı seçmek bu belirli görevde sıfır etkili köprüyü seçerdi. Ayrı testte bütçe sonucu bütün uygun seçeneklerin bağımsız tam aramasıyla karşılaştırıldı. Bu sentetik sonuç, gerçek auditor faydası veya genel yöntem üstünlüğü değildir.

Uygulama kimliği `native_reimplementation_20260914`; **özgün tarihî kaynak kurtarılmış değildir**. Yeni kod eski performans iddialarını miras almaz. P103 artık genel `spec_runtime` kullanmadığı için bu gruptaki Foundry sayısı 91'den 90'a indi.

Hodge projeksiyonu işaretli bir doğrusal cebir ayrıştırmasıdır; yönlü döngüsüz graf üzerinde de sıfırdan farklı olabilir. Dairesel ödeme veya fraud kanıtı değildir. Bütçe amacı, RMS enerji etkisinin karesi ile varsayılan artık hata çarpanının karesinin çarpımlarını toplar. Parasal kayıp veya audit riski değildir. Seçenek etkinlikleri varsayımdır; varsayılan `reviewed=0` etkiyi tamamen giderme varsayımıdır. Ortak inceleme etkileşimleri modellenmez. Yoğun matris uygulaması 2.000 düğüm, 200 bağlantı ve 20.000 senaryo-bağlantı girdisiyle sınırlıdır.

## Kullanım problemine ilişkin gözlemler

[PCAOB AS 1105 .05, .08–.10A](https://pcaobus.org/oversight/standards/auditing-standards/details/AS1105), aynı tür kanıtı çoğaltmanın düşük kaliteyi telafi etmediğini; bilginin kaynağının, elde edilişinin ve değişikliklerin önemini vurguluyor. Sayısal bir bağımsız kanıt sayısı formülü vermiyor.

[Bir auditor tartışmasında](https://www.reddit.com/r/Accounting/comments/1ebs6me), fiyatı destekleyen belge yerine elle girilen sayıların bölündüğü Excel gönderilmesinden yakınılıyor. Bu tekil anlatı yaygınlık ölçümü değildir; kaynak bağlantısı ile kaynağın doğruluğunun farklı işler olduğunu somutlaştırır.

Açık Excel bağlantıları artık verilen dosyalar arasında izlenebilir. Formülsüz kopyaların kökenini bulma hâlâ eksiktir. Mevcut Excel uygulamasının sınırları ve R207'nin güçlü toplu referansa üstünlük göstermeyen sonucu [WORKBENCH.md](WORKBENCH.md) içinde korunur.

## MIFF ve DREW: maliyet ölçeği doğru kesintiyi bozmuyor

MIFF, tanımlanmış şüpheli kaynaktan korunan sonuçlara giden bütün yolları en düşük toplam bağlantı kesme maliyetiyle ayırır. Önceki sürüm iki bağlantılı örnekte 1e-13 yerine 5e-13 maliyetli kesintiyi seçiyor, tek bağlantı 1e16 olduğunda hiç kesinti seçemiyordu. Tamsayı artık kapasite hesabı her iki hatayı ve büyük tamsayıların erken yuvarlanmasını giderdi. DREW içindeki gerçek MIFF kopyası da güncellendi.

24 motor + 11 ürün testi geçti. Küçük ağlarda bütün olası düğüm bölmeleriyle sonuç karşılaştırıldı; NetworkX'in yayımladığı yönlü ağda beklenen kesinti maliyeti 23 yeniden elde edildi. [Önce/sonra hesapları](restoration/20260915-miff/observed-comparison.json), [test kaydı](restoration/20260915-miff/validation.json), [incelenen gerçek algoritma](research/miff-mincut/OBSERVATIONS.md). Bu, bilinen minimum-kesinti hesabının onarımıdır; gerçek sistemde bağlantıları otomatik kesmez veya denetim görüşü üretmez.

## DREW / ACSA: seçilen adayın kendisini denetle

Eşit karar kaybında DLEW, gerçekleşen getirisi daha yüksek adayı seçiyordu;
ACSA aynı eşitliği sütun sırasıyla bozuyordu. Sonuçta seçilen `b` adayı yerine
`a` denetlenebiliyordu. DREW artık kayıp ve getiri matrislerini aynı eylem
yollarından üretiyor. ACSA aynı seçim kuralını, birlikte yeniden örneklenen
kayıp/getiri satırlarında da uyguluyor. Kimlik uyuşmazlığı hata üretir; kararsız
seçim sonucu “denetimden geçti” durumuna çevrilmez.

NaN veya sonsuz önemlilik eşiği artık reddediliyor. Gerçek el yazısı veri
pilotundaki model kayıplarında bu değerler, 0,01111 ek kayıp mevcutken
“regret detected” durumunu gizliyordu. Geçersiz eşik girdisini reddetmek,
istatistiksel anlamlılık veya bankacılık faydası kanıtı değildir.

Çalıştırıcıdaki ayrı bir hata da düzeltildi: ACSA ve MIFF'in fonksiyon testleri
normal unittest keşfinde atlanıyordu. Karma test paketleri artık pytest ile
çalışıyor. **85 motor/ürün testi ve 17 çalıştırıcı/bileşen testi geçti.**
[Gerçek çalışma kaydı](runs/20260915T164716Z-0d342c3a/receipt.json).

Mevcut 27 adaylı, tek sabit seed kullanan gerçek digits pilotu yeniden çalıştı:
seçilen ve denetlenen aday `knn_k3`; korunan doğrulamada en iyi aday `knn_k1`.
Son bölümde hata sayıları 8/360 ve 6/360. Sıradan doğrulama kaybı minimizasyonu
da `knn_k1` seçiyor; DREW'e özgü doğruluk üstünlüğü gösterilmedi. Yazar grubu
bağımsızlığı doğrulanmadı, bankacılık verisi kullanılmadı.
[Gerçek veri çıktısı](restoration/20260915-selection-identity/real-data-validation.json).

Bootstrap hâlâ verilen satırları yeniden örnekler; ardışık karar politikasını
yeniden çalıştırmaz ve aynı kaynaktan gelen satırlar için otomatik bağımlılık
düzeltmesi yapmaz. Bu sınır düzeltilmiş kimlik eşlemesiyle karıştırılmamalı.
