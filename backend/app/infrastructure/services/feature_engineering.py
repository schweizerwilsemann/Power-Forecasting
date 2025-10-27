from __future__ import annotations

import re
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd

from ...domain.entities import ModelState
from ...domain.exceptions import HistoryNotAvailableError

DEFAULT_LAGS: tuple[int, ...] = (1, 4, 8, 16, 24)
DEFAULT_ROLL_WINDOWS: tuple[int, ...] = (4, 8, 16, 32)


ISO_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


def _should_override_dayfirst(series: pd.Series) -> bool:
    if series.empty:
        return False
    for value in series:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        text = str(value)
        if ISO_PATTERN.match(text):
            return True
        break
    return False


def _parse_time_column(
    series: pd.Series,
    *,
    errors: str = 'raise',
    dayfirst: bool = True,
) -> pd.Series:
    """Parse timestamps while enforcing a consistent tz-naive UTC reference."""
    override_dayfirst = _should_override_dayfirst(series)
    effective_dayfirst = False if override_dayfirst else dayfirst
    converted = pd.to_datetime(series, errors=errors, dayfirst=effective_dayfirst, utc=True)
    if not isinstance(converted, pd.Series):
        converted = pd.Series(converted, index=series.index)
    if getattr(converted.dt, 'tz', None) is not None:
        converted = converted.dt.tz_convert('UTC').dt.tz_localize(None)
    return converted


def make_features(
    raw: pd.DataFrame,
    horizon: int = 1,
    lags: Iterable[int] = DEFAULT_LAGS,
    roll_windows: Iterable[int] = DEFAULT_ROLL_WINDOWS,
) -> pd.DataFrame:
    """Build lagged, rolling, and calendar features used by the forecaster."""
    df = raw.copy()
    if 'Time' not in df:
        raise ValueError("Input frame must contain a 'Time' column")

    df['Time'] = _parse_time_column(df['Time'])
    df = df.sort_values('Time').set_index('Time').asfreq('15min')

    # Rename to a consistent internal name and clean obvious issues.
    df = df.rename(columns={'Energy delta[Wh]': 'energy_wh'})
    if 'energy_wh' not in df:
        raise ValueError("Expected 'Energy delta[Wh]' column in source data")

    df = df[df['energy_wh'] >= 0]
    df = df.interpolate(limit_direction='both', limit=4)

    for lag in lags:
        df[f'lag_{lag}'] = df['energy_wh'].shift(lag)
    for window in roll_windows:
        df[f'roll_mean_{window}'] = df['energy_wh'].shift(1).rolling(window).mean()
        df[f'roll_std_{window}'] = df['energy_wh'].shift(1).rolling(window).std()

    weather_cols: List[str] = [
        'temp',
        'humidity',
        'wind_speed',
        'GHI',
        'clouds_all',
        'rain_1h',
        'snow_1h',
        'sunlightTime',
        'SunlightTime/daylength',
    ]
    for col in weather_cols:
        if col not in df:
            continue
        for lag in (1, 4, 8):
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)

    idx = df.index
    df['hour_sin'] = np.sin(2 * np.pi * idx.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * idx.hour / 24)
    df['dow_sin'] = np.sin(2 * np.pi * idx.dayofweek / 7)
    df['dow_cos'] = np.cos(2 * np.pi * idx.dayofweek / 7)
    df['month_sin'] = np.sin(2 * np.pi * idx.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * idx.month / 12)

    df['target'] = df['energy_wh'].shift(-horizon)
    return df.dropna()


class FeatureEngineer:
    """Coordinates feature assembly for inference use cases."""

    def __init__(self, history_window: int = 500):
        self.history_window = history_window

    def history_from_payload(self, payload: Optional[list[dict]]) -> pd.DataFrame:
        if not payload:
            raise HistoryNotAvailableError('History payload is empty')
        frame = pd.DataFrame(payload)
        if frame.empty:
            raise HistoryNotAvailableError('History payload is empty')
        return frame

    def future_from_payload(self, payload: Optional[list[dict]]) -> pd.DataFrame:
        if not payload:
            raise ValueError('future_weather payload is empty')
        frame = pd.DataFrame(payload)
        if frame.empty:
            raise ValueError('future_weather payload is empty')
        if 'Time' not in frame:
            raise ValueError("future_weather requires a 'Time' column")
        return frame

    def normalise_history(self, history_df: pd.DataFrame) -> pd.DataFrame:
        if 'Time' not in history_df:
            raise HistoryNotAvailableError("History requires a 'Time' column")
        frame = history_df.copy()
        frame['Time'] = _parse_time_column(frame['Time'], errors='coerce')
        frame = frame.dropna(subset=['Time']).sort_values('Time')
        if frame.empty:
            raise HistoryNotAvailableError('No valid timestamps found in history payload')
        return frame

    def normalise_future(self, future_df: pd.DataFrame) -> pd.DataFrame:
        if 'Time' not in future_df:
            raise ValueError("future_weather requires a 'Time' column")
        frame = future_df.copy()
        frame['Time'] = _parse_time_column(frame['Time'], errors='coerce')
        frame = frame.dropna(subset=['Time']).sort_values('Time')
        if frame.empty:
            raise ValueError('No valid timestamps found in future_weather payload')
        return frame

    def make_features(self, data: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
        """Make features from data using the global make_features function."""
        return make_features(data, horizon=horizon)
    
    def features_from_history(self, history_df: pd.DataFrame, state: ModelState) -> pd.DataFrame:
        windowed = history_df.tail(self.history_window)
        feature_frame = make_features(windowed, horizon=state.horizon)
        if feature_frame.empty:
            raise HistoryNotAvailableError('Not enough historical data to build features')
        latest = feature_frame.iloc[-1]
        return latest[state.features].to_frame().T

    def features_from_future(
        self,
        history_df: pd.DataFrame,
        future_df: pd.DataFrame,
        state: ModelState,
    ) -> pd.DataFrame:
        combined = pd.concat([history_df, future_df], ignore_index=True, sort=False)
        feature_frame = make_features(combined, horizon=state.horizon)
        if feature_frame.empty:
            raise HistoryNotAvailableError('Unable to assemble features for future horizon')
        return feature_frame.tail(len(future_df))[state.features]

    def extract_timestamps(self, df: pd.DataFrame) -> list[str]:
        if df.empty:
            return []
        timestamps: list[str] = []
        for value in df['Time']:
            if hasattr(value, 'isoformat'):
                timestamps.append(value.isoformat())
            else:
                timestamps.append(str(value))
        return timestamps
