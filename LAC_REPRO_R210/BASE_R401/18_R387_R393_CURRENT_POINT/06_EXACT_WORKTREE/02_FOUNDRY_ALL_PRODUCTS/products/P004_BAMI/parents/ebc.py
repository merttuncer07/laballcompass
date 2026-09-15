"""Adaptive borrowing of normal estimates, with declared observation identity.

An observation_id identifies repetitions of ONE underlying estimate, not an
entire organization/study or merely equal numbers. Partly overlapping estimates
need a covariance model; the independent-observation model here cannot infer it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class HistoricalEstimate:
    name: str
    estimate: float
    standard_error: float
    maximum_power: float = 1.0
    observation_id: str | None = None


@dataclass(frozen=True)
class BorrowingContribution:
    name: str
    estimate: float
    standard_error: float
    conflict_z: float
    commensurability_factor: float
    pre_cap_power: float
    final_power: float
    borrowed_precision: float
    observation_id: str | None = None
    counted_as: str | None = None


@dataclass(frozen=True)
class BorrowingResult:
    current_estimate: float
    current_standard_error: float
    posterior_estimate: float
    posterior_standard_error: float
    confidence_low: float
    confidence_high: float
    current_precision: float
    borrowed_precision: float
    borrowing_precision_ratio: float
    cap_scale: float
    current_information_share: float
    contributions: tuple[BorrowingContribution, ...]
    distinct_historical_observations: int = 0
    duplicate_history_count: int = 0
    current_overlap_count: int = 0
    dependency_model: str = "Distinct observation IDs (or unlabelled records) and current estimate are assumed independent; identity is caller-declared"
    interval_semantics: str = "Adaptive-weight plug-in normal interval; nominal confidence coverage and full Bayesian posterior calibration are not established"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["contributions"] = [asdict(item) for item in self.contributions]
        return payload


def coalesce_history(historical):
    """Validate and collapse declared aliases; retain the largest allowed power.

    With identical observations their compatibility is identical, so the largest
    power dominates the smaller policy allowances. Equal estimates with different
    identities are left separate. Return representatives and alias -> name map.
    """
    records = tuple(historical)
    if len({record.name for record in records}) != len(records):
        raise ValueError("historical estimate names must be unique")
    groups = {}
    for record in records:
        if (not isinstance(record.name, str) or not record.name
            or not np.isfinite(record.estimate) or not np.isfinite(record.standard_error)
            or not np.isfinite(record.maximum_power) or record.standard_error <= 0
            or not 0 <= record.maximum_power <= 1):
            raise ValueError("historical estimates require finite values, positive SE, and power in [0,1]")
        if record.observation_id is not None and (not isinstance(record.observation_id, str) or not record.observation_id.strip()):
            raise ValueError("observation_id must be a nonempty string or None")
        key = ('observation', record.observation_id) if record.observation_id is not None else ('record', record.name)
        groups.setdefault(key, []).append(record)
    chosen, mapping = [], {}
    for group in groups.values():
        first = group[0]
        if any((x.estimate, x.standard_error) != (first.estimate, first.standard_error) for x in group):
            raise ValueError("One observation_id has conflicting estimate/SE; partial overlap requires a covariance model")
        representative = min(group, key=lambda x: (-x.maximum_power, x.name))
        chosen.append(representative)
        mapping.update({x.name: representative.name for x in group})
    return tuple(chosen), mapping


def borrow_evidence(
    current_estimate: float,
    current_standard_error: float,
    historical: Sequence[HistoricalEstimate],
    *,
    compatibility_scale: float = 1.5,
    borrowing_cap_ratio: float = 2.0,
    confidence_z: float = 1.96,
    current_observation_id: str | None = None,
) -> BorrowingResult:
    """Combine current and historical normal estimates with conflict-adaptive power weights."""

    numbers = [current_estimate, current_standard_error, compatibility_scale, borrowing_cap_ratio, confidence_z]
    if not all(np.isfinite(numbers)) or current_standard_error <= 0 or compatibility_scale <= 0:
        raise ValueError("current SE and compatibility scale must be positive; all inputs finite")
    if borrowing_cap_ratio < 0 or confidence_z <= 0:
        raise ValueError("borrowing cap must be non-negative and confidence_z positive")
    records = tuple(historical)
    unique, aliases = coalesce_history(records)
    if current_observation_id is not None and (not isinstance(current_observation_id, str) or not current_observation_id.strip()):
        raise ValueError("current_observation_id must be a nonempty string or None")
    overlap = {r.name for r in records if current_observation_id is not None and r.observation_id == current_observation_id}
    for record in records:
        if record.name in overlap and (record.estimate, record.standard_error) != (current_estimate, current_standard_error):
            raise ValueError("Current and historical observation identity conflicts with estimate/SE")
    counted = {r.name for r in unique if r.name not in overlap}

    current_precision = 1.0 / current_standard_error**2
    provisional: list[tuple[HistoricalEstimate, float, float, float]] = []
    pre_cap_precision = 0.0
    for record in records:
        conflict_z = abs(record.estimate - current_estimate) / np.sqrt(
            record.standard_error**2 + current_standard_error**2
        )
        compatibility = float(np.exp(-0.5 * (conflict_z / compatibility_scale) ** 2))
        pre_cap_power = record.maximum_power * compatibility if record.name in counted else 0.0
        precision = pre_cap_power / record.standard_error**2
        provisional.append((record, conflict_z, compatibility, pre_cap_power))
        pre_cap_precision += precision

    allowed_precision = borrowing_cap_ratio * current_precision
    cap_scale = 1.0 if pre_cap_precision == 0 else min(1.0, allowed_precision / pre_cap_precision)
    contributions: list[BorrowingContribution] = []
    weighted_numerator = current_precision * current_estimate
    borrowed_precision = 0.0
    for record, conflict_z, compatibility, pre_cap_power in provisional:
        final_power = pre_cap_power * cap_scale
        precision = final_power / record.standard_error**2
        borrowed_precision += precision
        weighted_numerator += precision * record.estimate
        contributions.append(
            BorrowingContribution(
                record.name, record.estimate, record.standard_error, float(conflict_z), compatibility,
                float(pre_cap_power), float(final_power), float(precision),
                record.observation_id, 'current' if record.name in overlap else aliases[record.name],
            )
        )

    total_precision = current_precision + borrowed_precision
    posterior = weighted_numerator / total_precision
    posterior_se = float(1.0 / np.sqrt(total_precision))
    return BorrowingResult(
        current_estimate=float(current_estimate),
        current_standard_error=float(current_standard_error),
        posterior_estimate=float(posterior),
        posterior_standard_error=posterior_se,
        confidence_low=float(posterior - confidence_z * posterior_se),
        confidence_high=float(posterior + confidence_z * posterior_se),
        current_precision=float(current_precision),
        borrowed_precision=float(borrowed_precision),
        borrowing_precision_ratio=float(borrowed_precision / current_precision),
        cap_scale=float(cap_scale),
        current_information_share=float(current_precision / total_precision),
        contributions=tuple(contributions),
        distinct_historical_observations=len(counted),
        duplicate_history_count=len(records)-len(unique),
        current_overlap_count=len(overlap),
    )


def review_identity(config):
    """Compare the declared identities with the explicit independence baseline."""
    arguments = dict(config)
    history = [HistoricalEstimate(**r) for r in arguments.pop('historical')]
    grouped = borrow_evidence(historical=history, **arguments)
    independent_args = {k:v for k,v in arguments.items() if k != 'current_observation_id'}
    independent = borrow_evidence(historical=[replace(h,observation_id=None) for h in history], **independent_args)
    return {'identity_preserved':grouped.to_dict(),
            'independence_assumed':independent.to_dict(),
            'estimate_shift_from_counting_aliases':independent.posterior_estimate-grouped.posterior_estimate,
            'se_change_from_counting_aliases':independent.posterior_standard_error-grouped.posterior_standard_error,
            'interpretation':'The difference isolates declared repeated observations. Neither run establishes source authenticity, general independence, audit opinion or calibrated confidence.'}


if __package__:
    from .correlated import CorrelatedBorrowingResult, borrow_correlated_evidence, source_covariance
else:
    from correlated import CorrelatedBorrowingResult, borrow_correlated_evidence, source_covariance


def review_covariance(config):
    """Same inputs/policies; remove only cross-observation covariance for baseline."""
    arguments=dict(config)
    history=[HistoricalEstimate(**r) for r in arguments.pop('historical')]
    joint=borrow_correlated_evidence(historical=history,**arguments)
    matrix=np.asarray(arguments['covariance'],dtype=float)
    independent_args={**arguments,'covariance':np.diag(np.diag(matrix)), 'current_observation_id':None}
    independent=borrow_correlated_evidence(historical=[replace(h,observation_id=None) for h in history],**independent_args)
    return {'joint_covariance':joint.to_dict(),'diagonal_assumption':independent.to_dict(),
            'estimate_shift_if_covariance_ignored':independent.posterior_estimate-joint.posterior_estimate,
            'se_change_if_covariance_ignored':independent.posterior_standard_error-joint.posterior_standard_error,
            'interpretation':'Common scalar estimand and caller-supplied joint covariance. Differences isolate the diagonal-covariance assumption; they are not an audit opinion or calibrated fraud probability.'}


def main(argv=None):
    import argparse, hashlib, json
    from pathlib import Path
    parser=argparse.ArgumentParser(description='EBC: combine normal estimates while preserving declared observation identity')
    parser.add_argument('input_json');parser.add_argument('--output');parser.add_argument('--review',action='store_true')
    args=parser.parse_args(argv)
    try:
        raw=Path(args.input_json).read_bytes();config=json.loads(raw)
        if args.review:
            result=review_covariance(config) if 'covariance' in config else review_identity(config)
        else:
            config=dict(config)
            history=[HistoricalEstimate(**r) for r in config.pop('historical')]
            function=borrow_correlated_evidence if 'covariance' in config else borrow_evidence
            result=function(historical=history,**config).to_dict()
        result['mechanism']={'engine':'R026 EBC','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             'input_sha256':hashlib.sha256(raw).hexdigest()}
        result['mechanism']['correlated_source_sha256']=hashlib.sha256(Path(__file__).with_name('correlated.py').read_bytes()).hexdigest()
        text=json.dumps(result,indent=2,allow_nan=False)+'\n'
        if args.output:
            with Path(args.output).open('x') as f:f.write(text)
            print(args.output)
        else:print(text,end='')
        return 0
    except (ValueError,TypeError,KeyError,OSError) as error:
        parser.error(str(error))


if __name__=='__main__':
    raise SystemExit(main())
