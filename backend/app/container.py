from __future__ import annotations

from pathlib import Path

from .application.services import ForecastingService, MetricsService
from .application.historical_analysis_service import HistoricalAnalysisService
from .infrastructure.repositories.artifact_model_repository import ArtifactModelRepository
from .infrastructure.repositories.csv_history_repository import CSVHistoryRepository
from .infrastructure.services.feature_engineering import FeatureEngineer


class Container:
    """Simple dependency container wiring application services."""

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        artifacts_dir = Path(__file__).resolve().parents[1] / 'artifacts'

        feature_engineer = FeatureEngineer()
        model_gateway = ArtifactModelRepository(artifacts_dir)
        history_gateway = CSVHistoryRepository(base_dir / 'Renewable.csv')

        self.model_gateway = model_gateway
        self.history_gateway = history_gateway
        self.feature_engineer = feature_engineer
        self.forecasting_service = ForecastingService(model_gateway, history_gateway, feature_engineer)
        self.metrics_service = MetricsService(model_gateway)
        self.historical_analysis_service = HistoricalAnalysisService(history_gateway)
