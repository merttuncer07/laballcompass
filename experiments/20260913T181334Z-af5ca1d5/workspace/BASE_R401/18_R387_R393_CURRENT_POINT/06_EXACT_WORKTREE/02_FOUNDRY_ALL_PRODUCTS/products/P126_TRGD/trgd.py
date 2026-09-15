from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P126', 'short_name': 'TRGD', 'title': 'Product result — P126_TRGD v0.1', 'parents_raw': 'DTRM + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'DTRM indices are local to the declared linear shell, horizon, uncertainty radius, and decision gap; safeguard failure probabilities are declared inputs.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
