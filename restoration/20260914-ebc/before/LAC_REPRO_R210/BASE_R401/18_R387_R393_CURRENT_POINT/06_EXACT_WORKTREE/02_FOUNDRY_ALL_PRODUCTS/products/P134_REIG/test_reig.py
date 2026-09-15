import pytest

if __package__:
    from .reig import gate_and_borrow
else:
    from reig import gate_and_borrow
if __package__:
    from .parents.rel import EvidenceRecord, ConsistencyRelation
else:
    from parents.rel import EvidenceRecord, ConsistencyRelation
if __package__:
    from .parents.ebc import HistoricalEstimate
else:
    from parents.ebc import HistoricalEstimate


def fixture(violating=True):
    c = 1.05 if violating else 0.11
    records = [
        EvidenceRecord('A','a',0.10,0.05),
        EvidenceRecord('B','b',0.12,0.05),
        EvidenceRecord('C','c',c,0.05),
    ]
    relations = [
        ConsistencyRelation('AB','A','B',0.20),
        ConsistencyRelation('AC','A','C',0.20),
        ConsistencyRelation('BC','B','C',0.20),
    ]
    hist = [
        HistoricalEstimate('A',0.10,0.15,1.0),
        HistoricalEstimate('B',0.12,0.15,1.0),
        HistoricalEstimate('C',c,0.15,1.0),
    ]
    return records, relations, hist


def test_discrepancy_localizes_and_downweights_outlier():
    r, rel, h = fixture(True)
    out = gate_and_borrow(current_estimate=1.0,current_standard_error=0.5,evidence_records=r,relations=rel,historical=h)
    rows = {x.name:x for x in out.contributions}
    assert out.integrity_gate_active
    assert rows['C'].conditional_suspect_probability > 0.95
    assert rows['C'].gated_maximum_power < 0.05
    assert rows['A'].gated_maximum_power > 0.9


def test_integrity_gate_can_reverse_downstream_threshold_decision():
    r, rel, h = fixture(True)
    out = gate_and_borrow(current_estimate=1.0,current_standard_error=0.5,evidence_records=r,relations=rel,historical=h)
    threshold = 0.60
    assert out.ungated.posterior_estimate > threshold
    assert out.gated.posterior_estimate < threshold


def test_no_declared_violation_means_no_integrity_penalty():
    r, rel, h = fixture(False)
    out = gate_and_borrow(current_estimate=0.1,current_standard_error=0.5,evidence_records=r,relations=rel,historical=h)
    assert not out.integrity_gate_active
    assert all(x.conditional_suspect_probability is None for x in out.contributions)
    assert all(x.integrity_multiplier == 1.0 for x in out.contributions)
    assert out.gated.posterior_estimate == pytest.approx(out.ungated.posterior_estimate)


def test_conditional_semantics_are_explicit():
    r, rel, h = fixture(True)
    out = gate_and_borrow(current_estimate=1.0,current_standard_error=0.5,evidence_records=r,relations=rel,historical=h)
    text = out.posterior_semantics.lower()
    assert 'conditional' in text
    assert 'not as unconditional fraud probabilities' in text


def test_source_name_mapping_must_be_exact():
    r, rel, h = fixture(True)
    bad = h[:-1] + [HistoricalEstimate('D',1.05,0.15,1.0)]
    with pytest.raises(ValueError):
        gate_and_borrow(current_estimate=1.0,current_standard_error=0.5,evidence_records=r,relations=rel,historical=bad)


def test_integrity_exponent_controls_policy_strength_without_changing_rel():
    r, rel, h = fixture(True)
    soft = gate_and_borrow(current_estimate=1.0,current_standard_error=0.5,evidence_records=r,relations=rel,historical=h,integrity_exponent=0.5)
    hard = gate_and_borrow(current_estimate=1.0,current_standard_error=0.5,evidence_records=r,relations=rel,historical=h,integrity_exponent=2.0)
    s = {x.name:x for x in soft.contributions}['C']
    q = {x.name:x for x in hard.contributions}['C']
    assert s.conditional_suspect_probability == pytest.approx(q.conditional_suspect_probability)
    assert q.gated_maximum_power < s.gated_maximum_power


def test_repeating_the_same_checks_does_not_increase_borrowing_penalty():
    records, relations, history = fixture(True)
    repeats = relations + [ConsistencyRelation('copy_'+r.name, r.right, r.left, r.tolerance) for r in relations]
    kwargs = dict(current_estimate=1.0, current_standard_error=0.5, evidence_records=records, historical=history)
    once = gate_and_borrow(relations=relations, **kwargs)
    twice = gate_and_borrow(relations=repeats, **kwargs)
    assert once.contributions == twice.contributions
    assert once.gated == twice.gated
