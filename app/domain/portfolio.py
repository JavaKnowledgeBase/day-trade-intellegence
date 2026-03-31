"""Domain models that describe broker account state and portfolio snapshots."""

from datetime import datetime

from pydantic import BaseModel, Field


class BrokerPositionSnapshot(BaseModel):
    """Lightweight representation of one broker-reported position used in portfolio responses."""

    symbol: str
    quantity: float
    market_price: float
    market_value: float
    average_cost: float


class PortfolioSnapshot(BaseModel):
    """Normalized account summary used by risk management and operator-facing portfolio endpoints."""

    account_id: str
    source: str
    net_liquidation: float
    available_funds: float
    buying_power: float
    drawdown_pct: float = Field(default=0.0)
    positions: list[BrokerPositionSnapshot] = Field(default_factory=list)
    as_of: datetime
