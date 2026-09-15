"""Versioned, deterministic problem families; seeds are not independent domains."""
from itertools import combinations
import random
from .contracts import DependencyProblem


def evidence_demo():
    return DependencyProblem('shared_source_and_alternative_route',
        {'ledger': 'client_ledger', 'extract': 'client_ledger', 'slide': 'client_ledger',
         'confirmation': 'external_confirmation', 'receipt': 'receipt_record'},
        (('reconciliation', ('ledger', 'extract')),
         ('summary_check', ('slide',)),
         ('claim', ('reconciliation', 'summary_check')),
         ('claim', ('confirmation', 'receipt'))), ('claim', 'reconciliation', 'summary_check'),
        metadata={'origin': 'Synthetic, explicitly declared support rules; not extracted audit assertions.',
                  'title': 'Üç görünüm, bir kaynak; ikinci bir destek yolu',
                  'labels': {'client_ledger': 'Müşteri defteri (3 türev görünüm)',
                             'external_confirmation': 'Harici teyit kaydı', 'receipt_record': 'Tahsilat kaydı',
                             'claim': 'Örnek iddia', 'reconciliation': 'Mutabakat', 'summary_check': 'Özet kontrolü'},
                  'assumptions': ['Either declared route suffices only in this synthetic example.',
                                  'Distinct source IDs do not prove statistical independence.']})


def choice_blocks(count):
    bases = {f'{s}{i}': f'{s}{i}' for i in range(count) for s in ('a', 'b')}
    rules = [(f'c{i}', (f'{s}{i}',)) for i in range(count) for s in ('a', 'b')]
    rules.append(('target', tuple(f'c{i}' for i in range(count))))
    return DependencyProblem(f'choice_blocks_{count}', bases, tuple(rules), ('target',),
                             metadata={'family': 'factored_choices', 'synthetic': True,
                                       'analytical_minimal_support_count': 2**count})


def random_dag(seed, nodes=65, source_count=12):
    rng = random.Random(seed)
    bases = {f'b{i}': f's{i // 2}' for i in range(source_count * 2)}
    prior = list(bases)
    rules = []
    for i in range(nodes):
        head = f'n{i}'
        for _ in range(rng.randint(1, 3)):
            body = tuple(rng.sample(prior, min(len(prior), rng.randint(1, 3))))
            rules.append((head, body))
        prior.append(head)
    return DependencyProblem(f'random_dag_{seed}', bases, tuple(rules), tuple(prior[-4:]),
                             metadata={'family': 'random_dag', 'seed': seed, 'synthetic': True})


def suite():
    yield evidence_demo()
    yield DependencyProblem('empty_body_axiom', {'a': 'A'}, (('truth', ()),), ('truth',), metadata={'family': 'axiom'})
    yield DependencyProblem('shared_mandatory', {'a': 'A', 'b': 'B', 'c': 'C'},
                            (('target', ('a', 'b')), ('target', ('a', 'c'))), ('target',), metadata={'family': 'shared_mandatory'})
    for n in (4, 12, 24): yield choice_blocks(n)
    for seed in range(8): yield random_dag(seed)
    rules = tuple((f'n{i}', ('b' if i == 0 else f'n{i-1}',)) for i in range(1200))
    yield DependencyProblem('deep_chain_1200', {'b': 'root'}, rules, ('n1199',), metadata={'family': 'deep_chain'})


def failure_scenarios(problem, pair_limit=512):
    sources = problem.sources
    rows = [frozenset(), *(frozenset((s,)) for s in sources)]
    count = len(sources) * (len(sources) - 1) // 2
    if count <= pair_limit:
        pairs = list(combinations(sources, 2))
    else:
        rng = random.Random(20260914)
        sampled = set()
        while len(sampled) < pair_limit:
            sampled.add(tuple(sorted(rng.sample(sources, 2))))
        pairs = sorted(sampled)
    rows.extend(frozenset(p) for p in pairs)
    all_removed = frozenset(sources)
    if all_removed not in rows: rows.append(all_removed)
    return rows


def reference_truth(problem, removed):
    """Separate least-fixed-point semantics; does not import any candidate engine."""
    enabled = {node for node, source in problem.bases.items() if source not in removed}
    changed = True
    while changed:
        changed = False
        for head, body in reversed(problem.rules):
            if head not in enabled and set(body) <= enabled:
                enabled.add(head)
                changed = True
    return {target: target in enabled for target in problem.targets}
