from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P084', 'short_name': 'CAVT', 'title': 'P084_CAVT — Control Authority Viability Tipping', 'parents_raw': 'CCVC + TDSX', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Local boundary viability is certified for the declared linear dynamics, conservation manifold, safe polytope and actuator bounds. This is not a global nonlinear safety certificate.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
