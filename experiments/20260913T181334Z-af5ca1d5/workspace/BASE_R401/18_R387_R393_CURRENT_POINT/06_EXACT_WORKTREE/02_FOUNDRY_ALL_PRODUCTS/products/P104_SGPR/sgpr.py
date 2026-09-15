from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P104', 'short_name': 'SGPR', 'title': 'Product result — P104_SGPR v0.1', 'parents_raw': 'OWS + DTPR', 'historical_promotion_state': '', 'claim_boundary_raw': 'Privacy does not certify statistical validity, and OWS does not certify the externally declared global sensitivity of the DTPR score.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
