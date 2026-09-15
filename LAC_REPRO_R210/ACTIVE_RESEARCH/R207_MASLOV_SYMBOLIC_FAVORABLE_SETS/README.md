# R207 — Maslov symbolic favorable-set compiler

## Kısa hüküm

Maslov inverse method'un explicit favorable/minimal-support üretim darboğazı,
sonlu acyclic rule graph sınıfında kırıldı: bütün minimal set'leri enumerate
etmek yerine aynı upward-closed semantics factored monotone proof circuit olarak
compile ediliyor. Ailenin kendisi `2^n` iken circuit linear kalabiliyor.

Bu universal first-order theorem proving çözümü veya kurulmuş novelty değildir.
First-order unification/term growth açık; canonical BDD ayrıca variable-order
patlaması gösterebilir. Provenance semiring/circuit literatürüyle güçlü collision
vardır.

Tam matematik ve sınırlar: `THEORY.md`

## İlk deney

- 16 bağımsız seçim bloğu: explicit antichain `65,536` minimal support ve
  `1,048,576` support atomu; factored circuit `49` reachable node.
- Aynı function için interleaved ROBDD `34`, kötü split order ROBDD `131,072`
  reachable node: canonical diagram'ın order failure'ı gizlenmedi.
- 4,096 blok: implicit support sayısı `2^4096`, factored circuit `12,289` node.
- Beş unit test exact semantics, exponential separation, cyclic fixed point ve
  order failure boundary için geçti.

Karar: `THEORETICAL_MECHANISM_RETAINED_COLLISION_HEAVY_NOT_BREAKTHROUGH`.

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\run_experiment.py
```

