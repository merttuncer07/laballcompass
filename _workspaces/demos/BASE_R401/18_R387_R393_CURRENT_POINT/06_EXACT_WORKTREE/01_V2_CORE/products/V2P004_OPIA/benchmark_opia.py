from __future__ import annotations
import json
from pathlib import Path
from test_opia import near, far, run


def main():
    neutral=run(near(),0.0)
    confounded=run(near(),.05)
    stable=run(far(),0.0)
    out={
        "product_id":"V2P004_OPIA",
        "composition":"LCB-K081 ObservationPolicyConfoundingGuardV0 -> FOUNDRY:P138 SPIA",
        "neutral_near_boundary":neutral.to_dict(),
        "confounded_harmful_backaction":confounded.to_dict(),
        "neutral_far_boundary":stable.to_dict(),
        "decision_flip":{
            "base_chosen_channel":confounded.base_chosen_channel,
            "guarded_chosen_channel":confounded.chosen_channel,
            "base_net_value":confounded.ranked_channels[0]["base_net_value"],
            "guarded_net_value":confounded.ranked_channels[0]["adjusted_net_value"],
            "adjusted_backaction_coefficient":confounded.backaction_estimates[0]["adjusted_coefficient"],
            "naive_observed_minus_unobserved":confounded.backaction_estimates[0]["naive_observed_minus_unobserved"],
        },
        "claim_boundary":"development-shell adapter evidence only; estimated scalar backaction is valid only for the declared channel/history/effect contrast and is not a general causal model of target dynamics",
    }
    Path(__file__).with_name("BENCHMARK_RESULT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out["decision_flip"],indent=2,sort_keys=True))

if __name__=="__main__": main()
