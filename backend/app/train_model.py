from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .infrastructure.services.feature_engineering import make_features

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / 'Renewable.csv'
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / 'artifacts'


@dataclass
class DatasetSplits:
    train_idx: pd.Index
    val_idx: pd.Index
    test_idx: pd.Index


def split_frame(frame: pd.DataFrame) -> DatasetSplits:
    train_idx = frame.index < '2022-01-01'
    val_idx = (frame.index >= '2022-01-01') & (frame.index < '2022-07-01')
    test_idx = frame.index >= '2022-07-01'
    return DatasetSplits(train_idx, val_idx, test_idx)


def _model_filename(horizon: int) -> Path:
    return ARTIFACTS_DIR / f'model_h{horizon}.joblib'


def _metrics_filename(horizon: int) -> Path:
    return ARTIFACTS_DIR / f'metrics_h{horizon}.json'


def train_model(data_path: Path = DATA_PATH, horizon: int = 1) -> dict:
    if not data_path.exists():
        raise FileNotFoundError(f'Dataset not found at {data_path}')

    raw = pd.read_csv(data_path)
    frame = make_features(raw, horizon=horizon)
    splits = split_frame(frame)
    feature_cols = [c for c in frame.columns if c not in {'energy_wh', 'target'}]

    model = LGBMRegressor(
        n_estimators=2000,
        learning_rate=0.05,
        num_leaves=64,
        max_depth=-1,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_lambda=0.1,
        reg_alpha=0.05,
    )

    model.fit(
        frame.loc[splits.train_idx, feature_cols],
        frame.loc[splits.train_idx, 'target'],
        eval_set=[(
            frame.loc[splits.val_idx, feature_cols],
            frame.loc[splits.val_idx, 'target'],
        )],
        eval_metric='l2',
    )

    preds = model.predict(frame.loc[splits.test_idx, feature_cols])
    y_true = frame.loc[splits.test_idx, 'target']
    mae = float(mean_absolute_error(y_true, preds))
    mse = mean_squared_error(y_true, preds)
    rmse = float(np.sqrt(mse))

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    payload = {
        'model': model,
        'features': feature_cols,
        'horizon': horizon,
        'trained_on': {
            'train_end': '2021-12-31',
            'val_end': '2022-06-30',
        },
    }
    joblib.dump(payload, _model_filename(horizon))
    if horizon == 1:
        joblib.dump(payload, ARTIFACTS_DIR / 'model.joblib')

    metrics = {'horizon': horizon, 'mae': mae, 'rmse': rmse}
    _metrics_filename(horizon).write_text(json.dumps(metrics, indent=2))
    if horizon == 1:
        (ARTIFACTS_DIR / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train LightGBM forecaster')
    parser.add_argument('--data', type=Path, default=DATA_PATH, help='Path to Renewable.csv')
    parser.add_argument(
        '--horizon',
        type=int,
        default=1,
        help='Forecast horizon in 15-minute steps (deprecated when --horizons is provided)',
    )
    parser.add_argument(
        '--horizons',
        type=int,
        nargs='+',
        help='Train multiple horizons in one go (e.g. --horizons 1 4 8 24 48)',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    horizons = args.horizons or [args.horizon]
    results = {}
    for horizon in horizons:
        metrics = train_model(args.data, horizon)
        results[horizon] = metrics
    if len(results) == 1:
        print(json.dumps(next(iter(results.values())), indent=2))
    else:
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
