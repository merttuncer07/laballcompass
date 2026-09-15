# R201 — Glushkov × Schützenberger XOR Direct-Sum Compiler

R199 vector-output composition'ı factor etmiş, XOR aggregation'da certificate'i
bilerek reddetmişti. R201 bu açık coordinate'i cebirsel olarak değiştirdi.

## Cebir

Her deterministic component state'i one-hot vector, her input symbol transition'ı
GF(2) lineer operatör olarak yazılabilir. Component'ler aynı input word'ü alırken
global transition tensor/product değil block-diagonal direct sum olur. İki global
state arasındaki XOR-output farkı:

```text
v0 = direct_sum_i (onehot(left_i) XOR onehot(right_i))
v(w) = A_w v0
different(w) = c^T v(w) mod 2
```

`{A_w v0}` reachable set'inin GF(2) span'i en fazla component state toplamı kadar
boyutludur. Compiler yeni independent image'ları Gaussian elimination ile ekler:

- `c^T v = 1` bulursa o actual reachable vector'a ait word exact witness'tır;
- reachable span'in tamamında `c^T v = 0` ise state'ler bütün word'lerde XOR-
  observationally equivalent'tır.

Full synchronized product kurulmaz.

## Sonuç

- 8 seed × 2/3/4 component × 180 query = **4,320** küçük oracle sorgusu;
- full-product BFS ile hüküm agreement: **4,320/4,320**;
- dönen bütün distinguishing word'ler doğrudan yeniden çalıştırmada geçerli;
- identical component `(p,q)` / `(q,p)` cancellation equivalence: **24/24**;
- scale stress: 64 component × 8 state;
- full product state sayısı **58 decimal digit**, direct-sum dimension **512**;
- observed maximum reachable-span dimension **12**;
- maximum witness length **3**;
- median decision yaklaşık **44.5 µs**.

## Hüküm

XOR-aggregated composition equivalence bottleneck'i bu sınıfta exact olarak
product'tan direct-sum linear reachability'ye indirildi. Bu gerçek ve güçlü bir
capability'dir.

Fakat weighted automata ile linear representations arasındaki eşdeğerlik
Schützenberger hattında, automata equivalence'ın linear-algebra çözümü de sonraki
literatürde bilinmektedir. Dolayısıyla R201 bir global novelty claim değil;
Glushkov composition/experiment problemini doğru algebraic representation'a
terfi eden çalışan bir yeniden keşif/bileşimdir.

Açık coordinate'ler:

- AND/OR ve genel nonlinear aggregation;
- asynchronous component clocks;
- hidden shared state/coupling;
- approximate/probabilistic output equivalence;
- prime-field/modular sum genellemesi;
- representation collision'ın tam bibliyografik haritası.

Status: `EXACT_MAJOR_CAPABILITY_PRIOR_ART_COLLISION_NOT_BREAKTHROUGH`

## Kaynaklar

- Glushkov, *The abstract theory of automata* (1961):
  https://www.mathnet.ru/eng/rm6668
- Weighted automata/linear representation ve Schützenberger theorem özeti:
  https://www-igm.univ-mlv.fr/~perrin/Livres/RationalSeries9April2010.pdf
- Tzeng, probabilistic automata equivalence için polynomial-time linear algebra
  (1992): https://doi.org/10.1137/0221017

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_xor_direct_sum.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' xor_direct_sum.py
```

