from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Dict, List, Tuple

TIME_FORMATS: Tuple[str, ...] = (
    '%d/%m/%Y %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S',
)

NUMERIC_COLUMNS: Tuple[str, ...] = (
    'Energy delta[Wh]',
    'GHI',
    'temp',
    'humidity',
    'wind_speed',
)


def parse_time(text: str) -> datetime:
    cleaned = text.strip()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    raise ValueError(f'Cannot parse timestamp "{text}"')


def profile_dataset(csv_path: Path) -> dict:
    stats: Dict[str, List[float]] = defaultdict(list)
    missing: Dict[str, int] = defaultdict(int)
    total_rows = 0
    first_ts: datetime | None = None
    last_ts: datetime | None = None

    with csv_path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total_rows += 1
            time_value = row.get('Time')
            if time_value:
                try:
                    ts = parse_time(time_value)
                    first_ts = ts if first_ts is None else min(first_ts, ts)
                    last_ts = ts if last_ts is None else max(last_ts, ts)
                except ValueError:
                    pass

            for column in NUMERIC_COLUMNS:
                value = row.get(column)
                if value is None or value == '' or value.lower() == 'nan':
                    missing[column] += 1
                    continue
                try:
                    stats[column].append(float(value))
                except ValueError:
                    missing[column] += 1

    summary = {}
    for column, values in stats.items():
        if not values:
            continue
        summary[column] = {
            'samples': len(values),
            'min': min(values),
            'max': max(values),
            'mean': mean(values),
            'median': median(values),
            'std': pstdev(values) if len(values) > 1 else 0.0,
            'missing_rows': missing[column],
        }

    return {
        'rows': total_rows,
        'time_span': (first_ts, last_ts),
        'summary': summary,
    }


def evaluate_baselines(csv_path: Path, *, test_start: datetime) -> dict:
    persistence_mae = 0.0
    persistence_rmse = 0.0
    persistence_n = 0

    ma_window = deque(maxlen=4)
    ma_mae = 0.0
    ma_rmse = 0.0
    ma_n = 0

    prev_energy: float | None = None
    prev_time: datetime | None = None

    with csv_path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_time = row.get('Time')
            raw_energy = row.get('Energy delta[Wh]')
            if not raw_time or not raw_energy:
                prev_energy = None
                ma_window.clear()
                continue

            try:
                ts = parse_time(raw_time)
                energy = float(raw_energy)
            except ValueError:
                prev_energy = None
                ma_window.clear()
                continue

            if (
                prev_energy is not None
                and prev_time is not None
                and ts >= test_start
                and ts > prev_time
            ):
                err = energy - prev_energy
                persistence_mae += abs(err)
                persistence_rmse += err * err
                persistence_n += 1

            if len(ma_window) == ma_window.maxlen and ts >= test_start:
                avg = sum(ma_window) / len(ma_window)
                err = energy - avg
                ma_mae += abs(err)
                ma_rmse += err * err
                ma_n += 1

            ma_window.append(energy)
            prev_energy = energy
            prev_time = ts

    def finalize(mae: float, rmse: float, n: int) -> dict:
        if n == 0:
            return {'mae': math.nan, 'rmse': math.nan, 'samples': 0}
        return {
            'mae': mae / n,
            'rmse': math.sqrt(rmse / n),
            'samples': n,
        }

    return {
        'persistence': finalize(persistence_mae, persistence_rmse, persistence_n),
        'moving_average_4': finalize(ma_mae, ma_rmse, ma_n),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Profile Renewable.csv and compute baselines.')
    parser.add_argument(
        '--csv',
        type=Path,
        default=Path(__file__).resolve().parents[2] / 'Renewable.csv',
        help='Path to the source CSV dataset',
    )
    parser.add_argument(
        '--test-start',
        type=str,
        default='2022-07-01T00:00:00',
        help='ISO-like timestamp that defines the start of the evaluation window',
    )
    args = parser.parse_args()
    csv_path = args.csv.resolve()
    if not csv_path.exists():
        raise SystemExit(f'File not found: {csv_path}')

    dataset = profile_dataset(csv_path)
    try:
        test_start = parse_time(args.test_start.replace('T', ' '))
    except ValueError:
        test_start = datetime.fromisoformat(args.test_start)
    baselines = evaluate_baselines(csv_path, test_start=test_start)

    rows = dataset['rows']
    start, end = dataset['time_span']
    print('=== Dataset Overview ===')
    print(f'Path             : {csv_path}')
    print(f'Rows             : {rows:,}')
    if start and end:
        print(f'Time coverage    : {start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M}')
    print()
    print('Numeric summaries (Wh or weather units)')
    for column, summary in dataset['summary'].items():
        print(
            f'- {column:17s} | min={summary["min"]:.2f} '
            f'max={summary["max"]:.2f} mean={summary["mean"]:.2f} '
            f'median={summary["median"]:.2f} std={summary["std"]:.2f} '
            f'valid={summary["samples"]:,} missing={summary["missing_rows"]:,}'
        )
    print()
    print(f'=== Baseline metrics (start >= {test_start:%Y-%m-%d %H:%M}) ===')
    for name, vals in baselines.items():
        print(
            f'- {name:17s} | samples={vals["samples"]:,} '
            f'MAE={vals["mae"]:.2f} Wh  RMSE={vals["rmse"]:.2f} Wh'
        )


if __name__ == '__main__':
    main()
