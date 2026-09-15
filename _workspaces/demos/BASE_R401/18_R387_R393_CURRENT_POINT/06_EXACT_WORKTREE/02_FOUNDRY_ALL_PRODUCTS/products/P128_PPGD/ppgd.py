from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P128', 'short_name': 'PPGD', 'title': 'Product result — P128_PPGD v0.1', 'parents_raw': 'PCBE + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Cell replacement is a declared physical stress, not a causal failure-rate estimate.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
