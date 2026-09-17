"""Real repeated-source evaluation; not a medical or banking efficacy study.

Usage: python run.py --acsa-dir /absolute/path/to/ACSA
Only a hash-verified, unchanged public ZIP is accepted. No simulated data fallback.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import sys
import time
import zipfile

import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ZIP_SHA = '2f82bb0ef96fa7d8d7edf4d97b89173e07c2cca7723440a64bc38918a83345df'
CSV_SHA = 'f2c7d5025dec4e92e7feae367a5f7ccf58789a10ac6b54bdf15976c599f9dd39'
SEED = 20260915
B = 2000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acsa-dir', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.acsa_dir.resolve()))
    from acsa import audit_adaptive_selection
    archive = (HERE / 'data/parkinsons-telemonitoring.zip').read_bytes()
    if hashlib.sha256(archive).hexdigest() != ZIP_SHA:
        raise ValueError('Original UCI archive hash mismatch')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        raw = z.read('parkinsons_updrs.data')
    if hashlib.sha256(raw).hexdigest() != CSV_SHA:
        raise ValueError('Original UCI data hash mismatch')
    records = list(csv.reader(io.StringIO(raw.decode('ascii'))))
    columns = records[0]
    data = np.asarray(records[1:], dtype=float)
    assert data.shape == (5875, 22) and np.isfinite(data).all()
    subjects = data[:, 0].astype(int)
    ids = np.random.default_rng(SEED).permutation(np.unique(subjects))
    split_ids = dict(fit=ids[:20], selection=ids[20:31], holdout=ids[31:])
    masks = {key: np.isin(subjects, value) for key, value in split_ids.items()}
    assert not (set(split_ids['fit']) & set(split_ids['selection']) or
                set(split_ids['fit']) & set(split_ids['holdout']) or
                set(split_ids['selection']) & set(split_ids['holdout']))
    x = data[:, 6:]  # 16 original voice measurements only.
    y = data[:, columns.index('motor_UPDRS')]
    models = {
        'constant_fit_mean': DummyRegressor(strategy='mean'),
        'ridge_1': make_pipeline(StandardScaler(), Ridge(alpha=1.)),
        'ridge_100': make_pipeline(StandardScaler(), Ridge(alpha=100.)),
        'knn_5': make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=5)),
        'knn_25': make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=25)),
        'hist_gradient_boosting': HistGradientBoostingRegressor(
            max_iter=100, learning_rate=.1, max_leaf_nodes=15,
            early_stopping=False, random_state=SEED),
    }
    predictions = {'selection': [], 'holdout': []}
    for name, model in models.items():
        model.fit(x[masks['fit']], y[masks['fit']])
        for partition in predictions:
            predictions[partition].append(model.predict(x[masks[partition]]))
    losses = {key: np.abs(np.column_stack(value) - y[masks[key], None])
              for key, value in predictions.items()}
    common = dict(candidate_names=tuple(models), bootstrap_samples=B, random_seed=SEED)
    start = time.perf_counter()
    row = audit_adaptive_selection(losses['selection'], losses['holdout'], **common)
    row_seconds = time.perf_counter() - start
    start = time.perf_counter()
    grouped = audit_adaptive_selection(losses['selection'], losses['holdout'], **common,
        selection_groups=subjects[masks['selection']].tolist(),
        holdout_groups=subjects[masks['holdout']].tolist())
    grouped_seconds = time.perf_counter() - start
    assert row.selected_candidate == grouped.selected_candidate
    assert row.selection_mean_losses == grouped.selection_mean_losses
    assert row.holdout_mean_losses == grouped.holdout_mean_losses

    # Independent intercept-only sandwich calculation via the design matrix.
    selected = list(models).index(grouped.selected_candidate)
    v = losses['holdout'][:, selected]
    holdout_ids = subjects[masks['holdout']]
    design = (np.unique(holdout_ids)[:, None] == holdout_ids[None, :]).astype(float)
    cluster_scores = design @ (v - v.mean())
    g = design.shape[0]
    baseline_se = float(np.sqrt((cluster_scores @ cluster_scores) * g / (g - 1)) / len(v))
    np.testing.assert_allclose(grouped.pointwise_standard_error, baseline_se, rtol=1e-12)

    for partition, errors in losses.items():
        # These are fitted-model losses derived from the unchanged public records.
        out = np.column_stack((np.flatnonzero(masks[partition]) + 2,
                               subjects[masks[partition]], errors))
        np.savetxt(HERE / f'{partition}-losses.csv', out, delimiter=',',
            header='original_csv_line,subject_id,' + ','.join(models), comments='',
            fmt=['%d', '%d'] + ['%.17g'] * len(models))

    result = {
        'source': {
            'title': 'Tsanas & Little (2009), Parkinsons Telemonitoring, UCI',
            'page': 'https://archive.ics.uci.edu/dataset/189/parkinsons+telemonitoring',
            'download': 'https://archive.ics.uci.edu/static/public/189/parkinsons+telemonitoring.zip',
            'doi': '10.24432/C5ZS3N', 'license': 'CC BY 4.0',
            'zip_sha256': ZIP_SHA, 'data_sha256': CSV_SHA,
            'rows': len(data), 'subjects': len(ids), 'features': columns[6:],
            'target': 'motor_UPDRS (linearly interpolated by the dataset authors)',
        },
        'protocol': {
            'seed': SEED, 'bootstrap_samples_per_method': B,
            'loss': 'absolute prediction error', 'estimand': 'pooled recording mean',
            'split_ids': {key: value.tolist() for key, value in split_ids.items()},
            'split_rows': {key: int(mask.sum()) for key, mask in masks.items()},
            'models': {key: repr(model) for key, model in models.items()},
            'adaptation': 'One predeclared seed and family; no tuning on holdout; train-only scaling.',
        },
        'row_baseline': row.to_dict(), 'grouped': grouped.to_dict(),
        'comparison': {
            'same_selected_candidate': True, 'same_point_estimates': True,
            'cluster_to_row_standard_error_ratio': grouped.pointwise_standard_error / row.pointwise_standard_error,
            'independent_sandwich_baseline_se': baseline_se,
            'row_seconds': row_seconds, 'grouped_seconds': grouped_seconds,
        },
        'environment': {name: importlib.metadata.version(name) for name in
                        ('numpy', 'scipy', 'scikit-learn', 'joblib', 'threadpoolctl')},
        'acsa_sha256': hashlib.sha256((args.acsa_dir / 'acsa.py').read_bytes()).hexdigest(),
        'limitations': [
            'This is a repeated-source software evaluation, not clinical validation or a banking case.',
            'Only 11 protected subjects; neither normal nor percentile intervals have proven coverage here.',
            'Grouping assumes subjects are independent; IDs alone cannot prove this.',
            'Fixed fitted models and observed losses; no retraining uncertainty or candidate-generation audit.',
            'No accuracy advantage over ordinary model selection is claimed; point estimates are identical.',
            'Cluster CR1 and pairs bootstrap are established methods, not a new lab invention.',
        ],
    }
    (HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('protocol', 'comparison')}, indent=2))
    print('Selected:', grouped.selected_candidate)
    print('Row interval:', row.selected_holdout_loss_bootstrap_interval_95)
    print('Grouped interval:', grouped.selected_holdout_loss_bootstrap_interval_95)


if __name__ == '__main__':
    main()
