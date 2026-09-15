from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P083', 'short_name': 'HEAG', 'title': 'P083_HEAG — Historical Evidence Acquisition Gate', 'parents_raw': 'EBC + AICC', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Historical estimates are borrowed only under EBC compatibility/cap rules. A lower measurement value after borrowing does not imply historical evidence is correct; strong conflict should suppress borrowing.', 'execution_mode': 'allocation'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
