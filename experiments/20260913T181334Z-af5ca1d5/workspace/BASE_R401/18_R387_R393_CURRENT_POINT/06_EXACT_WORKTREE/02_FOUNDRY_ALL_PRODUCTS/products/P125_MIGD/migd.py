from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P125', 'short_name': 'MIGD', 'title': 'Product result — P125_MIGD v0.1', 'parents_raw': 'MCRIS + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Lever-failure probabilities and guard effectiveness are declared; the benchmark does not estimate implementation-failure rates.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
