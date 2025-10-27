from __future__ import annotations

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import NotFittedError
import pandas as pd

from ..domain.interfaces import ModelGateway, HistoryGateway
from ..infrastructure.services.feature_engineering import FeatureEngineer


class AdvancedForecastingService:
    """Advanced forecasting service with ensemble models and confidence intervals."""
    
    def __init__(self, model_gateway: ModelGateway, feature_engineer: FeatureEngineer, history_gateway: HistoryGateway):
        self.model_gateway = model_gateway
        self.feature_engineer = feature_engineer
        self.history_gateway = history_gateway
        self._ensemble_registry: dict[int, dict[str, Any]] = {}
    
    def _current_timestamp(self) -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat()
    
    def _load_state(self, horizon: int) -> Any:
        return self.model_gateway.get_state(horizon)
    
    def _latest_feature_frame(self, state):
        historical_data = self.history_gateway.load(limit=self.feature_engineer.history_window)
        if historical_data.empty:
            raise ValueError("No historical data available")
        
        prepared_history = self.feature_engineer.normalise_history(historical_data)
        feature_frame = self.feature_engineer.features_from_history(prepared_history, state)
        return feature_frame, prepared_history

    def _train_random_forest(self, horizon: int, target_features: list[str]) -> Optional[RandomForestRegressor]:
        try:
            dataset = self.history_gateway.load()
            if dataset.empty:
                return None
            frame = self.feature_engineer.make_features(dataset, horizon=horizon)
            feature_cols = [c for c in frame.columns if c not in {'energy_wh', 'target'}]
            intersecting = [col for col in target_features if col in frame.columns]
            if not intersecting:
                return None
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_split=4,
                random_state=42,
                n_jobs=-1,
            )
            model.fit(frame[intersecting], frame['target'])
            return model
        except Exception as exc:
            print(f'Warning: failed to train random forest ensemble for horizon={horizon}: {exc}')
            return None

    def _get_ensemble_models(self, horizon: int, state) -> dict[str, Any]:
        if horizon in self._ensemble_registry:
            return self._ensemble_registry[horizon]
        models = {'lightgbm': state.model}
        rf_model = self._train_random_forest(horizon, state.features)
        if rf_model is not None:
            models['random_forest'] = rf_model
        self._ensemble_registry[horizon] = models
        return models
    
    def forecast_with_confidence(
        self, 
        horizon: int = 1, 
        include_confidence: bool = True,
        ensemble_mode: bool = False
    ) -> Dict[str, Any]:
        """Generate forecast with confidence intervals."""
        try:
            if ensemble_mode:
                return self._ensemble_forecast(horizon, include_confidence)
            else:
                return self._single_model_forecast(horizon, include_confidence)
        except Exception as e:
            raise ValueError(f"Forecasting failed: {str(e)}")
    
    def _single_model_forecast(self, horizon: int, include_confidence: bool) -> Dict[str, Any]:
        """Generate forecast using single model."""
        state = self._load_state(horizon)
        latest_features, prepared_history = self._latest_feature_frame(state)
        
        prediction = state.model.predict(latest_features)[0]
        
        result = {
            "prediction_wh": float(prediction),
            "horizon_steps": state.horizon,
            "timestamp": self._current_timestamp(),
            "model_used": "lightgbm"
        }
        
        if include_confidence:
            confidence_interval = self._calculate_confidence_interval(
                prediction, prepared_history, state
            )
            result["confidence_interval"] = confidence_interval
        
        return result
    
    def _ensemble_forecast(self, horizon: int, include_confidence: bool) -> Dict[str, Any]:
        """Generate forecast using ensemble of models."""
        state = self._load_state(horizon)
        latest_features, prepared_history = self._latest_feature_frame(state)
        models = self._get_ensemble_models(horizon, state)
        
        predictions = {}
        for name, model in models.items():
            try:
                pred = model.predict(latest_features)[0]
                predictions[name] = float(pred)
            except NotFittedError:
                continue
        
        if not predictions:
            raise ValueError("All ensemble models failed")
        
        weights = {'lightgbm': 0.7, 'random_forest': 0.3}
        total_weight = sum(weights.get(name, 0.1) for name in predictions.keys())
        ensemble_prediction = sum(
            predictions[name] * weights.get(name, 0.1)
            for name in predictions.keys()
        ) / total_weight
        
        result = {
            "prediction_wh": float(ensemble_prediction),
            "horizon_steps": state.horizon,
            "timestamp": self._current_timestamp(),
            "model_used": "ensemble",
            "individual_predictions": predictions
        }
        
        if include_confidence:
            pred_values = list(predictions.values())
            pred_std = np.std(pred_values)
            confidence_interval = {
                "lower": float(ensemble_prediction - 1.96 * pred_std),
                "upper": float(ensemble_prediction + 1.96 * pred_std),
                "std": float(pred_std)
            }
            result["confidence_interval"] = confidence_interval
        
        return result
    
    def _calculate_confidence_interval(
        self, 
        prediction: float, 
        historical_data: Any, 
        state: Any
    ) -> Dict[str, float]:
        """Calculate confidence interval for prediction."""
        try:
            # Use historical prediction errors to estimate confidence
            # This is a simplified approach - in production, you'd use more sophisticated methods
            
            # Get recent historical predictions vs actuals
            recent_data = historical_data.tail(100)  # Last 100 points
            if len(recent_data) < 10:
                # Fallback to simple percentage-based confidence
                return {
                    "lower": float(prediction * 0.8),
                    "upper": float(prediction * 1.2),
                    "std": float(prediction * 0.1)
                }
            
            # Calculate historical prediction errors
            historical_features = self.feature_engineer.make_features(recent_data, horizon=state.horizon)
            if historical_features.empty:
                return {
                    "lower": float(prediction * 0.8),
                    "upper": float(prediction * 1.2),
                    "std": float(prediction * 0.1)
                }
            
            # Get predictions for historical data
            hist_features = historical_features.drop(['energy_wh', 'target'], axis=1, errors='ignore')
            hist_predictions = state.model.predict(hist_features)
            
            # Calculate errors
            actuals = historical_features['target'].values
            errors = actuals - hist_predictions
            error_std = np.std(errors)
            
            # Calculate confidence interval
            confidence_interval = {
                "lower": float(prediction - 1.96 * error_std),
                "upper": float(prediction + 1.96 * error_std),
                "std": float(error_std)
            }
            
            return confidence_interval
        except Exception:
            # Fallback confidence interval
            return {
                "lower": float(prediction * 0.8),
                "upper": float(prediction * 1.2),
                "std": float(prediction * 0.1)
            }
    
    def forecast_multiple_scenarios(
        self,
        weather_scenarios: List[Dict[str, Any]],
        horizon: int = 1,
        include_confidence: bool = False,
        ensemble_mode: bool = False,
    ) -> List[Dict[str, Any]]:
        """Generate forecasts for multiple weather scenarios."""
        historical_data = self.history_gateway.load()
        if historical_data.empty:
            raise ValueError("No historical data available for scenario forecasting")

        prepared_history = self.feature_engineer.normalise_history(historical_data)
        state = self._load_state(horizon)

        base_time = prepared_history['Time'].max()
        if pd.isna(base_time):
            raise ValueError("Historical data is missing valid timestamps")

        results: List[Dict[str, Any]] = []
        freq = pd.to_timedelta(15, unit='m')

        base_models = None
        if ensemble_mode:
            base_models = self._get_ensemble_models(state.horizon, state)
        else:
            base_models = {'lightgbm': state.model}
        weights = {'lightgbm': 0.7, 'random_forest': 0.3}
        total_weight = sum(weights.get(name, 0.1) for name in base_models.keys())

        confidence_template = None
        if include_confidence and not ensemble_mode:
            confidence_template = self._calculate_confidence_interval(
                state.model.predict(self.feature_engineer.features_from_history(prepared_history, state))[-1],
                prepared_history,
                state,
            )

        for i, scenario in enumerate(weather_scenarios):
            try:
                future_rows: List[Dict[str, Any]] = []
                for step in range(max(state.horizon, 1)):
                    target_time = base_time + freq * (step + 1)
                    row: Dict[str, Any] = {'Time': target_time.isoformat()}
                    for key, value in scenario.items():
                        if key == 'name':
                            continue
                        row[key] = value
                    future_rows.append(row)

                future_df = pd.DataFrame(future_rows)
                future_df = self.feature_engineer.normalise_future(future_df)

                feature_block = self.feature_engineer.features_from_future(
                    prepared_history,
                    future_df,
                    state,
                )
                lightgbm_preds = state.model.predict(feature_block)
                ensemble_preds = lightgbm_preds
                per_model_predictions = {'lightgbm': lightgbm_preds}

                if ensemble_mode:
                    summed = np.zeros_like(lightgbm_preds, dtype=float)
                    for name, model in base_models.items():
                        try:
                            preds = model.predict(feature_block)
                            per_model_predictions[name] = preds
                            summed += preds * weights.get(name, 0.1)
                        except Exception as exc:
                            print(f'Warning: Ensemble model {name} failed during scenario forecasting: {exc}')
                    ensemble_preds = summed / total_weight if total_weight else lightgbm_preds
                else:
                    ensemble_preds = lightgbm_preds

                scenario_timestamps = self.feature_engineer.extract_timestamps(future_df)

                for step_idx, pred in enumerate(ensemble_preds):
                    timestamp = (
                        scenario_timestamps[step_idx]
                        if step_idx < len(scenario_timestamps)
                        else self._current_timestamp()
                    )
                    record: Dict[str, Any] = {
                        "scenario_id": i,
                        "scenario_name": scenario.get('name', f'Scenario {i+1}'),
                        "prediction_wh": float(pred),
                        "horizon_steps": state.horizon,
                        "timestamp": timestamp,
                        "weather_conditions": scenario,
                        "step_index": step_idx + 1,
                    }
                    if include_confidence:
                        if ensemble_mode:
                            candidate = [per_model_predictions[name][step_idx] for name in per_model_predictions]
                            pred_std = float(np.std(candidate))
                            record["confidence_interval"] = {
                                "lower": float(pred - 1.96 * pred_std),
                                "upper": float(pred + 1.96 * pred_std),
                                "std": pred_std,
                            }
                        elif confidence_template:
                            record["confidence_interval"] = confidence_template
                    results.append(record)
            except Exception as e:
                results.append({
                    "scenario_id": i,
                    "scenario_name": scenario.get('name', f'Scenario {i+1}'),
                    "error": str(e),
                    "timestamp": self._current_timestamp()
                })

        return results
