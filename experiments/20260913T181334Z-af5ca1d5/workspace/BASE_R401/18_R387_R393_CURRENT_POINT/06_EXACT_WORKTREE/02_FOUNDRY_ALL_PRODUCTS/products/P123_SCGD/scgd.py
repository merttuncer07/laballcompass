from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P123', 'short_name': 'SCGD', 'title': 'Product result — P123_SCGD v0.1', 'parents_raw': 'SACPS + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'The holdout covariance is treated as protected evaluation evidence; support-edge failure probabilities remain declared inputs.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
