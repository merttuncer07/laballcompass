from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P078', 'short_name': 'IARA', 'title': 'Influence-Aware Resolution Allocator', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'Observed replacement influence is a consequence proxy, not proof of causal effect or adversarial realizability. Global concentration claims still require valid caller-supplied bounds; IARA uses the empirical influence audit for allocation.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
