from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ..domain.interfaces import HistoryGateway

AGGREGATION_RULES: Dict[str, str] = {
    'minute': '15T',
    'hour': 'H',
    'day': 'D',
    'week': 'W',
}


def _normalise_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _format_timestamp(value: pd.Timestamp) -> str:
    return value.to_pydatetime().replace(tzinfo=None, microsecond=0).isoformat()


class HistoricalAnalysisService:
    """Provides statistical summaries over historical production records."""

    def __init__(self, history_gateway: HistoryGateway) -> None:
        self._history_gateway = history_gateway

    def analyse(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregation: str,
        metrics: List[str] | None = None,
    ) -> Dict[str, Any]:
        if start_date > end_date:
            raise ValueError('start_date must be earlier than end_date')

        data = self._history_gateway.load()
        if data.empty:
            raise ValueError('No historical records available')

        frame = data.copy()
        series = pd.to_datetime(frame['Time'], errors='coerce', utc=True)
        frame['Time'] = series.dt.tz_localize(None)
        frame = frame.dropna(subset=['Time']).sort_values('Time')
        if frame.empty:
            raise ValueError('No valid timestamps found in historical data')

        start = _normalise_datetime(start_date)
        end = _normalise_datetime(end_date)

        mask = (frame['Time'] >= start) & (frame['Time'] <= end)
        filtered = frame.loc[mask]
        if filtered.empty:
            raise ValueError('No data points within the requested window')

        filtered = filtered.set_index('Time')
        values = filtered['Energy delta[Wh]'].astype(float)
        if len(values) < 2:
            raise ValueError('Not enough data points to analyse the selected window')

        summary_metrics = self._compute_metrics(values, metrics or [])

        freq = AGGREGATION_RULES.get(aggregation, AGGREGATION_RULES['day'])
        grouped = filtered.resample(freq)
        data_points = self._build_series(grouped)
        trends = self._describe_trends(data_points)

        return {
            'period': {
                'start': start,
                'end': end,
            },
            'metrics': summary_metrics,
            'data_points': data_points,
            'trends': trends,
        }

    @staticmethod
    def _compute_metrics(values: pd.Series, metrics: List[str]) -> Dict[str, float]:
        shifted = values.shift(1).dropna()
        actuals = values.iloc[1:]
        errors = actuals - shifted

        mae = float(np.abs(errors).mean())
        rmse = float(np.sqrt((errors ** 2).mean()))

        denominator = np.abs(actuals.replace(0, np.nan))
        mape = float((np.abs(errors) / denominator).dropna().mean() * 100) if not denominator.dropna().empty else float('nan')
        ss_res = float((errors ** 2).sum())
        ss_tot = float(((actuals - actuals.mean()) ** 2).sum())
        r2_score = 1.0 if ss_tot == 0 else 1 - (ss_res / ss_tot)

        available_metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2_score': r2_score,
        }

        if not metrics:
            return {key: value for key, value in available_metrics.items() if not np.isnan(value)}
        return {
            key: value for key, value in available_metrics.items() if key in metrics and not np.isnan(value)
        }

    @staticmethod
    def _build_series(grouped: pd.core.groupby.DataFrameGroupBy) -> List[Dict[str, Any]]:
        series: List[Dict[str, Any]] = []
        for timestamp, group in grouped:
            frame = group.sort_index()
            if frame.empty:
                continue
            energy = frame['Energy delta[Wh]'].astype(float)
            record: Dict[str, Any] = {
                'timestamp': _format_timestamp(timestamp),
                'energy_mean': float(energy.mean()),
                'energy_sum': float(energy.sum()),
                'energy_max': float(energy.max()),
                'energy_min': float(energy.min()),
            }
            if len(energy) > 1:
                shifted = energy.shift(1).dropna()
                actuals = energy.iloc[1:]
                errors = actuals - shifted
                record['mae'] = float(np.abs(errors).mean())
                record['rmse'] = float(np.sqrt((errors ** 2).mean()))
            series.append(record)
        return series

    @staticmethod
    def _describe_trends(data_points: List[Dict[str, Any]]) -> Dict[str, str]:
        if not data_points:
            return {}

        def describe(key: str, lower_is_better: bool = False) -> str:
            first = next((point.get(key) for point in data_points if key in point), None)
            last = next((point.get(key) for point in reversed(data_points) if key in point), None)
            if first is None or last is None:
                return 'stable'

            if first == 0:
                if last == 0:
                    return 'stable'
                return 'declining' if lower_is_better else 'increasing'

            change = (last - first) / first if first != 0 else float('inf')
            threshold = 0.05
            if lower_is_better:
                if change <= -threshold:
                    return 'improving'
                if change >= threshold:
                    return 'declining'
            else:
                if change >= threshold:
                    return 'increasing'
                if change <= -threshold:
                    return 'decreasing'
            return 'stable'

        trends: Dict[str, str] = {}
        trends['accuracy'] = describe('mae', lower_is_better=True)
        trends['performance'] = describe('energy_sum')
        return trends
