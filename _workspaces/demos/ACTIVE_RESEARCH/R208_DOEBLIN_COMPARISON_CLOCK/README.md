# R208 — Döblin comparison clock

## Sonuç

Döblin'in sealed manuscript'i baştan sona incelendi. Manuskript tam olarak ortak
diffusion ve ordered driftler için CDF comparison proof'u sırasında kesiliyor.
Sürekli-zaman sonucu modern comparison theory tarafından, random-clock çekirdeği
ise Dambis–Dubins–Schwarz tarafından özümsenmiş.

R208'in retained scoped mekanizması: raw Euler'in kaybedebildiği pathwise order
certificate'ını Lamperti/Döblin koordinatında step-size koşullu exact koruyan
shared-noise update. Bu bir breakthrough veya novelty claim değildir.

50,000 path benchmark'ında raw Euler order-failure oranı 10/20/50 step için
sırasıyla `%6.272 / %2.664 / %0.080`; transformed scheme 10/20/50/100/200
step'in tamamında `%0` ihlâl verdi. Bütün koşullarda nonfinite oranı `%0` idi.

Tam teori: `THEORY.md`
Makine-okunur sonuç: `R208_RESULT.json`
Karar: `R208_DECISION.json`

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\run_experiment.py
```
