from __future__ import annotations

from functools import lru_cache

from ..application.services import ForecastingService, MetricsService
from ..container import Container


@lru_cache(maxsize=1)
def get_container() -> Container:
    return Container()


def get_forecasting_service() -> ForecastingService:
    return get_container().forecasting_service


def get_metrics_service() -> MetricsService:
    return get_container().metrics_service
