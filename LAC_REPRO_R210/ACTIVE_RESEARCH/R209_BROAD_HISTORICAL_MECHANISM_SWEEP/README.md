# R209 — Broad Historical Mechanism Sweep

Bu round R193–R208 portföyünü derinleştirmez ve ürün seçmez. On tarihî hattı
aynı düşük bütçeli protokolden geçirir: birincil çekirdek, gerçek darboğaz,
korunacak invariant, tek matematiksel mutasyon, ucuz tanık/karşı-örnek ve modern
çakışma sınırı.

## Çalıştırma

```powershell
$python = 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python -m pytest .\test_surface_sweep.py -q
& $python .\run_sweep.py
```

## Dosyalar

- `surface_sweep.py`: on bağımsız cebirsel/hesaplamalı ayrıştırıcı.
- `test_surface_sweep.py`: kapsam ve failure boundary testleri.
- `R209_RESULT.json`: deterministik ilk-tur ölçümleri.
- `R209_FIRST_PASS.md`: kaynaklar, cebir, sonuç ve nötr kararlar.
- `R209_DECISION.json`: sonraki tur için makine-okunur kısa hüküm.

## Ana sonuç

İlk turda global breakthrough ilan edilmedi. En kuvvetli yeni soru GDR
sonsuz-bölünebilir nokta-süreci cebirinden çıkan **controlled-thinning void
tomography** oldu: bounded cluster order altında exact tanımlanabilirlik var,
fakat mertebe arttıkça ters problem hızla ill-conditioned oluyor. İkinci
inceleme ancak bu conditioning darboğazını representation değişikliğiyle kırma
ve doğrudan prior-art collision taraması üzerine kurulmalıdır.

