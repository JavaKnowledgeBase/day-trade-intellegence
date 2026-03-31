"""Service that reads portfolio and account state from IBKR or synthetic paper settings."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.errors import ConfigurationError, ExecutionError
from app.core.settings import Settings
from app.domain.portfolio import BrokerPositionSnapshot, PortfolioSnapshot

logger = logging.getLogger(__name__)

try:
    from ib_insync import IB
except Exception:
    IB = None


class PortfolioService:
    """Provide normalized account state to risk management and read APIs without leaking broker SDK details."""

    def __init__(self, settings: Settings) -> None:
        """Store the runtime settings needed for synthetic paper values and live IBKR access."""
        self.settings = settings

    async def get_portfolio_snapshot(self, use_live_data: bool) -> PortfolioSnapshot:
        """Return either a synthetic paper snapshot or a live broker-backed account snapshot."""
        if not use_live_data:
            return self._build_paper_snapshot()
        return self._build_live_snapshot()

    def _build_paper_snapshot(self) -> PortfolioSnapshot:
        """Construct a predictable paper-trading snapshot so development and dry-run flows remain safe."""
        logger.info("Using synthetic paper portfolio snapshot")
        return PortfolioSnapshot(
            account_id="paper-account",
            source="paper",
            net_liquidation=self.settings.paper_account_equity,
            available_funds=self.settings.paper_account_equity,
            buying_power=self.settings.paper_buying_power,
            drawdown_pct=0.0,
            positions=[],
            as_of=datetime.now(timezone.utc),
        )

    def _build_live_snapshot(self) -> PortfolioSnapshot:
        """Connect to IBKR, normalize account values, and return the current portfolio state."""
        if IB is None:
            raise ExecutionError("ib_insync components are unavailable in the current environment.")
        if not self.settings.ibkr_host or not self.settings.ibkr_port:
            raise ConfigurationError("IBKR connection settings are required for live portfolio access.")

        ib = IB()
        try:
            ib.connect(self.settings.ibkr_host, self.settings.ibkr_port, clientId=self.settings.ibkr_client_id)
            account_values = {value.tag: value.value for value in ib.accountSummary()}
            positions = [
                BrokerPositionSnapshot(
                    symbol=position.contract.symbol,
                    quantity=float(position.position),
                    market_price=float(position.marketPrice),
                    market_value=float(position.marketValue),
                    average_cost=float(position.averageCost),
                )
                for position in ib.positions()
            ]

            net_liquidation = float(account_values.get("NetLiquidation", 0.0))
            available_funds = float(account_values.get("AvailableFunds", 0.0))
            buying_power = float(account_values.get("BuyingPower", 0.0))
            highest_equity = max(net_liquidation, self.settings.paper_account_equity)
            drawdown_pct = 0.0 if highest_equity == 0 else max((highest_equity - net_liquidation) / highest_equity, 0.0)

            logger.info("Fetched live portfolio snapshot", extra={"positions_count": len(positions), "net_liquidation": net_liquidation})
            return PortfolioSnapshot(
                account_id=self.settings.ibkr_client_id.__str__(),
                source="ibkr",
                net_liquidation=net_liquidation,
                available_funds=available_funds,
                buying_power=buying_power,
                drawdown_pct=drawdown_pct,
                positions=positions,
                as_of=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.exception("Failed to fetch live portfolio snapshot")
            raise ExecutionError("Unable to retrieve live portfolio snapshot from IBKR.") from exc
        finally:
            if ib.isConnected():
                ib.disconnect()
