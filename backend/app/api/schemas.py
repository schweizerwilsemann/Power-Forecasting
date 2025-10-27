from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

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
    scenario_name: Optional[str] = None
    leaf_indices: Optional[list] = None
    confidence_interval: Optional[Dict[str, float]] = None


class AdvancedForecastRequest(BaseModel):
    horizon: int = Field(1, description="Number of 15-minute steps ahead to forecast")
    include_confidence: bool = Field(True, description="Include confidence intervals")
    ensemble_mode: bool = Field(False, description="Use ensemble of models")
    weather_scenarios: Optional[List[Dict[str, Any]]] = None


class ScenarioForecastRequest(BaseModel):
    horizon: int = Field(1, description="Number of 15-minute steps ahead to forecast")
    weather_scenarios: List[Dict[str, Any]]


class MetricsResponse(BaseModel):
    horizon: int
    mae: float
    rmse: float
    r2_score: Optional[float] = None
    mape: Optional[float] = None


class SystemHealthResponse(BaseModel):
    status: str
    timestamp: datetime
    model_loaded: bool
    database_connected: bool
    memory_usage: Dict[str, Any]
    cpu_usage: float
    uptime: float


class DataQualityResponse(BaseModel):
    total_records: int
    missing_values: Dict[str, int]
    data_completeness: float
    anomaly_count: int
    quality_score: float
    last_updated: datetime


class HistoricalAnalysisRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    aggregation: str = Field("hour", description="Aggregation level: minute, hour, day")
    metrics: List[str] = Field(["mae", "rmse"], description="Metrics to calculate")


class HistoricalAnalysisResponse(BaseModel):
    period: Dict[str, datetime]
    metrics: Dict[str, float]
    data_points: List[Dict[str, Any]]
    trends: Dict[str, str]


class ModelManagementResponse(BaseModel):
    current_model: str
    available_models: List[str]
    model_metrics: Dict[str, Any]
    last_trained: datetime
    training_status: str


class AlertRule(BaseModel):
    id: str
    name: str
    condition: str
    threshold: float
    enabled: bool
    notification_method: str


class AlertResponse(BaseModel):
    id: str
    rule_id: str
    message: str
    severity: str
    timestamp: datetime
    resolved: bool


class DataImportRequest(BaseModel):
    data_source: str
    file_format: str = "csv"
    validation_rules: Optional[Dict[str, Any]] = None
    auto_process: bool = True


class DataImportResponse(BaseModel):
    import_id: str
    status: str
    records_processed: int
    errors: List[str]
    quality_score: float
