# SONI fiyat kontrolü — özgün kamu finansal modelinde kaynak izi

Kaynak, Kuzey İrlanda Utility Regulator kurumunun 21 Aralık 2020'de yayımladığı SONI 2020–2025 fiyat kontrolü nihai kararının finansal modelidir. Model dosyası değiştirilmedi; varsayım, işlem veya banka kaydı eklenmedi. Bu bir eğitim dosyası veya bizim ürettiğimiz vaka değildir. Finansal modelin kendisi tahmin/varsayımlar içerir; gerçekleşmiş banka işlemleri olarak sunulmaz.

[Birincil yayın sayfası](https://www.uregni.gov.uk/publications/final-determination-soni-price-control-2020-2025) · [Özgün finansal model](https://www.uregni.gov.uk/files/uregni/media-files/UR%20TSO%20financial%20model%20FD.xlsx)

Raporu görmek için `report.zip` dosyasını çıkarıp içindeki `index.html` dosyasını tarayıcıda açın. Ayrıntılı kaynak haritası aynı klasördeki `lineage.html` dosyasındadır. Raporda Inflation!F6 hücresini kaynak aramasında bulup devreden çıkarmak, 487 nihai çıktının potansiyel statik bağlantısını etkiler. Bu, 487 sayının yanlış olduğu veya bir enflasyon varsayımının hatalı olduğu anlamına gelmez.

Gözlenen sonuçlar:
- 33 sayfa, 14.604 dolu hücre, 6.694 formül; tamamının desteklenen statik referansları çözüldü.
- 2.904 kök hücre, 1.043 nihai çıktı, aynı köklere dayanan 1.379 formül grubu.
- Eski uygulama 500.000 geçişli kaynak üyeliği sınırında duruyordu. Yeni gösterim dosyayı açtı. Bağımsız kontrol için eski yöntem yalnız üyelik sınırı artırılarak da çalıştırıldı; eski ve yeni tam problem çıktılarının hashleri aynı.
- Dört yöntem, aynı 33 kaynak çıkarma senaryosu × 1.043 çıktı üzerinde aynı sonuçları verdi. Bunlar gözlenen kaynak kimlikleriyle kurulan varsayımsal kayıp senaryolarıdır; çalışma kitabına müdahale edilmedi.
- Rapor 3.418 senaryo içerir: tüm tekil kaynak kayıpları ve sınırlı ikili tarama dahil. Tüm olası birleşimler veya sayısal sonuçlar doğrulanmış sayılmaz.
- Tek çalıştırmada toplam işlem bellek tepesi eski referansta 106.020.864, yeni gösterimde 85.098.496 bayttı. Süreler ve yöntem başına değerler validation.json içindedir; genellenmiş performans üstünlüğü iddiası değildir. AND/OR bitset bu ölçümde R207 bitset'ten hızlıydı.

Bu modelde SUMIF/AVERAGEIF bulunmadı. Aralık semantiği düzeltmesinin saha kanıtı olarak kullanılmıyor. Ayrıca incelenen SONI teslimatlar dosyası ve Westmorland and Furness özel okul bütçe dosyası formül içermedi; bu gözlem manifest.json'da kaydedildi. Sahte bir formül eklenmedi.

Tarayıcı otomasyonunun file:// bağlantısını engellemesi nedeniyle görsel açılış doğrulanamadı. Rapor üretimi ve iki HTML dosyasının JavaScript sözdizimi kontrolü geçti.

Yeniden üretim, lab klasöründen mevcut araçla:

```sh
.venv/bin/python lab.py workbench analyze examples/soni-price-control/sources/soni-financial-model.xlsx --output /tmp/soni-new-report
```

Çıktı klasörü yeni veya boş olmalıdır. `report.zip` 40 MB üzerindeki tekrarlı JSON/HTML kayıtlarını sıkıştırılmış tutar; böylece repo aynı rapor verisinin birden fazla açık kopyasını taşımak zorunda kalmaz. Kaynak dosyaları, URL'ler ve edinme hashleri `sources/` ile `manifest.json` içindedir. Formüller değerlendirilmez, dış dosya veya ağ bağlantısı otomatik açılmaz.

Tam problem eşitliğini yeniden ölçmek için `compare_sets.py compact /tmp/soni-comparison` ve `compare_sets.py legacy /tmp/soni-comparison` komutlarını labın `.venv/bin/python` yorumlayıcısıyla çalıştırın. Script yeni sonuç dosyaları ister; eski kodun yalnız üyelik sınırını karşılaştırma için değiştirir. İki JSON içindeki `full_problem_sha256_without_new_empty_field` aynı olmalıdır.
