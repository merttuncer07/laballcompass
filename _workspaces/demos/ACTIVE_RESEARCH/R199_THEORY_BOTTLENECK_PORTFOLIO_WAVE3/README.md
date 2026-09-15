# R199 — Theory Bottleneck Portfolio, Wave 3

Bu wave Tsetlin'in binary response sınırını, Glushkov'un automata composition
patlamasını ve Chebyshev–Markov extremal moment bound'larının karar/witness
eksikliğini test etti.

## HM-05 — Tsetlin rank-coded finite response

### Mutasyon

Her action başına yalnız 8-bit state korunarak binary favourable/unfavourable
response, bounded ödülün 256 seviyeli rank response'una çevrildi. State doğrudan
ödül toplamı değildir; hedef reward level'a doğru sonlu geçişlerle hareket eder.

96 bandit vakasında:

- rank response binary response'u **85/96** geçti;
- payout mean regret `513.91 -> 86.10`;
- drift mean regret `572.00 -> 243.87`;
- fakat her rejim için ayrı tune edilmiş UCB/EWMA ailesine karşı yalnız **7/96**
  kazandı ve dört rejimin hiçbirinde en iyi baseline'ın `%10` bandına girmedi.

Binary feedback'in bilgi kaybı gerçekten kırıldı. Fakat bu finite-state learner,
modern policy-selection bottleneck'ini kırmadı. Yeni state-allocation veya
counterfactual credit algebra olmadan yüksek öncelikli survivor değildir.

Status: `BINARY_RESPONSE_BROKEN_FINITE_STATE_MODERN_POLICY_EDGE_UNPROVEN`

## HM-06 — Glushkov separability-certified composition

### Mutasyon

Global automaton'ın gözlemi component output vector olarak ayrışıyorsa, full
Cartesian product automaton kurulmadı. Her component için distinguishing-word
characterization set'i çıkarıldı; global state fingerprint'i local output
fingerprint'lerinin tuple'ı oldu.

8 seed × 2/4/6/8 component = 32 vaka:

- 15,000 random global-state pair/vaka üzerinde exact ayrım **32/32**;
- median characterization set yalnız **7 word**;
- 8 component × 6 state için full product **1,679,616 state**;
- factor representation geçiş hücresinde median **34,992×** küçüldü;
- iki aynı component'in `(p,q)` ve `(q,p)` state'leri XOR output altında bütün
  word'lerde indistinguishable kaldı; vector certificate'in aggregated output'a
  yanlış taşınması **32/32** reddedildi.

Bu, vector-observable composition sınıfında state explosion'ı exact olarak
kırar. Genel composition'ı çözmez: shared hidden state, synchronized constraints
ve XOR/AND gibi aggregated observations ayrı quotient cebiri ister.

Status: `VECTOR_OBSERVATION_COMPOSITION_EXACTLY_FACTORIZED_AGGREGATION_OPEN`

## HM-13 — Extremal atomic decision compiler

### Mutasyon

Sabit finite support grid, mean ve variance verildiğinde bütün feasible üç-atomlu
moment temsilleri enumerate edildi. Böylece yalnız tail bound değil, şu üçlü aynı
anda çıktı:

```text
minimum safe threshold
worst-case tail probability
bound'u gerçekleştiren atom locations + weights
```

18 interior ve 18 boundary-skew dağılımında:

- gerçek dağılım safe: **36/36**;
- extremal atomic witness alpha sınırında: **36/36**;
- interior'da Cantelli ile aynı: **0/18 improvement**;
- boundary-skew'da **18/18 improvement**, mean threshold reduction `0.74167`.

Support bilgisi Cantelli extremizer'ının support dışına çıktığı boundary rejiminde
büyük değer açıyor; interior'da hiçbir şey kazandırmıyor. Fakat finite-support
moment problem'in linear programming/extreme-point çözümü bilinen prior art'tır.
Lab ilerlemesi bound'u executable threshold ve explicit adversarial witness ile
tek compiler'a çevirmektir; novelty/breakthrough değildir.

Status: `FINITE_SUPPORT_DECISION_AND_EXTREMAL_WITNESS_COMPILED_PRIOR_ART`

## Birincil/komşu kaynaklar

- Tsetlin, *Finite automata and models of simple forms of behaviour* (1963):
  https://www.mathnet.ru/eng/rm6373
- Glushkov, *The abstract theory of automata* (1961), özellikle composition ve
  experiments bölümleri:
  https://www.mathnet.ru/eng/rm6668
- Discrete moment problem and linear programming (1990):
  https://doi.org/10.1016/0166-218X(90)90068-N

Compositional verification/testing, finite-state bandits ve distributionally
robust moment optimization ile collision audit açıktır.

## Çalıştırma

```powershell
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v test_wave3.py
& 'C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' wave3.py
```

