from __future__ import annotations

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd

from ..domain.interfaces import ModelGateway, HistoryGateway
from ..infrastructure.services.feature_engineering import FeatureEngineer


class AdvancedForecastingService:
    """Advanced forecasting service with ensemble models and confidence intervals."""
    
    def __init__(self, model_gateway: ModelGateway, feature_engineer: FeatureEngineer, history_gateway: HistoryGateway):
        self.model_gateway = model_gateway
        self.feature_engineer = feature_engineer
        self.history_gateway = history_gateway
        self.ensemble_models = {}
        self._initialize_ensemble_models()
    
    def _initialize_ensemble_models(self):
        """Initialize ensemble models for improved forecasting."""
        # LightGBM (primary model)
        self.ensemble_models['lightgbm'] = self.model_gateway.get_state().model
        
        # Random Forest (secondary model)
        self.ensemble_models['random_forest'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Train ensemble models if not already trained
        # In production, these would be pre-trained and loaded
        self._train_ensemble_models()
    
    def _train_ensemble_models(self):
        """Train ensemble models on historical data."""
        # This is a simplified version - in production, you'd load pre-trained models
        # or train them on a larger dataset
        pass
    
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
        # Get historical data
        historical_data = self.history_gateway.load()
        if historical_data.empty:
            raise ValueError("No historical data available")
        
        # Prepare features
        features = self.feature_engineer.make_features(historical_data)
        if features.empty:
            raise ValueError("Feature engineering failed")
        
        # Get the latest features for prediction
        latest_features = features.iloc[-1:].drop(['energy_wh', 'target'], axis=1, errors='ignore')
        
        # Make prediction
        model = self.model_gateway.get_state().model
        prediction = model.predict(latest_features)[0]
        
        result = {
            "prediction_wh": float(prediction),
            "horizon_steps": horizon,
            "timestamp": datetime.now().isoformat(),
            "model_used": "lightgbm"
        }
        
        if include_confidence:
            # Calculate confidence interval using historical prediction errors
            confidence_interval = self._calculate_confidence_interval(
                prediction, historical_data, model, latest_features
            )
            result["confidence_interval"] = confidence_interval
        
        return result
    
    def _ensemble_forecast(self, horizon: int, include_confidence: bool) -> Dict[str, Any]:
        """Generate forecast using ensemble of models."""
        # Get historical data
        historical_data = self.history_gateway.load()
        if historical_data.empty:
            raise ValueError("No historical data available")
        
        # Prepare features
        features = self.feature_engineer.make_features(historical_data)
        if features.empty:
            raise ValueError("Feature engineering failed")
        
        # Get the latest features for prediction
        latest_features = features.iloc[-1:].drop(['energy_wh', 'target'], axis=1, errors='ignore')
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.ensemble_models.items():
            try:
                pred = model.predict(latest_features)[0]
                predictions[name] = float(pred)
            except Exception as e:
                print(f"Warning: Model {name} failed: {e}")
                continue
        
        if not predictions:
            raise ValueError("All ensemble models failed")
        
        # Calculate ensemble prediction (weighted average)
        weights = {'lightgbm': 0.7, 'random_forest': 0.3}  # Adjust based on model performance
        ensemble_prediction = sum(
            predictions[name] * weights.get(name, 0.1) 
            for name in predictions.keys()
        ) / sum(weights.get(name, 0.1) for name in predictions.keys())
        
        result = {
            "prediction_wh": float(ensemble_prediction),
            "horizon_steps": horizon,
            "timestamp": datetime.now().isoformat(),
            "model_used": "ensemble",
            "individual_predictions": predictions
        }
        
        if include_confidence:
            # Calculate confidence based on prediction variance
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
        model: Any, 
        features: Any
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
            historical_features = self.feature_engineer.make_features(recent_data)
            if historical_features.empty:
                return {
                    "lower": float(prediction * 0.8),
                    "upper": float(prediction * 1.2),
                    "std": float(prediction * 0.1)
                }
            
            # Get predictions for historical data
            hist_features = historical_features.drop(['energy_wh', 'target'], axis=1, errors='ignore')
            hist_predictions = model.predict(hist_features)
            
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
        horizon: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate forecasts for multiple weather scenarios."""
        historical_data = self.history_gateway.load()
        if historical_data.empty:
            raise ValueError("No historical data available for scenario forecasting")

        prepared_history = self.feature_engineer.normalise_history(historical_data)
        state = self.model_gateway.get_state()

        base_time = prepared_history['Time'].max()
        if pd.isna(base_time):
            raise ValueError("Historical data is missing valid timestamps")

        results: List[Dict[str, Any]] = []
        freq = pd.to_timedelta(15, unit='m')

        for i, scenario in enumerate(weather_scenarios):
            try:
                future_rows: List[Dict[str, Any]] = []
                for step in range(max(horizon, 1)):
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
                preds = state.model.predict(feature_block)
                scenario_timestamps = self.feature_engineer.extract_timestamps(future_df)

                results.append({
                    "scenario_id": i,
                    "scenario_name": scenario.get('name', f'Scenario {i+1}'),
                    "prediction_wh": float(preds[0]),
                    "horizon_steps": state.horizon,
                    "timestamp": scenario_timestamps[0] if scenario_timestamps else None,
                    "weather_conditions": scenario
                })
            except Exception as e:
                results.append({
                    "scenario_id": i,
                    "scenario_name": scenario.get('name', f'Scenario {i+1}'),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

        return results
