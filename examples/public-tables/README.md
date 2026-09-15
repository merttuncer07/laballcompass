# Excel tablolarının formül bağlantıları

[9 formülün kaynak izini aç](StructuredReferences-report/lineage.html). Apache POI'nin değiştirilmemiş dosyasında `Table!C3` kaynağını devreden çıkar: hesaplanan `Table!A3` üzerinden `Formulas!A1` sonucu etkilenir. `Name` sütununa dayanan iki sonuç erişilebilir kalır. Bu yapısal etki, hesaplanan sayının yanlış olduğunu göstermez.

[Sütun aralığı kullanan ikinci dosya](evaluate_formula_with_structured_table_references-report/lineage.html), `SUM(Table1[[A]:[B]])` formülünü dört gerçek kök hücreye bağlar.

| Değiştirilmemiş dosya | Önce | Şimdi |
|---|---|---|
| StructuredReferences.xlsx | 0/9 formül çözülebiliyor | 9/9; 12 kök hücre |
| evaluate_formula_with_structured_table_references.xlsx | 0/1 | 1/1; 4 kök hücre |
| StructuredRefs-lots-with-lookups.xlsx | 20.000 dolu hücre sınırında reddediliyor | Aynı sınırda reddediliyor |

Bu dosyalar bağımsız yayımlanmış mühendislik girdileridir; denetim müşterisi dosyaları değildir. Büyük dosyayı kırparak başarılı gösterme veya sınırı kaldırma yapılmadı. [Önce/sonra gözlemleri](../../restoration/20260915-structured-tables/public-observations.json), [indirilen asıl dosyaların URL ve özetleri](SOURCES.json).

```sh
.venv/bin/python lab.py workbench analyze examples/public-tables/StructuredReferences.xlsx --output /tmp/new-table-report
```

Raporun arkasındaki R207 motoru değişmedi. Yeni destek, kaydedilmiş Excel tablo adlarını, sütunları, başlık/toplam ve `@`/`#This Row` başvurularını koordinatlara çevirir. Eksik toplam satırı, hatalı/belirsiz tablo tanımı, veri dışındaki `#This Row` ve aşağı akışındaki formüller çözüldü sayılmaz. Formül değerleri hesaplanmaz; aynı sayılara sahip farklı dosya kökleri birleştirilmez.

[İncelenen gerçek ayrıştırıcı kodu ve farklı davranışlar](../../research/structured-references/OBSERVATIONS.md). Apache 2.0 lisansı ve NOTICE dosyası bu klasörde korunur. Yayımlanmış test beklenenleriyle koordinatlar karşılaştırıldı; Apache Java test takımı veya Excel kendisi çalıştırılmış sayılmaz.
