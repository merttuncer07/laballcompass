from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P093', 'short_name': 'BMDT', 'title': 'P093_BMDT — Belief Metric Decision Tipping', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Path-local result; it is not a global adversarial belief radius.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
