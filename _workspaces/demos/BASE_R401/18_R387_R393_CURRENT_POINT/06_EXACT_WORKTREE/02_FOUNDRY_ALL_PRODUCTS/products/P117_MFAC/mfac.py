from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P117', 'short_name': 'MFAC', 'title': 'Product result — P117_MFAC v0.1', 'parents_raw': 'MCPR + AICC', 'historical_promotion_state': '', 'claim_boundary_raw': 'The shortage threshold is grid-relative and conditional on fixed offer quantities/prices and the declared scarcity-price convention.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
