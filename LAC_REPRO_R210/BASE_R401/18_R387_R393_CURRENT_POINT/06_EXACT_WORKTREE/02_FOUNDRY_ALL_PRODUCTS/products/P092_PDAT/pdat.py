from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P092', 'short_name': 'PDAT', 'title': 'P092_PDAT — Private Decision Accuracy Tipping', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Exact adapter currently covers one public threshold/two actions and is a utility calculation, not a new privacy theorem.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
