from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P082', 'short_name': 'CDTS', 'title': 'P082_CDTS — Channel Dominance Tipping Surface', 'parents_raw': 'CDA + TDSX', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Blackwell dominance is exact only on the declared binary experiment family; the tipping surface does not extrapolate beyond the supplied channel grid.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
