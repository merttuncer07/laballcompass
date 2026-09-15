from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P099', 'short_name': 'CAPA', 'title': 'Product result — P099_CAPA v0.1', 'parents_raw': 'CAPL + ACSA', 'historical_promotion_state': '', 'claim_boundary_raw': 'The benchmark is a regime-shift stress test. Per-period loss uses net return plus the declared local risk penalty; it is not a universal portfolio utility.', 'execution_mode': 'allocation'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
