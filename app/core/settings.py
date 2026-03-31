"""Typed application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central runtime configuration that keeps the platform strongly typed at startup."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Day Trade Intelligence", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")
    alpaca_data_feed: str = Field(default="iex", alias="ALPACA_DATA_FEED")
    ibkr_host: str = Field(default="127.0.0.1", alias="IBKR_HOST")
    ibkr_port: int = Field(default=7497, alias="IBKR_PORT")
    ibkr_client_id: int = Field(default=1, alias="IBKR_CLIENT_ID")
    database_url: str = Field(default="sqlite:///./day_trade_intelligence.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    max_capital_at_risk_pct: float = Field(default=0.02, alias="MAX_CAPITAL_AT_RISK_PCT")
    max_drawdown_pct: float = Field(default=0.10, alias="MAX_DRAWDOWN_PCT")
    default_stop_loss_pct: float = Field(default=0.01, alias="DEFAULT_STOP_LOSS_PCT")
    paper_account_equity: float = Field(default=100000.0, alias="PAPER_ACCOUNT_EQUITY")
    paper_buying_power: float = Field(default=250000.0, alias="PAPER_BUYING_POWER")
    seed_demo_data: bool = Field(default=True, alias="SEED_DEMO_DATA")
    bootstrap_schema: bool = Field(default=True, alias="BOOTSTRAP_SCHEMA")
    run_migrations_on_start: bool = Field(default=False, alias="RUN_MIGRATIONS_ON_START")
    trader_api_key: str = Field(default="trader-local-key", alias="TRADER_API_KEY")
    operator_api_key: str = Field(default="operator-local-key", alias="OPERATOR_API_KEY")
    admin_api_key: str = Field(default="admin-local-key", alias="ADMIN_API_KEY")
    auth_secret_key: str = Field(default="change-this-local-auth-secret", alias="AUTH_SECRET_KEY")
    auth_token_exp_minutes: int = Field(default=480, alias="AUTH_TOKEN_EXP_MINUTES")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object so requests do not re-parse environment variables."""
    return Settings()
