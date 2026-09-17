# LabAllCompass için sonuç üreten araştırma düzeni

## Teşhis

LabAllCompass, tarihî ve çağdaş matematik mekanizmalarını algoritmaya çeviren, bu algoritmaları birleştirerek yeni yetenekler arayan bir hesaplamalı araştırma laboratuvarı. İçeriği yalnız audit ile sınırlı değil: istatistiksel bağımlılık, karar verme, bilgi toplama, temsil küçültme, dinamik sistemler ve sembolik ispat içeriyor. Audit, bu araştırmaların somut bir kullanım alanı olabilir.

İncelenen kaynaklarda beş iş ailesi öne çıkıyor. Bu sınıflandırma bir öneridir; bütün bileşenlere uygulanmış yeni bir katalog değildir.

| İş ailesi | Labdaki örnekler | Yapabilecekleri iş |
| --- | --- | --- |
| Kanıt, bağımlılık ve belirsizlik | REL, SACPS, EBC, MIFF, R207 | İlişki ihlallerini yerelleştirme, hata kovaryansı, bilgi aktarımı ve ispat bağımlılıkları |
| Hangi bilgiyi/incelemeyi seçmeliyiz? | AICC, ACRA, DTTC | Karar değerine göre ölçüm, inceleme veya tetikleyici seçimi |
| Daha küçük temsille aynı kararı koruma | TSRC, TWMR, DSBC, ATRC | Hedefe göre indirgeme, sıkıştırma ve bellek seçimi |
| Akışlar ve dinamik sistemler | HFAD, UMCA, CORMA, R204–R206 | Akış ayrıştırma, taşıma, gözlenebilirlik ve rekürsif filtreleme |
| Araştırmanın kendi ölçümü | DLEW, MDDC, R209–R210 | Karar kaybı, metriklerin yanıltması ve karşı örneklerle kapsam daraltma |

**Ana eksik, bütün labın tekrar tekrar döndüğü ortak bir kullanım problemi ve o problemde biriken karşılaştırılabilir sonuçlar.** Bazı araştırmalarda iyi deney disiplini zaten var. Ancak bu disiplin, bütün motorların ortak çalışma biçimine ve teslim edilen uygulamalara dönüşmemiş.

Yerel kaynaklardan üç somut gözlem:

- [P103/CFAI kaynak dosyası](./LAC_REPRO_R210/BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS/products/P103_CFAI/cfai.py), ilk incelemede üst mekanizmaları `HFAD + BICC + ACRA` olarak yazmasına rağmen genel `spec_runtime` yolunu çağırıyordu. Bu gözlem sonrasında P103 gerçek motor birleşimine geçirildi; güncel onarım `PRODUCT_REPAIRS.md` içinde. İlk tespit, bugünkü kodun hâlâ aynı olduğu anlamına gelmez.
- [R207 kararı](./LAC_REPRO_R210/ACTIVE_RESEARCH/R207_MASLOV_SYMBOLIC_FAVORABLE_SETS/R207_DECISION.json), faktörlü ispat temsilini koruyor ama literatürle örtüştüğü için breakthrough saymıyor. Bu, kullanım değerinin bulunmadığını göstermiyor. Teknik yetenek ile bilimsel özgünlük ayrı sorular.
- [R204](./LAC_REPRO_R210/ACTIVE_RESEARCH/R204_PUGACHEV_PSD_CLOSURE_STRESS/README.md) ve [R206](./LAC_REPRO_R210/ACTIVE_RESEARCH/R206_PUGACHEV_ADAPTIVE_INNOVATION_METRIC/README.md), rakipler, bileşen çıkarma deneyleri ve başarısızlık sınırları taşıyor. Buna karşın açıklanan veri aileleri sentetik. Kayıtlı üstünlükleri bu incelemede yeniden çalıştırmadım; gerçek dosyalardaki fayda olarak kabul etmiyorum.

Önceki onarımın test sayıları yazılımın belirtilen davranışlarını ölçüyor. Ekonomik fayda, bilimsel yenilik ve gerçek kullanım başarısı için ayrı kanıt gerekiyor.

## Benzer projelerin fiilen yaptığı

14 Eylül 2026'da erişilen kod ve sonuç dosyaları incelendi. Aşağıdakiler projelerin tamamına ilişkin bağımsız performans doğrulaması değildir.

| Proje | İncelenen uygulama | Lab için alınabilecek davranış |
| --- | --- | --- |
| FunSearch | Değiştirilen fonksiyon bir program şablonuna yerleştiriliyor; verilen girdilerde çalıştırılıp skorları program veritabanına yazılıyor. Açık sürümün sandbox ve model bileşenleri tamamlanmış bir hizmet değil. | Araştırmayı belirli bir hesaplama darboğazına bağlamak; her adaydan aynı değerlendirilebilir çıktıyı istemek. [Kod](https://raw.githubusercontent.com/google-deepmind/funsearch/main/implementation/evaluator.py) |
| Nevergrad | Ek deney örneği, problem × optimizer × bütçe birleşimlerini oluşturuyor; `RandomSearch` aynı deneyler içinde karşılaştırılıyor. | Motor ile problem paketini ayırmak; yeni mekanizmayı mevcut rakiplerin yanına takabilmek. [Kod](https://raw.githubusercontent.com/facebookresearch/nevergrad/main/nevergrad/benchmark/additional/example.py) |
| Ax | `BenchmarkProblem`, `BenchmarkMethod` ve seed tekrarları ayrı. Sonuç işleme, gözlenen değerlerle sonradan hesaplanan oracle değerlerini de ayırıyor. | Aday seçiminde bilinen bilgi ile değerlendirme için kullanılan gerçeği karıştırmamak; bütçe ve tekrarları eşlemek. [Kod](https://raw.githubusercontent.com/facebook/Ax/main/ax/benchmark/benchmark.py) |
| AlphaEvolve sonuç paketi | Matematiksel sonuçları ve doğrulama kodunu yayımlıyor. Depo, yalnız en iyi bilinen sonuçları aşan örnekleri içerdiğini; AlphaEvolve'u çalıştıran kodu içermediğini açıklıyor. | Her başarılı çalışma için yeniden incelenebilir bir sonuç teslim etmek. Bu vitrinden genel başarı oranı çıkarmamak. [Paket](https://github.com/google-deepmind/alphaevolve_results) |
| Sakana AI Scientist | Fikirler için modelin verdiği ilginçlik/uygulanabilirlik/yenilik puanları var; literatür araması sonrası yenilik kararı da model çıktısından ayrıştırılıyor. | Bu puanları araştırma önerisi olarak kullanmak; ölçülmüş sonuç veya doğrulanmış özgünlük statüsüne çevirmemek. [Kod](https://raw.githubusercontent.com/SakanaAI/AI-Scientist/main/ai_scientist/generate_ideas.py) |

OpenEvolve'da körlemesine alınmaması gereken somut bir örnek de var: `function_minimization/evaluator.py`, aday iki değer döndürürse amaç fonksiyonunu hesaplıyor; üç değer döndürürse adayın `value` değerini kullanıyor. O değer daha sonra skora giriyor. **Kod incelemesinden çıkarımım:** bu örnekte skorun bir kısmı gerçek amaç değeri yeniden hesaplanmadan şişirilebilir. Bu bulgu bütün OpenEvolve değerlendiricilerine genellenmez; örneği burada çalıştırmadım. Lab standardında aday çözümü üretmeli, başarı ölçüsünü ayrı değerlendirici hesaplamalı. [İlgili kod](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/examples/function_minimization/evaluator.py)

Reddit'teki bir araştırmacı tartışmasında farklı baseline kodlarının veri hazırlama ve ayar farkları yüzünden birlikte çalıştırılmasının haftalar alması anlatılıyor. Bu anekdot bir yaygınlık ölçümü değil; ortak problem adaptörünün hangi sürtünmeyi azaltabileceğine dair kullanım sinyali. Bazı yorumlardaki yalnız yayımlanmış rakamlarla karşılaştırma önerisini bu lab için benimsemiyorum: mümkün olduğunda rakibi aynı veri ve bütçede çalıştırmalıyız. [Tartışma](https://www.reddit.com/r/MachineLearning/comments/1ah3qil)

## Önerilen standart

### 1. Yenilik, kazanç ve kullanım üç ayrı sonuç olsun

Her çalışma üç soruya cevap versin: Literatüre göre ne yeni? Aynı koşullarda hangi mevcut yöntemi geçiyor? Hangi gerçek işte fayda sağlıyor? Cevapların hepsinin olumlu olması şart değil. Bilinen bir mekanizma yararlı bir uygulamanın parçası olabilir; yeni bir teorem de henüz ürün olmayabilir.

Arşiv korunmalı; aktif mühendislik, kullanım hedefine bağlanan küçük bir alt kümede ilerlemeli. Kaynağı eksik bir tarihî ürün yeniden uygulanırsa yeni uygulama kimliği almalı; eski performansını otomatik olarak miras almamalı.

### 2. Ortak çalıştırma biçimi, açık matematiksel anlam

İlk pilot motorları için giriş, çıkış, varsayım ve maliyet tanımı yeterli. Alanlar yalnız `array` diye tanımlanmamalı: SACPS'in hata örnekleri, AICC'nin Gaussian inancı ve REL'in kayıt ilişkileri farklı nesneler. Aynı boyuttaki iki matrisin anlamı aynı olmayabilir.

Örneğin REL'in koşullu aday olasılıkları, AICC'nin Gaussian kovaryansı yerine doğrudan verilemez. Böyle bir birleşim için ayrı bir dönüşüm ve onun geçerli olduğu varsayımlar gerekir. Motorların birbirini gerçekten çağırdığı, ilgili girdiye tepki verdiği ve bir motor çıkarıldığında ne değiştiği de ölçülmeli.

### 3. Deney tanımını kullanım sorusuna bağla

Küçük bir problem paketi şu bilgileri taşısın: girdi, istenen çıktı, karşılaştırılacak mevcut yöntem, ana ölçü, çalışma bütçesi ve değerlendirme için ayrılan örnekler. Çalıştırıcı kod sürümü, hata, süre ve sonuçları otomatik kaydetsin. Bunlar yeni kullanıcı formları haline getirilmemeli.

Her yarışta basit ama makul bir yöntem, uygun bir yerleşik yöntem ve lab adayı bulunsun. Veri ve ayar bütçeleri karşılaştırılabilir olsun. İlgili durumlarda birleşimin bir parçasını çıkararak görünen kazancın nereden geldiği kontrol edilsin. Her değişiklikte bütün labın testlerini tekrar etmek gerekmez.

### 4. Bağımlılığı labın kendi kanıtlarında da hesaba kat

Aynı veri üreticisinden gelen yüz seed, yüz ayrı gerçek kullanım alanını temsil etmez. Aynı belgeden türemiş dosyalar eğitim ve son değerlendirme tarafına bölünmemeli. Grup kimliği, belgenin veya senaryonun asıl kaynağını izlemeli. Tek bir genel skor yerine kazanç, kötüleşen durumlar, maliyet ve kapsam görünmeli.

Mevcut [karşılaştırma kodu](./maintenance/compare.py) eşlenmiş sonuçlar, kötüleşen durumlar ve tekrar türleri için zaten bir başlangıç sunuyor. Bu kod verilen bağımsızlık beyanının doğru olduğunu kanıtlamıyor; problem paketlerinin bu anlamı sağlaması gerekiyor.

### 5. Araştırma birikimini yeniden kullan

Bir adayın başarısızlığı, başka bir adayın sonraki sınama örneği olsun. Her çalışmanın kısa kapanışı: hangi kod denendi, hangi durumda kazandı/kaybetti, sonucu değiştirebilecek bir sonraki soru ne? Mevcut çalıştırma kayıtları bunun kaynağı olabilir. Böylece sohbet bağlamı kaybolduğunda araştırma baştan başlamaz.

Keşif hattı devam edebilir; ilk dönemde eşzamanlı bir uygulama teslimi ve bir keşif sorusu öneriyorum. Bu bir endüstri standardı veya değişmez kapı değil; dağılmayı azaltmak için başlangıç tercihi.

## Labdan çıkabilecek üç somut hat

| Öncelik | Hat | İlk mekanizmalar | Gerçek değer nasıl anlaşılır? |
| --- | --- | --- | --- |
| 1 | Kanıtın ortak kaynağa bağımlılığı ve sonuç hassasiyeti | R207; uygun sayısal veri varsa SACPS/REL | Bilinen türeme ilişkilerinde yanlış bağımsızlık iddiaları, kaçırılan ilişkiler, sonucun hangi kaynakla değiştiği ve ek kullanıcı emeği |
| 2 | Aynı bütçeyle daha faydalı bilgi/inceleme seçimi | AICC, ACRA, DTTC; ölçüm için DLEW/MDDC yaklaşımı | Eşit maliyette bulunan önemli istisnalar veya eşit kapsama ulaşma maliyeti; kanal ve fayda varsayımlarının veriyle desteklenmesi |
| 3 | Korelasyon değişiminde rekürsif filtreleme | R204–R206 | Uygun gerçek çok değişkenli zaman serisinde hata, belirsizlik kapsamı ve gecikme; mevcut filtrelere karşı karşılaştırma |

Bunlar doğrulanmış pazar boşlukları değildir. Mevcut koddan hareketle sınanabilir kullanım hipotezleridir. Öncelik sırası, başlangıçtaki audit ve işe alınma hedefi gözetilerek önerilmiştir.

## İlk uygulama için önerim

**Kanıt bağımlılığı hattıyla başlamak.** İlk girdi türü, kaynak ilişkileri gerçekten gözlenebilen bir dosya ailesi olmalı; örneğin formül ve kaynak bağlantıları taşıyan çalışma kitapları. Bilinen türemeler, bağımsız kayıtlar ve belirsiz ilişkiler ayrı tutulmalı. Belge benzerliği tek başına aynı kaynağın veya istatistiksel bağımlılığın kanıtı sayılmamalı.

R207 yalnız açık öncül/sonuç kuralları kurulabildiği yerde kullanılmalı. Bir kaynağı çıkardığımızda hangi sonuçların dayanağını kaybettiğini hesaplamak makul bir ilk iş. Genel belge metninden bu kuralları kusursuz çıkardığı veya auditor opinion için kalibre edilmiş olasılık verdiği iddia edilmemeli. SACPS ve AICC de ancak ihtiyaç duydukları sayısal örnekler ve karar tanımı oluştuğunda eklenmeli.

İlk teslimin başarısı şu olmalı: aynı dosya paketinde, basit tekrar tespiti ve sıradan bağımlılık grafiği yaklaşımına göre ek olarak ne bulduğunu gösteren bir çıktı; doğru örnekler kadar yanlış alarmlar ve kaçırmalar; kullanıcıdan istenen işlem sayısı. Bağımlılık grafiğine gelişmiş bir motor eklemek ölçülebilir fayda sağlamazsa motoru o üründe kullanmanın gerekçesi yoktur.

Standardizasyonun ilk kapsamı bu deney için gereken motorlar, ortak problem paketi ve otomatik sonuç kaydı olmalı. Ardından ikinci bir problemde aynı altyapının yeniden kullanılabildiği gösterilmeli. Böylece standart, gerçekten yapılan işten türeyerek büyür.

## 16 Eylül: çalışma ortamı, verimlilik ve sıradaki onarımlar

Aktif repo `/Users/mertalituncer/Developer/lab`. Bu sohbetin kayıtlı çalışma alanı hâlâ eski `Documents/Codex/.../do-x20`; bu nedenle gerçek repoya yazma, bu görevde çalışma alanı dışına çıkıyor. Dosya taşıyarak ikinci bir aktif kopya üretmeyelim. Codex'te sonraki lab görevini **yerel proje olarak Developer/lab klasöründen** başlatmak bu farkı giderir. Projeyi sabitlemek yalnız görünümü değiştirir; eski sohbetin dosya erişimini taşımaz. İlgili işler aynı görevde devam edebilir; bağımsız bir sonuç için yeni görev açılır. Paralel kod değişiklikleri gerektiğinde worktree kullanılır; her soru için yeni kopya gerekmez. [Resmî proje açıklaması](https://learn.chatgpt.com/docs/projects), [worktree davranışı](https://learn.chatgpt.com/docs/environments/git-worktrees).

GitHub bağlantısı 16 Eylül'de `merttuncer07` hesabını ve `laballcompass` için `push` yetkisini bildirdi; main hâlâ `83a3a712f340a7826ace0478e553e18a09c23267`. Bu, terminal Git oturumu değildir: terminalin HTTPS kimliği önceki dry-run'da eksikti. GitHub işlemleri için mevcut uygulama bağlantısı kullanılabilir; sırf bu nedenle yeni ürün bağımlılığı eklenmez. Yazma işlemi denenmedi, kullanıcının commit/push bekletme isteği sürüyor. API deponun `public` olduğunu gösterdi; önceki özel-depo tanımıyla fark kullanıcıya soruldu, görünürlük değiştirilmedi.

**Gözlenen israf ve yapılan düzeltme:** `components` ve `show`, her aramada `catalog.json` yazdığı için salt okuma bile izin hatasına düşüyordu. Katalog toplama ile kaydetme ayrıldı; arama yine güncel kaynakları tarar, dosya yazmaz. Veri tazeliği için ikinci bir önbellek veya yeni servis eklenmedi. Karşılaştırma modülü de hesapladığı dosyaları hash için tekrar okuyordu; şimdi hesaplama ve parmak izi aynı okunmuş baytlardan üretilir. Testler ve değişen dosyalar `restoration/20260916-lab-operations/` altında kaydedilir.

**Bu lab için mimari tercihi:** motorlar kendi anlamlı Python API'lerini korusun; gerçek dosyaları görev girdisine çeviren adaptör, motor, değerlendirme ve dosyaya yazma birbirinden ayrılabilsin. Tek bir evrensel motor arayüzü dayatmayalım. Nevergrad'ın `Experiment._run_with_error` kodu deney fonksiyonunu kopyalar; `_log_results` sonucu problemin değerlendirme fonksiyonuyla ölçer. Optuna `_run_trial` normal bir hedef fonksiyonunu çağırır; kayıt ve geri çağrılar ayrı yoldadır, callback'e denemenin kopyası verilir. Bu kodları inceledim; bütün bu projeleri burada performans testine sokmadım. Lab için çıkarım, bu ayrımları ihtiyaç duyulan mevcut modüllerde uygulamak; framework'leri bütünüyle bağımlılık yapmak değil. [Nevergrad kodu](https://raw.githubusercontent.com/facebookresearch/nevergrad/main/nevergrad/benchmark/xpbase.py), [Optuna kodu](https://raw.githubusercontent.com/optuna/optuna/master/optuna/study/_optimize.py).

**Codex'i daha verimli kullanma:** bir görev “bir satır değiştir” kadar dar değil, tamamlanabilir bir yetenek olsun: örneğin “kaynak dosyası değişse de karşılaştırmanın gerçek girdisini koru; mevcut karşılaştırmaları bozma”. Katalogdan ilgili bileşeni bul; etkilenen kodu ve testi oku; uzun çıktıyı dosyada tut; sonuç, başarısızlık ve sonraki açık soruyu kısa kaydet. Yeni görevde bütün sohbeti kopyalamak yerine ilgili kaynak ve çalışma kaydını göster. Bu tercih ürünün iddiasını küçültmez; aynı keşfi tekrar etmeyi azaltır. `AGENTS.md` yalnız bu repo yollarını ve alışkanlıklarını taşır. Model, global ayarlar ve eklentiler değiştirilmedi.

Hashimoto'nun kendi deneyimi doğrulanabilir görevler ve gözlenen hatalara yönelik küçük kalıcı iyileştirmeleri destekliyor. Reddit'teki “tek iş/sohbet” tartışmasında daha az kota kullanımı bildiriliyor ama yeniden keşif maliyeti de belirtiliyor; gereksiz değişiklikler tartışmasının yazarı A/B ölçümü yapmadığını açıkça söylüyor. Bu anlatılardan yüzde tasarruf sonucu çıkarmıyoruz. Bizde doğrudan gözlenen sonuç, basit keşfin artık yazma gerektirmemesi; token/kota tasarrufu henüz karşılaştırmalı ölçülmedi. [Hashimoto](https://mitchellh.com/writing/my-ai-adoption-journey), [Reddit: görev bağlamı](https://www.reddit.com/r/codex/comments/1v1o463/i_drastically_reduced_my_codex_quota_usage_by/), [Reddit: gereksiz değişiklikler](https://www.reddit.com/r/codex/comments/1vtt9sy/has_anyone_else_noticed_how_much_token_usage/).

Sıradaki ürün işi kanıt bağımlılığı hattında kalıyor: `workbench/contracts.py` dışa verdiği sözlüklerin problem nesnesini değiştirmesini önlemeli; ardından SUMIF/AVERAGEIF'nin fiilen kullandığı aralığı çözen adaptör tamamlanmalı. Önceki geçici SUMIF taslağının yolu 16 Eylül'deki dosya kontrolünde bulunamadı; uygulanmış değişiklik gibi sayılmıyor. Gerçek bir kamu çalışma kitabındaki gözlenen fark, güçlü AND/OR referansıyla aynı bilgilerde gösterilmeli. İZ'in gerçek SVB paketi korunuyor; R207 için önceki üstünlük bulunamaması sonucu geçerli. ACSA/DREW grup onarımı tamamlanmış kayıtlarından sürdürülür; eski deneyler yeniden keşfedilmez.
