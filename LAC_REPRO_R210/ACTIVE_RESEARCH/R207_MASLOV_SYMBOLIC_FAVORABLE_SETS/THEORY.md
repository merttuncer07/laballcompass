# R207 — Maslov favorable set'lerini enumerate etmek yerine compile etmek

## 1. Tarihî mekanizma

Maslov'un 1964 inverse method'u, bir hedef formülden yalnız geriye doğru dalmak
yerine closed ve ardından favorable `F`-sets üretir. Empty favorable set'in elde
edilmesi derivability'yi verir. Maslov'un kendi metni yöntemin avantajını şöyle
konumlandırır: yeni favorable set'ler problemi basitleştirebilir ve bazen
gözlemlenemeyecek kadar büyük bir proof'u daha küçük alt problemlere indirebilir.
Ancak bütün favorable set'leri üretmek yine saturation ve bellek patlaması
yaratabilir.

Modern inverse-method anlatımı aynı sınırı daha doğrudan söyler: forward search
backtracking'i azaltır, fakat retained sequent sayısı nedeniyle space problemi
yaşar. Subsumption yalnız redundant supersets'i siler. Geriye kalan minimal
supports bir antichain'dir ve antichain'in kendisi üstel büyük olabilir.

Kaynaklar:

- Maslov 1964 birincil metin:
  https://www.mathnet.ru/php/getFT.phtml?jrnid=dan&option_lang=rus&paperid=30298&what=fullt
- CMU inverse-method notları:
  https://www.cs.cmu.edu/~fp/courses/15317-s23/lectures/22-invmethod.pdf

## 2. Darboğazın doğru matematiksel nesnesi

Sonlu bir ground/subformula-finite inverse rule hypergraph'ı ele alalım.
`X={x_1,...,x_m}` başlangıç axiom/fact etiketleri olsun. Bir sonuç `v` için

\[
\mathcal M(v)\subseteq 2^X
\]

`v`yi üreten subset-minimal proof supports ailesi olsun. Alternatif proof'lar
union, birlikte gereken premises ise set-union product üretir:

\[
\mathcal A\oplus\mathcal B
=\min_{\subseteq}(\mathcal A\cup\mathcal B),
\]

\[
\mathcal A\otimes\mathcal B
=\min_{\subseteq}\{A\cup B:A\in\mathcal A,B\in\mathcal B\}.
\]

Buradaki absorption

\[
A\subseteq B \quad\Longrightarrow\quad A\oplus B=A
\]

Maslov/subsumption mantığının tam karşılığıdır. Fakat absorption üstel geniş bir
minimal antichain'i küçültmek zorunda değildir.

## 3. Değiştirilen temsil

Her minimal support'u ayrı saklamak yerine onun upward closure'ını monotone bir
Boolean function olarak sakla:

\[
F_v(S)=1
\iff
\exists A\in\mathcal M(v):A\subseteq S.
\]

Base fact `x` için `F_x=x`. Her rule

\[
u_1,\ldots,u_k\longrightarrow v
\]

şu circuit katkısını verir:

\[
F_v\leftarrow F_v\lor\bigwedge_{i=1}^kF_{u_i}.
\]

Yani support-family cebirindeki `\(\oplus\)` ve `\(\otimes\)`, factored temsilde doğrudan
`or` ve `and` kapılarına dönüşür. `x or (x and y)=x` absorption yasasıdır.

## 4. Temsil teoremi

**Teorem.** `H` sonlu ve acyclic bir proof-rule hypergraph olsun. Yukarıdaki
recurrence ile kurulan monotone circuit `C_v`, her `\(S\subseteq X\)` için

\[
C_v(1_S)=1
\iff
\exists A\in\mathcal M(v):A\subseteq S
\]

eşitliğini sağlar. Circuit DAG hash-consing ile

\[
O\left(|X|+|R|+\sum_{r\in R}|body(r)|\right)
\]

kapı içinde kurulabilir; bu bound `|M(v)|`ye bağlı değildir.

**İspat.** Topological order üzerinde induction yap. Base case'te `x`, tam olarak
`x in S` ise true'dur. Bir rule'un bütün premises'i true ise induction
hypothesis ile her premise için bir support `\(A_i\subseteq S\)` vardır; union
`cup_i A_i` rule'un support'udur ve `S` içindedir. Tersine rule support'u `S`
içindeyse onu oluşturan her premise support'u da `S` içindedir; AND true, rule
alternatifleri arasındaki OR true olur. Subset-minimalization, yalnız aynı
upward closure'ı veren absorbed supersets'i kaldırdığı için Boolean semantics'i
değiştirmez. Circuit size her base, rule ve premise incidence için sabit sayıda
node/edge sayılarak elde edilir. ∎

## 5. Üstel ayrım

`n` bağımsız seçim bloğu kur:

\[
p_i\leftarrow a_i,
\qquad p_i\leftarrow b_i,
\qquad goal\leftarrow p_1,\ldots,p_n.
\]

Her minimal support her çiftten tam bir eleman seçer:

\[
|\mathcal M(goal)|=2^n.
\]

Fakat circuit

\[
F_{goal}=\bigwedge_{i=1}^n(a_i\lor b_i)
\]

yalnız linear büyür. R207 deneyi `n=16` için 65,536 explicit support'u gerçekten
oluşturdu. Aynı compiler `n=4096` ve implicit `2^4096` minimal support'u küçük
bir factored circuit'te tuttu.

Bu sonuç “proof sayısı azaldı” demek değildir. Proof family enumerate edilmedi;
decision semantics ve istenirse on-demand witness extraction korunarak compile
edildi.

## 6. Cyclic saturation ve neden tek temsil yetmiyor

Acyclic proof DAG'da structural circuit yeterlidir. Cyclic finite rule graph'ta
least fixed point gerekir. R207 bunun için canonical ROBDD kullanır: iki Boolean
function aynı ise node identity de aynıdır ve saturation gerçekten durduğunu
anlar.

Ancak ROBDD genel çözüm değildir. Aynı

\[
\bigwedge_i(a_i\lor b_i)
\]

fonksiyonunda interleaved order `a_1,b_1,a_2,b_2,...` linear kalırken split
order `a_1,...,a_n,b_1,...,b_n` exponential node üretir. Deney bu farkı ayrıca
ölçer. Dolayısıyla retained mekanizma:

1. acyclic/factored bölgede variable-order-free proof circuit;
2. equality/fixed-point gereken küçük cyclic boundary'de canonical diagram;
3. diagram büyürse onu evrensel çözüm saymama.

Bu üçüncü madde henüz tam otomatik separator compiler değildir; açık devam
noktasıdır.

## 7. Ne çözüldü, ne çözülmedi?

Çözülen scoped problem:

- finite ground/subformula-finite acyclic inverse rule graph'ta explicit minimal
  favorable-set enumeration decision için gereksizdir;
- aynı exact semantics linear-size rule circuit'te tutulabilir;
- finite cyclic graph'ta canonical BDD ile exact least fixed point alınabilir;
- exponential separation executable counterexample ile gösterilmiştir.

Çözülmeyen:

- first-order term generation ve unification sonsuzluğunun kendisi;
- bütün variable order'larda küçük canonical diagram;
- arbitrary factored circuit equivalence'inin ucuz çözümü;
- full Maslov calculus için end-to-end competitive prover;
- publication novelty.

## 8. Collision audit

Bu cebirin genel fikri yeni diye sunulamaz. Green, Karvounarakis ve Tannen
provenance'i semiring expressions olarak kurdu; Datalog'a uzattı. Daha sonra
absorptive semirings `x+xy=x` yasasını açık biçimde formalize etti. Datalog
provenance circuits için polynomial-overhead sonuçlar da vardır. Minato'nun ZDD
hattı set-family compression için doğrudan bir başka collision'dır.

- Provenance semirings:
  https://www.cs.ucdavis.edu/~green/papers/pods07.pdf
- Circuits for Datalog provenance:
  https://www.math.tau.ac.il/~milo/projects/bpq/papers/icdt14b.pdf
- Absorptive fixed-point provenance:
  https://doi.org/10.4230/LIPIcs.CSL.2021.17
- Zero-suppressed BDD:
  https://doi.org/10.1145/157485.164890

Doğru R207 iddiası bu nedenle “yeni proof-circuit cebiri” değildir. Elde edilen
ilerleme, Maslov favorable-set darboğazının exact absorptive-support semantics'e
çevrilmesi, açık exponential counterexample ve hangi parçanın circuit, hangi
parçanın canonical quotient istediğinin ayrılmasıdır.
