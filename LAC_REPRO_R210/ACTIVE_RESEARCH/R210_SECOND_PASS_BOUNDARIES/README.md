# R210 — Second-Pass Boundaries

R209'dan ikinci tura kalan iki mekanizmanın theorem-level kapanışıdır.

- GDR controlled-thinning void tomography'nin yüksek-order conditioning sorunu
  için bütün real retention tasarımlarını kapsayan kör yön kuruldu.
- Zhuravlev affine corrector, bounded-degree Boolean polynomial closure'a
  genişletildi; fixed degree ve empirical generator rank altındaki exact
  compile-or-abstain sınırı çıkarıldı.

Çalıştırma:

```powershell
$python = 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python -m pytest .\test_second_pass.py -q
& $python .\run_second_pass.py
```

Sonuç: GDR adayının full-spectrum/void-only güçlü biçimi yapısal olarak öldü.
Zhuravlev genişlemesi exact fakat Boolean ANF/Reed–Muller evaluation cebriyle
çakıştığı ve generalization sağlamadığı için breakthrough değildir.

