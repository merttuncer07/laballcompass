import unittest
if __package__:
    from .vprl import plan_priority_relief
else:
    from vprl import plan_priority_relief
if __package__:
    from .parents.lcm import Claim as LClaim, FundingChannel
else:
    from parents.lcm import Claim as LClaim, FundingChannel
if __package__:
    from .parents.priu import Claim as PClaim, Scenario
else:
    from parents.priu import Claim as PClaim, Scenario

class VPRLTests(unittest.TestCase):
    def setUp(self):
        self.channels=[FundingChannel('warehouse',100,('v',),('receivable',),.8)]
        self.liabilities=[PClaim('SENIOR',80),PClaim('JUNIOR',80)]
        self.states=[Scenario(.2,40,60),Scenario(.5,40,130),Scenario(.3,40,220)]

    def test_verified_claim_reduces_new_money_need(self):
        r=plan_priority_relief(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channels,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertAlmostEqual(r.deployable_verified_liquidity,80)
        self.assertAlmostEqual(r.residual_new_money_need,20)
        self.assertAlmostEqual(r.liquidity_coverage_fraction,.8)

    def test_verification_can_turn_unprotected_priority_reset_into_protected_one(self):
        r=plan_priority_relief(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channels,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertEqual(r.protected_positions_before,())
        self.assertIn(0,r.protected_positions_after)
        self.assertTrue(r.priority_protection_improved)

    def test_unverified_nominal_claim_does_not_create_relief(self):
        r=plan_priority_relief(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','none',False)],funding_channels=self.channels,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertEqual(r.deployable_verified_liquidity,0)
        self.assertEqual(r.residual_new_money_need,100)
        self.assertEqual(r.status,'NO_VERIFIED_LIQUIDITY_RELIEF')

    def test_full_coverage_skips_priority_reset(self):
        r=plan_priority_relief(funding_need=50,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channels,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertEqual(r.residual_new_money_need,0)
        self.assertIsNone(r.residual_priority_audit)
        self.assertTrue(r.priority_protection_improved)

    def test_invalid_need_rejected(self):
        with self.assertRaises(ValueError):
            plan_priority_relief(funding_need=-1,liquidity_claims=[],funding_channels=[],existing_liability_claims=self.liabilities,scenarios=self.states)

if __name__=='__main__': unittest.main()
