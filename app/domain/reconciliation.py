"""Domain models used for broker reconciliation workflows and reporting."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReconciliationStatus(str, Enum):
    """Overall outcome of a reconciliation run between persisted and broker positions."""

    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    FAILED = "FAILED"


class PositionReconciliationItem(BaseModel):
    """One symbol-level comparison between the internal position book and the live broker snapshot."""

    symbol: str
    internal_quantity: float
    broker_quantity: float
    quantity_difference: float
    internal_average_price: float
    broker_average_price: float
    price_difference: float
    matched: bool


class ReconciliationRunRecord(BaseModel):
    """Persistence model representing one completed reconciliation attempt."""

    status: ReconciliationStatus
    source: str
    checked_symbols: int
    mismatched_symbols: int
    detail: str
    metadata: dict = Field(default_factory=dict)


class ReconciliationRunRead(BaseModel):
    """API model returned when operators query persisted reconciliation history."""

    id: int
    status: str
    source: str
    checked_symbols: int
    mismatched_symbols: int
    detail: str
    metadata: dict
    created_at: datetime


class ReconciliationRunListResponse(BaseModel):
    """Paginated response returned for reconciliation history queries."""

    total: int
    limit: int
    offset: int
    items: list[ReconciliationRunRead]


class ReconciliationResponse(BaseModel):
    """Response returned when a reconciliation run is triggered manually or by a background worker."""

    status: ReconciliationStatus
    source: str
    checked_symbols: int
    mismatched_symbols: int
    items: list[PositionReconciliationItem]
    detail: str
