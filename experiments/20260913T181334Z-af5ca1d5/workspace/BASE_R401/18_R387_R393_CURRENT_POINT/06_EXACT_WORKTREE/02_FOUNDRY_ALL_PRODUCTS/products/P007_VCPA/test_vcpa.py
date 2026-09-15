import unittest
if __package__:
    from .vcpa import clear_verified_capital_plan
else:
    from vcpa import clear_verified_capital_plan
if __package__:
    from .parents.lcm import Claim as LClaim, FundingChannel
else:
    from parents.lcm import Claim as LClaim, FundingChannel
if __package__:
    from .parents.mcpr import Offer
else:
    from parents.mcpr import Offer
if __package__:
    from .parents.priu import Claim as PClaim, Scenario
else:
    from parents.priu import Claim as PClaim, Scenario

class VCPATests(unittest.TestCase):
    def setUp(self):
        self.channel=[FundingChannel('warehouse',100,('v',),('receivable',),.8)]
        self.offers=[Offer('cheap',10,.05),Offer('mid',30,.10),Offer('expensive',20,.20)]
        self.liabilities=[PClaim('SENIOR',80),PClaim('JUNIOR',80)]
        self.states=[Scenario(.2,40,60),Scenario(.5,40,130),Scenario(.3,40,220)]

    def test_verification_can_turn_capital_shortage_into_cleared_residual(self):
        unverified=clear_verified_capital_plan(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','none',False)],funding_channels=self.channel,capital_offers=self.offers,existing_liability_claims=self.liabilities,scenarios=self.states,scarcity_rate=.5)
        verified=clear_verified_capital_plan(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channel,capital_offers=self.offers,existing_liability_claims=self.liabilities,scenarios=self.states,scarcity_rate=.5)
        self.assertFalse(unverified.financing_complete)
        self.assertEqual(unverified.market_clear.unserved_quantity,40)
        self.assertTrue(verified.financing_complete)
        self.assertEqual(verified.residual_capital_demand,20)
        self.assertAlmostEqual(verified.clearing_required_return,.10)

    def test_market_rate_is_translated_into_priu_repayment_contract(self):
        r=clear_verified_capital_plan(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channel,capital_offers=self.offers,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertAlmostEqual(r.clearing_required_return,.10)
        arrangement=r.priority_audit.arrangements[0]
        self.assertAlmostEqual(arrangement.lender_required_recovery,22.0)
        self.assertAlmostEqual(arrangement.expected_new_money_recovery,22.0)

    def test_cleared_residual_has_protected_financing_position(self):
        r=clear_verified_capital_plan(funding_need=100,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channel,capital_offers=self.offers,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertTrue(r.protected_financing_available)
        self.assertIn(0,r.priority_audit.protected_unlocking_positions)

    def test_full_lcm_coverage_skips_market_and_priority(self):
        r=clear_verified_capital_plan(funding_need=50,liquidity_claims=[LClaim('r',100,'a','receivable','v',True)],funding_channels=self.channel,capital_offers=self.offers,existing_liability_claims=self.liabilities,scenarios=self.states)
        self.assertIsNone(r.market_clear); self.assertIsNone(r.priority_audit); self.assertTrue(r.financing_complete)

    def test_negative_rate_offer_is_rejected_by_adapter(self):
        with self.assertRaises(ValueError):
            clear_verified_capital_plan(funding_need=20,liquidity_claims=[],funding_channels=[],capital_offers=[Offer('bad',20,-.01)],existing_liability_claims=self.liabilities,scenarios=self.states)

if __name__=='__main__': unittest.main()
