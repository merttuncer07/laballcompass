from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P121', 'short_name': 'MSGD', 'title': 'Product result — P121_MSGD v0.1', 'parents_raw': 'MCPR + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Offer-outage probabilities and shortage unit cost are declared scenario inputs; this does not infer physical outage rates.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
