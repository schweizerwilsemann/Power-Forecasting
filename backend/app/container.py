from __future__ import annotations

from pathlib import Path

from .application.services import ForecastingService, MetricsService
from .application.historical_analysis_service import HistoricalAnalysisService
from .infrastructure.repositories.artifact_model_repository import ArtifactModelRepository
from .infrastructure.repositories.csv_history_repository import CSVHistoryRepository
from .infrastructure.services.feature_engineering import FeatureEngineer
from .infrastructure.services.weather_service import OpenWeatherService
from .infrastructure.services.weather_adapter import WeatherAdapter

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


class Container:
    """Simple dependency container wiring application services."""

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        artifacts_dir = Path(__file__).resolve().parents[1] / 'artifacts'

        # Env vars
        api_key = os.getenv('OPEN_WEATHER_APP_API', '')

        feature_engineer = FeatureEngineer()
        model_gateway = ArtifactModelRepository(artifacts_dir)
        history_gateway = CSVHistoryRepository(base_dir / 'Renewable.csv')
        
        weather_service = OpenWeatherService(api_key=api_key)
        weather_adapter = WeatherAdapter()

        self.model_gateway = model_gateway
        self.history_gateway = history_gateway
        self.feature_engineer = feature_engineer
        
        self.forecasting_service = ForecastingService(
            model_gateway, 
            history_gateway, 
            feature_engineer,
            weather_service,
            weather_adapter
        )
        self.metrics_service = MetricsService(model_gateway)
        self.historical_analysis_service = HistoricalAnalysisService(history_gateway)
