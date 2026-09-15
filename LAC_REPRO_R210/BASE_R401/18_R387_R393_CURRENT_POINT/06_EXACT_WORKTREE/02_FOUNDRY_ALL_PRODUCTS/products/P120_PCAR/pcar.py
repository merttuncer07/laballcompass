from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P120', 'short_name': 'PCAR', 'title': 'Product result — P120_PCAR v0.1', 'parents_raw': 'CWC + DTPR', 'historical_promotion_state': '', 'claim_boundary_raw': 'Differential privacy applies to the released miss-count action under the declared neighboring-dataset definition; internal CWC state remains trusted computation.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
