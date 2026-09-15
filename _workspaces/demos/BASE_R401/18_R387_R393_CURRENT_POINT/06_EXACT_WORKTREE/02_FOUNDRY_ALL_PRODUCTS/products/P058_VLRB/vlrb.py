from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P058', 'short_name': 'VLRB', 'title': 'P058 VLRB v0.2 — Verified-Liquidity Redemption Buffer', 'parents_raw': 'LCM → explicit TRUE_SALE adapter → OFLS. LCM-financed claim face is removed from the liquidatable asset book, proceeds are added to cash, and any face/proceeds discount is written into NAV before OFLS redemption simulation.', 'historical_promotion_state': 'WORKING_COMPOSITION / BALANCE-SHEET-COMPATIBLE LIQUIDITY BENCHMARK', 'claim_boundary_raw': '', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
