from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P059', 'short_name': 'SBTE', 'title': 'P059 SBTE v0.1 — Safeguard Budget Tipping Explorer', 'parents_raw': 'CSID → TDSX. At each budget, CSID chooses its economically preferred safeguard portfolio. TDSX finds the nearest budget where the selected portfolio reaches a declared residual-loss target.', 'historical_promotion_state': 'WORKING_COMPOSITION / SAFEGUARD-BUDGET BENCHMARK', 'claim_boundary_raw': '', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
