from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P057', 'short_name': 'FIAC', 'title': 'P057 FIAC v0.1 — Firewalled Information Acquisition Controller', 'parents_raw': 'MIFF → AICC. MIFF removes suspect-source information-flow paths to the protected controller; AICC then ranks only the channels whose source modules remain reachable after the firewall.', 'historical_promotion_state': 'WORKING_COMPOSITION / INFORMATION-FIREWALL BENCHMARK', 'claim_boundary_raw': '', 'execution_mode': 'allocation'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
