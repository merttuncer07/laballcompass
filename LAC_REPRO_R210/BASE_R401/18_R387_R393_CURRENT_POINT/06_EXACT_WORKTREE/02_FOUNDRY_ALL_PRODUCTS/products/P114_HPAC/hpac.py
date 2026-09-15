from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P114', 'short_name': 'HPAC', 'title': 'Product result — P114_HPAC v0.1', 'parents_raw': 'MLHPE + AICC', 'historical_promotion_state': '', 'claim_boundary_raw': 'The Gaussian belief adapter uses the Chapman standard error and a declared linear expand/hold utility around a capacity threshold; it is not a full Bayesian posterior over capture dependence.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
