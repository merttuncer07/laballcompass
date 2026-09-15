from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P088', 'short_name': 'LFTS', 'title': 'P088_LFTS — Lumpability Fragility Tipping Surface', 'parents_raw': 'SALC + TDSX', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'The perturbation is a declared stochastic-matrix path. Exceeding the error budget means the chosen aggregation certificate fails on that path, not that all possible aggregations fail.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
