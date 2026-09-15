from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P103', 'short_name': 'CFAI', 'title': 'Product result — P103_CFAI v0.1', 'parents_raw': 'HFAD + BICC + ACRA', 'historical_promotion_state': '', 'claim_boundary_raw': 'Circulation is a flow-topology signal, not a fraud label. The current benchmark uses empirical influence only because no global edge-flow bound is supplied.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
