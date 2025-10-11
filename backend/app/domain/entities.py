from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelState:
    """Aggregate representing the loaded forecasting model."""

    model: Any
    features: list[str]
    horizon: int
    metrics: dict[str, Any]
