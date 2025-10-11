from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..domain.entities import ModelState
from ..domain.exceptions import HistoryNotAvailableError, ModelNotReadyError
from ..domain.interfaces import HistoryGateway, ModelGateway
from ..infrastructure.services.feature_engineering import FeatureEngineer


class ForecastingService:
    """Application service orchestrating forecasting use cases."""

    def __init__(
        self,
        model_gateway: ModelGateway,
        history_gateway: HistoryGateway,
        feature_engineer: FeatureEngineer,
    ) -> None:
        self._model_gateway = model_gateway
        self._history_gateway = history_gateway
        self._feature_engineer = feature_engineer

    def model_ready(self) -> bool:
        return self._model_gateway.is_ready()

    def _load_state(self) -> ModelState:
        if not self.model_ready():
            raise ModelNotReadyError('Model artifacts not available')
        return self._model_gateway.get_state()

    def forecast_next(self, horizon: Optional[int], include_components: bool) -> Dict[str, Any]:
        state = self._load_state()
        if horizon and horizon != state.horizon:
            raise ValueError(f'Model supports horizon={state.horizon}, received {horizon}.')

        history_df = self._history_gateway.load(limit=self._feature_engineer.history_window)
        if history_df.empty:
            raise HistoryNotAvailableError('Historical dataset is empty')

        prepared_history = self._feature_engineer.normalise_history(history_df)
        features = self._feature_engineer.features_from_history(prepared_history, state)

        prediction = float(state.model.predict(features)[0])
        response: Dict[str, Any] = {
            'prediction_wh': prediction,
            'horizon_steps': state.horizon,
        }

        if include_components and hasattr(state.model, 'predict'):
            response['leaf_indices'] = state.model.predict(features, pred_leaf=True).tolist()
        return response

    def forecast_batch(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        state = self._load_state()

        history_payload = payload.get('history')
        if history_payload:
            history_df = self._feature_engineer.history_from_payload(history_payload)
        else:
            history_df = self._history_gateway.load(limit=self._feature_engineer.history_window)

        if history_df.empty:
            raise HistoryNotAvailableError('Historical data required for batch forecasting')

        prepared_history = self._feature_engineer.normalise_history(history_df)

        future_payload = payload.get('future_weather')
        timestamps = payload.get('timestamps') or []

        if future_payload:
            future_df = self._feature_engineer.future_from_payload(future_payload)
            prepared_future = self._feature_engineer.normalise_future(future_df)
            feature_block = self._feature_engineer.features_from_future(
                prepared_history,
                prepared_future,
                state,
            )
            if not timestamps:
                timestamps = self._feature_engineer.extract_timestamps(prepared_future)
        else:
            feature_block = self._feature_engineer.features_from_history(prepared_history, state)

        preds = state.model.predict(feature_block)

        results: List[Dict[str, Any]] = []
        for idx, pred in enumerate(preds):
            record: Dict[str, Any] = {
                'prediction_wh': float(pred),
                'horizon_steps': state.horizon,
            }
            if idx < len(timestamps):
                record['timestamp'] = timestamps[idx]
            results.append(record)
        return results


class MetricsService:
    """Application service exposing evaluation metrics."""

    def __init__(self, model_gateway: ModelGateway) -> None:
        self._model_gateway = model_gateway

    def get_metrics(self) -> Dict[str, Any]:
        if not self._model_gateway.is_ready():
            raise ModelNotReadyError('Model artifacts not available')
        state = self._model_gateway.get_state()
        return state.metrics
