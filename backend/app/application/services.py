from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..domain.entities import ModelState
from ..domain.exceptions import HistoryNotAvailableError, ModelNotReadyError
from ..domain.interfaces import HistoryGateway, ModelGateway
from ..infrastructure.services.feature_engineering import FeatureEngineer
from ..infrastructure.services.weather_service import OpenWeatherService
from ..infrastructure.services.weather_adapter import WeatherAdapter


class ForecastingService:
    """Application service orchestrating forecasting use cases."""

    def __init__(
        self,
        model_gateway: ModelGateway,
        history_gateway: HistoryGateway,
        feature_engineer: FeatureEngineer,
        weather_service: Optional[OpenWeatherService] = None,
        weather_adapter: Optional[WeatherAdapter] = None,
    ) -> None:
        self._model_gateway = model_gateway
        self._history_gateway = history_gateway
        self._feature_engineer = feature_engineer
        self._weather_service = weather_service
        self._weather_adapter = weather_adapter

    def model_ready(self, horizon: Optional[int] = None) -> bool:
        return self._model_gateway.is_ready(horizon)

    def _load_state(self, horizon: Optional[int] = None) -> ModelState:
        if not self.model_ready(horizon):
            raise ModelNotReadyError('Model artifacts not available')
        return self._model_gateway.get_state(horizon)

    def forecast_next(
        self, 
        horizon: Optional[int], 
        include_components: bool,
        use_live_weather: bool = True
    ) -> Dict[str, Any]:
        state = self._load_state(horizon)

        history_df = self._history_gateway.load(limit=self._feature_engineer.history_window)
        if history_df.empty:
            raise HistoryNotAvailableError('Historical dataset is empty')

        prepared_history = self._feature_engineer.normalise_history(history_df)

        # Decide whether to use real-time weather or history-based next step
        use_live = use_live_weather and self._weather_service and self._weather_adapter
        
        if use_live:
            try:
                # 1. Fetch live weather
                api_data = self._weather_service.get_current_weather()
                # 2. Adapt to model features (mock future)
                future_df = self._weather_adapter.to_model_input(api_data)
                prepared_future = self._feature_engineer.normalise_future(future_df)
                
                # 3. Combine with history to generate lags
                features = self._feature_engineer.features_from_future(
                    prepared_history, 
                    prepared_future, 
                    state
                )
                
                # Check if we got features (tail 1)
                if features.empty:
                    # Fallback to history if feature engineering fails for some reason
                    use_live = False
                else:
                    # For forecast_next, we expect exactly 1 row if we provide 1 future row
                    # But features_from_future handles returning the tail matching future_df
                    pass

            except Exception as e:
                # Log error and fallback
                print(f"Live weather failed: {e}. Falling back to historical simulation.")
                use_live = False

        if not use_live:
            # Original Logic: Predict next step based on history end
            features = self._feature_engineer.features_from_history(prepared_history, state)

        prediction = float(state.model.predict(features)[0])
        
        response: Dict[str, Any] = {
            'prediction_wh': prediction,
            'horizon_steps': state.horizon,
            'source': 'live_weather' if use_live else 'historical_simulation'
        }

        if include_components and hasattr(state.model, 'predict'):
            response['leaf_indices'] = state.model.predict(features, pred_leaf=True).tolist()
        return response

    def forecast_batch(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        horizon = payload.pop('horizon', None)
        state = self._load_state(horizon)

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
        metrics = dict(state.metrics)
        metrics['available_horizons'] = self._model_gateway.available_horizons()
        return metrics
