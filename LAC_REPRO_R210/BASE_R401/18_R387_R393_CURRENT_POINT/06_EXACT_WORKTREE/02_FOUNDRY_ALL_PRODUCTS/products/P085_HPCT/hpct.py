from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P085', 'short_name': 'HPCT', 'title': 'P085_HPCT — Hidden Population Capacity Tipping', 'parents_raw': 'MLHPE + TDSX', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'The surface perturbs an observed capture-history count and refits MLHPE at every point. Akaike model averaging is a declared decision convention, not a literal posterior over population models.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
