from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P105', 'short_name': 'PRAS', 'title': 'Product result — P105_PRAS v0.1', 'parents_raw': 'ACSA + DTPR', 'historical_promotion_state': '', 'claim_boundary_raw': 'The utility-sensitivity bound is caller-supplied and must be valid under the neighboring-dataset definition. Internal access to protected losses remains trusted computation.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
