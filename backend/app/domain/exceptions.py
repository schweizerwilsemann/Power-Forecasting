class DomainError(Exception):
    """Base exception for domain-level failures."""


class ModelNotReadyError(DomainError):
    """Raised when the forecasting model artifacts are missing or invalid."""


class HistoryNotAvailableError(DomainError):
    """Raised when historical data required for forecasting cannot be retrieved."""
