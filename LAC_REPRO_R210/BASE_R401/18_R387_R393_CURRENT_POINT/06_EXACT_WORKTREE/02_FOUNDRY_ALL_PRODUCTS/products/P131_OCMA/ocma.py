from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P131', 'short_name': 'OCMA', 'title': 'Product result — P131_OCMA v0.1', 'parents_raw': 'OWNM + ACRA', 'historical_promotion_state': '', 'claim_boundary_raw': 'The perturbation size is a declared audit tolerance; economic ownership and voting control remain separate.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
