from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import joblib

from ...domain.entities import ModelState
from ...domain.exceptions import ModelNotReadyError
from ...domain.interfaces import ModelGateway


class ArtifactModelRepository(ModelGateway):
    """Loads and caches the trained forecasting model from disk."""

    def __init__(self, artifacts_dir: Path):
        self._artifacts_dir = artifacts_dir
        self._legacy_model_path = artifacts_dir / 'model.joblib'
        self._legacy_metrics_path = artifacts_dir / 'metrics.json'
        self._state_cache: Dict[int, ModelState] = {}
        self._artifact_index: Dict[int, Path] = {}
        self._refresh_index()

    def _refresh_index(self) -> None:
        artifact_map: Dict[int, Path] = {}
        pattern = 'model_h'
        for path in self._artifacts_dir.glob('model_h*.joblib'):
            name = path.stem
            try:
                horizon = int(name.replace('model_h', ''))
            except ValueError:
                continue
            artifact_map[horizon] = path
        if not artifact_map and self._legacy_model_path.exists():
            artifact_map[1] = self._legacy_model_path
        self._artifact_index = artifact_map

    def _default_horizon(self) -> Optional[int]:
        self._refresh_index()
        return min(self._artifact_index.keys()) if self._artifact_index else None

    def available_horizons(self) -> list[int]:
        self._refresh_index()
        return sorted(self._artifact_index.keys())

    def _metrics_path_for(self, horizon: int) -> Optional[Path]:
        specific = self._artifacts_dir / f'metrics_h{horizon}.json'
        if specific.exists():
            return specific
        if horizon == 1 and self._legacy_metrics_path.exists():
            return self._legacy_metrics_path
        return None

    def is_ready(self, horizon: Optional[int] = None) -> bool:
        self._refresh_index()
        if horizon is None:
            return bool(self._artifact_index)
        return horizon in self._artifact_index

    def get_state(self, horizon: Optional[int] = None) -> ModelState:
        self._refresh_index()
        target_horizon = horizon or self._default_horizon()
        if target_horizon is None:
            raise ModelNotReadyError('Model artifact missing. Run training before starting the API.')

        if target_horizon in self._state_cache:
            return self._state_cache[target_horizon]

        model_path = self._artifact_index.get(target_horizon)
        if not model_path or not model_path.exists():
            raise ValueError(f'Model artifact for horizon={target_horizon} not found.')

        payload = joblib.load(model_path)
        metrics = {}
        metrics_path = self._metrics_path_for(target_horizon)
        if metrics_path:
            metrics = json.loads(metrics_path.read_text())

        state = ModelState(
            model=payload['model'],
            features=payload['features'],
            horizon=payload['horizon'],
            metrics=metrics,
        )
        self._state_cache[target_horizon] = state
        return state

    def refresh(self, horizon: Optional[int] = None) -> ModelState:
        """Force a reload of the cached model state."""
        if horizon is None:
            self._state_cache.clear()
            self._refresh_index()
            return self.get_state()
        self._state_cache.pop(horizon, None)
        return self.get_state(horizon)
