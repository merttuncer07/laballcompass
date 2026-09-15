from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P086', 'short_name': 'FPSD', 'title': 'P086_FPSD — Failure Path Safeguard Designer', 'parents_raw': 'MFPA + CSID', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Failure consequence is the drop in worst-case dissipation energy under a fixed optimized architecture. Safeguard probabilities/coverage are declared inputs and require empirical calibration.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
