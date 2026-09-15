from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P091', 'short_name': 'DCBT', 'title': 'P091_DCBT — Decision Compression Budget Tipping', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'The result is conditional on the supplied beliefs, utilities, and declared tolerance grid.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
