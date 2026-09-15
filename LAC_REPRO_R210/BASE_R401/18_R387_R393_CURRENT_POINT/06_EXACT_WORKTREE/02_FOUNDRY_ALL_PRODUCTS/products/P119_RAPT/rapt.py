from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P119', 'short_name': 'RAPT', 'title': 'Product result — P119_RAPT v0.1', 'parents_raw': 'CBAC + TDSX', 'historical_promotion_state': '', 'claim_boundary_raw': 'The pool-size floor is a design requirement, not a universal causal-validity threshold; the tipping value is relative to the declared randomization-draw count.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
