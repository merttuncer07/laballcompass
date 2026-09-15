from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P118', 'short_name': 'MRAC', 'title': 'Product result — P118_MRAC v0.1', 'parents_raw': 'MCRIS + AICC', 'historical_promotion_state': '', 'claim_boundary_raw': 'The default-rate belief is a one-dimensional adapter with other transition rates and intervention terms held fixed.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
