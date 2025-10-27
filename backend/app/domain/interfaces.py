from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd

from .entities import ModelState


class ModelGateway(ABC):
    """Interface for accessing the persisted forecasting model."""

    @abstractmethod
    def get_state(self, horizon: Optional[int] = None) -> ModelState:
        raise NotImplementedError

    @abstractmethod
    def is_ready(self, horizon: Optional[int] = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def available_horizons(self) -> List[int]:
        raise NotImplementedError


class HistoryGateway(ABC):
    """Interface for accessing historical production data."""

    @abstractmethod
    def load(self, limit: Optional[int] = None) -> pd.DataFrame:
        raise NotImplementedError
