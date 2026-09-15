from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P102', 'short_name': 'LLFD', 'title': 'Product result — P102_LLFD v0.1', 'parents_raw': 'SLERM + TFLD', 'historical_promotion_state': '', 'claim_boundary_raw': 'The episode-fraction localization requirement is user-declared; it is not a universal physical constant. No dangerous energy-transferring lock-in means no localization design is emitted.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
