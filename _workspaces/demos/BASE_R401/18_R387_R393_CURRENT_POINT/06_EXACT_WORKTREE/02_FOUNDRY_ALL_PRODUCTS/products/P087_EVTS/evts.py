from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P087', 'short_name': 'EVTS', 'title': 'P087_EVTS — Exploration Value Tipping Surface', 'parents_raw': 'DRE + TDSX', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'The surface uses DRE Gaussian-arm assumptions and the declared cost/horizon grid. The reported interaction tipping is not an asymptotic exploration theorem.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
