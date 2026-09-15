from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P116', 'short_name': 'FCAC', 'title': 'Product result — P116_FCAC v0.1', 'parents_raw': 'FCMS + AICC', 'historical_promotion_state': '', 'claim_boundary_raw': 'The measurement target is specimen thickness only; material defects and other manufacturing tolerances are outside this adapter.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
