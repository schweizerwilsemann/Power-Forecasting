from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from .entities import ModelState


class ModelGateway(ABC):
    """Interface for accessing the persisted forecasting model."""

    @abstractmethod
    def get_state(self) -> ModelState:
        raise NotImplementedError

    @abstractmethod
    def is_ready(self) -> bool:
        raise NotImplementedError


class HistoryGateway(ABC):
    """Interface for accessing historical production data."""

    @abstractmethod
    def load(self, limit: Optional[int] = None) -> pd.DataFrame:
        raise NotImplementedError
