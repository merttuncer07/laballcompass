import json

from priu import Claim, Scenario, audit_priority_reset


def main() -> None:
    audit = audit_priority_reset(
        [Claim("SECURED_OLD", 80.0), Claim("UNSECURED_OLD", 80.0)],
        [
            Scenario(0.20, 40.0, 60.0),
            Scenario(0.50, 40.0, 130.0),
            Scenario(0.30, 40.0, 220.0),
        ],
        new_money_principal=30.0,
        promised_new_money_repayment=33.0,
    )
    print(json.dumps(audit.to_dict(), indent=2))


if __name__ == "__main__":
    main()
