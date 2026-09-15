from __future__ import annotations

import json
from pathlib import Path

from rel import ConsistencyRelation, EvidenceRecord, RelationalEvidenceLocalizer


def evaluate() -> dict[str, object]:
    records = [
        EvidenceRecord("buyer_order", "buyer", 100.0, 0.01),
        EvidenceRecord("seller_invoice", "seller", 120.0, 0.10),
        EvidenceRecord("warehouse_receipt", "warehouse", 100.0, 0.01),
        EvidenceRecord("carrier_manifest", "carrier", 100.0, 0.01),
        EvidenceRecord("bank_payment", "bank", 120.0, 0.08),
    ]
    sparse_relations = [
        ConsistencyRelation("order_matches_invoice", "buyer_order", "seller_invoice"),
        ConsistencyRelation("invoice_matches_payment", "seller_invoice", "bank_payment"),
    ]
    redundant_relations = sparse_relations + [
        ConsistencyRelation("order_matches_receipt", "buyer_order", "warehouse_receipt"),
        ConsistencyRelation("receipt_matches_manifest", "warehouse_receipt", "carrier_manifest"),
        ConsistencyRelation("invoice_matches_receipt", "seller_invoice", "warehouse_receipt"),
        ConsistencyRelation("invoice_matches_manifest", "seller_invoice", "carrier_manifest"),
        ConsistencyRelation("payment_matches_receipt", "bank_payment", "warehouse_receipt"),
    ]
    localizer = RelationalEvidenceLocalizer()
    sparse = localizer.localize(records, sparse_relations, max_colluding_records=2)
    redundant = localizer.localize(records, redundant_relations, max_colluding_records=2)
    return {
        "actual_altered_records": ["seller_invoice", "bank_payment"],
        "sparse_graph": {
            "relation_count": len(sparse_relations),
            "top_candidate": sparse["top_candidate"],
            "top_five": sparse["ranking"][:5],
        },
        "counterparty_generated_redundant_graph": {
            "relation_count": len(redundant_relations),
            "top_candidate": redundant["top_candidate"],
            "top_five": redundant["ranking"][:5],
            "observed_violations": redundant["observed_violations"],
        },
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("relational_localization_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
