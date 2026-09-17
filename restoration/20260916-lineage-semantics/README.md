# 16 Eylül — kanıt kaynağı ve Excel hesaplama onarımı

DependencyProblem artık kaynak eşlemesini kendi salt okunur kopyasında, kural ve hedefleri tuple olarak tutar. Kurucuya verilen listelerin/sözlüklerin veya to_dict çıktısının değiştirilmesi analizi ve derlenmiş motoru bozamaz. İç açıklama metadata'sı düzenlenebilir; kurucu ve JSON dışa aktarım sınırlarında iç içe kopyalanır. Tamamen donmuş bir genel veri yapısı framework'ü eklenmedi.

SUMIF ve AVERAGEIF üçüncü aralığı, ilk aralığın satır/sütun boyutlarıyla sol üst hücreden itibaren izler. Token konumuna göre düzeltme yapıldığı için aynı referansın başka bir argümandaki kullanımı değişmez. Statik adlar, desteklenen tablo sütunları ve verilen diğer çalışma kitapları çözülür; çok parçalı adlar veya hesaplanan aralıklar açıkça çözülemeyen olarak kalır. Aralık değişikliği JSON'a ve HTML raporuna yazılır. Apache POI Sumif.createSumRange uygulaması ve Microsoft AVERAGEIF açıklaması incelendi; hiçbir formül değeri hesaplanmaz.

Kaynak kümeleri her formül için ayrı Python setleri yerine tamsayı bitleriyle taşınır. Aynı kümeye sahip formüller hâlâ aynı biçimde gruplanır. Bu değişiklik, gerçek SONI dosyasında eski 500.000 geçişli üyelik sınırının yol açtığı durmayı giderdi. Kullanıcıdan yeni veri veya kaynak haritası girmesi istenmedi.

Excel dosyası yüklenirken baytları bir kez alınır; ZIP incelemesi, Excel okuması ve SHA-256 aynı içerikle yapılır. Sonradan dosyanın değiştirilmesi raporun kaynağını değiştirmez. Doğrudan verilmiş, dosyadan okunmamış bellek içi workbook nesnesine disk dosyasının hash'i iliştirilmez.

82 test ve 12 alt test geçti. İki mevcut Apache POI dosyasının stil uyarısı kaldı. İlk kapsamlı çalışmadaki tek hata, testte Excel'in ayrılmış Criteria adının kullanılmasıydı; Conditions olarak düzeltildi. Mekanizma karşı örnekleri gerçek banka dosyaları gibi sunulmaz.

Gerçek vaka ve sonuçlar: ../../examples/soni-price-control/README.md. Düzenleyicinin değiştirilmemiş finansal modelindeki 6.694 formül çözüldü. Eski küme yöntemi (yalnız karşılaştırma için üyelik sınırı artırılarak) ve yeni yöntem aynı tam problem hash'ini verdi. Dört motor, 33 gerçek-kaynak çıkarma senaryosunda aynı sonuçları verdi. R207 üstünlüğü bulunmadı.

changes.json bu onarımın değişiklik öncesi/sonrası kod hashlerini listeler. before/ özgün kodu, intermediate/ geliştirme sırasında oluşan ara dosyaları saklar. validation.json komut çıktısını ve doğrulamanın sınırlarını içerir. Eski arşivler, önceki ACSA/DREW onarımları ve İZ portföy paketi korunmuştur. Commit/push yapılmadı.

Kaynaklar:
- https://raw.githubusercontent.com/apache/poi/trunk/poi/src/main/java/org/apache/poi/ss/formula/functions/Sumif.java
- https://support.microsoft.com/en-us/excel/functions/averageif-function
- https://support.microsoft.com/en-us/excel/functions/sumif-function
