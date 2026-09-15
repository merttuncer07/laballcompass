from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P067', 'short_name': 'DARA', 'title': 'Deployability-Aware Resolution Allocator', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': '', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
