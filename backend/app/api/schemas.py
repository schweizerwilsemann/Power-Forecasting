from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PointForecastRequest(BaseModel):
    horizon: Optional[int] = Field(1, description="Number of 15-minute steps ahead to forecast")
    include_components: bool = Field(False, description="Return model leaf indices for debugging")


class HistoryPoint(BaseModel):
    Time: str
    energy: Optional[float] = Field(None, alias="Energy delta[Wh]")

    class Config:
        allow_population_by_field_name = True


class BatchForecastRequest(BaseModel):
    history: Optional[List[dict]] = None
    future_weather: Optional[List[dict]] = None
    timestamps: Optional[List[str]] = None


class ForecastResponse(BaseModel):
    prediction_wh: float
    horizon_steps: int
    timestamp: Optional[str] = None
    leaf_indices: Optional[list] = None


class MetricsResponse(BaseModel):
    horizon: int
    mae: float
    rmse: float
