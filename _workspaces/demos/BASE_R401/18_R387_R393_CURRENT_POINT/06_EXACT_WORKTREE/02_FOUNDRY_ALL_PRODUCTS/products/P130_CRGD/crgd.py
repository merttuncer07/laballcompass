from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P130', 'short_name': 'CRGD', 'title': 'Product result — P130_CRGD v0.1', 'parents_raw': 'SCCRT + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Feed-block outages and failure probabilities are declared scenarios; no universal catalyst reliability claim is made.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
