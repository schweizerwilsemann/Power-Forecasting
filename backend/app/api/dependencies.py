from __future__ import annotations

from functools import lru_cache

from ..application.services import ForecastingService, MetricsService
from ..application.monitoring_service import MonitoringService
from ..application.data_quality_service import DataQualityService
from ..application.advanced_forecasting_service import AdvancedForecastingService
from ..application.historical_analysis_service import HistoricalAnalysisService
from ..container import Container


@lru_cache(maxsize=1)
def get_container() -> Container:
    return Container()


def get_forecasting_service() -> ForecastingService:
    return get_container().forecasting_service


def get_metrics_service() -> MetricsService:
    return get_container().metrics_service


def get_monitoring_service() -> MonitoringService:
    container = get_container()
    return MonitoringService(container.model_gateway)


def get_data_quality_service() -> DataQualityService:
    container = get_container()
    return DataQualityService(container.history_gateway)


def get_advanced_forecasting_service() -> AdvancedForecastingService:
    container = get_container()
    return AdvancedForecastingService(container.model_gateway, container.feature_engineer, container.history_gateway)


def get_historical_analysis_service() -> HistoricalAnalysisService:
    container = get_container()
    return container.historical_analysis_service
