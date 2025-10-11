from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ...domain.exceptions import HistoryNotAvailableError
from ...domain.interfaces import HistoryGateway


class CSVHistoryRepository(HistoryGateway):
    """Provides access to the persisted Renewable.csv dataset."""

    def __init__(self, dataset_path: Path):
        self._dataset_path = dataset_path

    def load(self, limit: Optional[int] = None) -> pd.DataFrame:
        if not self._dataset_path.exists():
            raise HistoryNotAvailableError(f'Dataset not found at {self._dataset_path}')

        frame = pd.read_csv(self._dataset_path)
        if limit:
            return frame.tail(limit)
        return frame
