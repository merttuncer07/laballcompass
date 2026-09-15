from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P115', 'short_name': 'PAAC', 'title': 'Product result — P115_PAAC v0.1', 'parents_raw': 'PRIU + AICC', 'historical_promotion_state': '', 'claim_boundary_raw': 'The threshold is grid-relative and uses the declared single-scenario appraisal adapter; measurement costs must be expressed in the same utility scale.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
