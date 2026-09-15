# Kanıt bağımlılığı ek ölçüm kararına nasıl taşınıyor?

[Çalışan görünümü aç](verified/index.html). Maliyet sürgüsü, motorun hesapladığı bilgi değerlerinin hangi aralıkta farklı seçim ürettiğini gösterir. İlk örnek sentetik; ikinci örnekte 56 yayımlanmış eğitim araştırması tahmini kullanılır, karar faydaları ve gelecek ölçüm özellikleri varsayımsaldır.

Bu uygulama labın **P083 HEAG** ürünüdür. Önceki kod EBC + AICC yerine genel puan sıralayıcısını çağırıyordu. Yeni uygulamada EBC'nin normal çalışma dağılımı doğrudan AICC'ye gider. EBC veya AICC kodu bu ürünün içine kopyalanmadı; kanonik motorlar çağrılır ve dosya özetleri çıktıdadır.

İlk örnekte bir geçmiş gözlemin beş kopyası, tek gözlem sayıldığında yeni ölçümün bilgi değeri **0,16286750**; bağımsız sayıldığında **0,11516472**. Aynı **0,15** maliyet iki modelde ters seçim üretiyor. Tekrarları koruyan sonuç 1–20 kopyada değişmiyor.

Yayımlanmış 56 tahminde, sabit kovaryanslı GLS referansıyla aynı ortalama/varyans alınıyor. Varsayımsal eşik 0,2 ve yeni ölçüm SE'si 0,1 altında bilgi değeri ortak kovaryansla **0,01499544**, köşegen varsayımıyla yaklaşık **0,000000331**. Sürgü bu iki değeri ve aralarındaki maliyet aralığını gösterir. Bu fark bir saha kazancı veya okul politikası önerisi değildir. Doğru kovaryansı kullanan bağımsız GLS + kapalı-form referansı aynı sonucu verir; yönteme üstünlük iddia edilmez.

Veri ve sabit varyans bileşenleri önceki `examples/correlated-evidence/` çalışmasından yeniden kullanıldı. [Orijinal veri yayını](https://wviechtb.github.io/metadat/reference/dat.konstantopoulos2011.html), [sabit kovaryans örneği](https://www.metafor-project.org/doku.php/tips:weights_in_rma.mv_models). Sayısal tablo daha önce resmî HTML'den aktarılmıştı; burada yeniden veri toplanmadı ve REML fit edilmedi. İlk gözlemin `current` seçilmesi kronoloji iddiası değildir. Bu örnekte uyarlanan ağırlık kapalı ve bilgi tavanı etkisizdir.

```sh
.venv/bin/python lab.py evidence-acquisition examples/evidence-acquisition/verified/declared_copies-input.json --review
.venv/bin/python examples/evidence-acquisition/reproduce.py --output /tmp/new-heag-observations
```

İstenen çıktı yolu yeni olmalıdır. `--output yeni.json` ile JSON kaydedilebilir. Ürün API'si, kullanılan kanıttan bağımsız yeni ölçüm hatası ister; paylaşılan hata beyanını otomatik bağımsız saymaz. Excel benzerliğinden kovaryans veya kalibre risk olasılığı çıkarılmaz. Maliyet/fayda varsayımlarını kullanıcı modelinin sağlaması gerekir.

[13 ürün testinin kaydı](../../restoration/20260914-heag/validation.json), [bağımsız sayısal referanslar](verified/receipt.json), [arayüz kontrolü](../../restoration/20260914-heag/ui-check.json). Arayüz etkileşimleri jsdom ile sınandı; gerçek tarayıcıda görsel veya denetçi kullanım doğrulaması değildir. Eski `report/` çıktısı korunur; güncel çıktı `verified/` klasörüdür.
