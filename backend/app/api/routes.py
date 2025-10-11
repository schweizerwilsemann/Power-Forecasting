from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..application.services import ForecastingService, MetricsService
from ..domain.exceptions import HistoryNotAvailableError, ModelNotReadyError
from .dependencies import get_forecasting_service, get_metrics_service
from .schemas import BatchForecastRequest, ForecastResponse, MetricsResponse, PointForecastRequest

router = APIRouter()


@router.get('/health')
def health(forecasting: ForecastingService = Depends(get_forecasting_service)) -> dict[str, bool | str]:
    return {'status': 'ok', 'model_loaded': forecasting.model_ready()}


@router.get('/metrics', response_model=MetricsResponse)
def read_metrics(metrics_service: MetricsService = Depends(get_metrics_service)) -> MetricsResponse:
    try:
        metrics = metrics_service.get_metrics()
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return MetricsResponse(**metrics)


@router.post('/forecast/next', response_model=ForecastResponse)
def forecast_next(
    payload: PointForecastRequest,
    forecasting: ForecastingService = Depends(get_forecasting_service),
) -> ForecastResponse:
    try:
        result = forecasting.forecast_next(payload.horizon, payload.include_components)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ModelNotReadyError, HistoryNotAvailableError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ForecastResponse(**result)


@router.post('/forecast/batch', response_model=list[ForecastResponse])
def forecast_batch(
    payload: BatchForecastRequest,
    forecasting: ForecastingService = Depends(get_forecasting_service),
) -> list[ForecastResponse]:
    try:
        results = forecasting.forecast_batch(payload.dict(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ModelNotReadyError, HistoryNotAvailableError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [ForecastResponse(**item) for item in results]
