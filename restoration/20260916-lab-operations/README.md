# 16 Eylül — lab çalışma yolu ve karşılaştırma kaynağı

Bileşen görüntüleme her çağrıda katalog yazıyordu. Aynı salt okunur ACSA araması eski kodda izin hatası verirken yeni kodda tamamlandı. catalog.collect() güncel kaynak bilgisini üretir; build() gerektiğinde kaydeder. components ve show ilk yolu kullanır.

compare.evaluate() artık her girdiyi bir kez okur. Ayrıştırma ve SHA-256 aynı baytları kullanır; dosyanın sonradan değişmesi sonuç kaydının dayanağını değiştirmez. Varsayılan metin kodlaması, CSV yeni satır davranışı, hesaplama ve mevcut sonuç yapısı korunur. İki farklı dosyanın okunmasının tek bir atomik işlem olduğu iddia edilmez.

9 karşılaştırma ve 5 bileşen testi geçti. Üç yeni karşılaştırma testi eski kodda hatayı yeniden üretti (ajanın staging çalışması); kanonik repoda 14 testin tamamı geçti. validation.json gerçek komut çıktılarını içerir. Bunlar mekanizma testleridir; yeni bir banka saha vakası değildir.

before/ değişiklik öncesi dosyaları, changes.json bu turda uygulanan dosyaların hashlerini saklar. Önceki ACSA/DREW değişiklikleri korunmuştur. Genel git diff bu önceki değişiklikleri de içerir; bu turun kapsamı changes.json listesidir.

Kullanım ve araştırmaya dayalı mimari tercihi LAB_STRATEGY.md son bölümünde; kısa repo yönlendirmesi AGENTS.md içinde. Yeni bağımlılık, model değişikliği veya dağıtım hizmeti eklenmedi.

Sonraki somut iş: DependencyProblem dışa verilen / dışarıdan alınan koleksiyonları güvenli biçimde sahiplenmeli; ardından SUMIF/AVERAGEIF efektif aralık desteği gerçek dosya incelemesine bağlanmalı. Geçici eski SUMIF taslağı bulunamadı; dağıtılmış özellik değildir.

