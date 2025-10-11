from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import joblib

from ...domain.entities import ModelState
from ...domain.exceptions import ModelNotReadyError
from ...domain.interfaces import ModelGateway


class ArtifactModelRepository(ModelGateway):
    """Loads and caches the trained forecasting model from disk."""

    def __init__(self, artifacts_dir: Path):
        self._artifacts_dir = artifacts_dir
        self._model_path = artifacts_dir / 'model.joblib'
        self._metrics_path = artifacts_dir / 'metrics.json'
        self._state: Optional[ModelState] = None

    def is_ready(self) -> bool:
        return self._model_path.exists()

    def get_state(self) -> ModelState:
        if self._state is not None:
            return self._state

        if not self._model_path.exists():
            raise ModelNotReadyError('Model artifact missing. Run training before starting the API.')

        payload = joblib.load(self._model_path)
        metrics = {}
        if self._metrics_path.exists():
            metrics = json.loads(self._metrics_path.read_text())

        self._state = ModelState(
            model=payload['model'],
            features=payload['features'],
            horizon=payload['horizon'],
            metrics=metrics,
        )
        return self._state

    def refresh(self) -> ModelState:
        """Force a reload of the cached model state."""
        self._state = None
        return self.get_state()
