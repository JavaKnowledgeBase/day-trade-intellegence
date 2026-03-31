# Day Trade Intelligence

Enterprise-oriented trading platform scaffold that uses Alpaca for market data, IBKR for execution and live account state, FastAPI for control-plane APIs, Redis/Celery for background processing, PostgreSQL for durable operational state, and Alembic for schema migrations.

## Why this project exists

This repository turns the architecture described in the developer document into a production-ready backend foundation. The goal is to provide:

- clear module boundaries
- structured logging
- explicit exception handling
- typed configuration
- database-backed auditability
- live-risk-ready portfolio integration
- broker reconciliation support
- basic operator/admin protection
- JWT-style bearer authentication with local users
- a lightweight built-in operator console
- testable service orchestration

## API and UI capabilities

- `GET /console`: built-in operator console
- `POST /api/v1/auth/login`: exchange local user credentials for a bearer token
- `GET /api/v1/auth/me`: inspect the current authenticated user
- `GET /api/v1/health`: liveness endpoint
- `GET /api/v1/ready`: readiness endpoint with DB/Redis status
- `POST /api/v1/trading/signal`: evaluate a strategy and optionally execute an order
- `GET /api/v1/trading/orders`: inspect persisted order history
- `GET /api/v1/trading/positions`: inspect the internal position snapshot
- `GET /api/v1/trading/strategy-runs`: inspect persisted strategy evaluation history
- `GET /api/v1/trading/audit-logs`: inspect lifecycle audit records
- `GET /api/v1/portfolio/summary?live=false|true`: inspect synthetic paper or live IBKR account state
- `POST /api/v1/reconciliation/run?live=true|false`: run broker reconciliation synchronously
- `POST /api/v1/reconciliation/run/background?live=true|false`: enqueue reconciliation in Celery
- `GET /api/v1/reconciliation/runs`: inspect reconciliation history
- `GET /api/v1/admin/system/status`: inspect admin-only system status

## Local template startup

1. Create a virtual environment with Python 3.11+.
2. Install dependencies with `pip install -e .[dev]`.
3. The repo includes a local `.env` with safe SQLite and local Redis defaults.
4. Start the API with `powershell -ExecutionPolicy Bypass -File .\scripts\start-local.ps1`.
5. Open `http://localhost:8000/console`.
6. Log in with one of the default local users below.
7. Optionally start a worker with `celery -A app.workers.celery_app.celery_app worker --loglevel=info`.
8. Optionally start scheduler with `celery -A app.workers.celery_app.celery_app beat --loglevel=info`.
9. Run tests with `pytest`.

## User guide

- Start with [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for a step-by-step console walkthrough with annotated visuals.

## Default local users

- Trader: `trader / trader123`
- Operator: `operator / operator123`
- Admin: `admin / admin123`

## Compatibility note

- Bearer authentication is now the preferred path.
- The legacy `X-API-Key` role checks still work as a local compatibility fallback during this transition.

## Startup behavior

- If `RUN_MIGRATIONS_ON_START=true`, startup requires Alembic and applies migrations.
- If migrations are not enabled and `BOOTSTRAP_SCHEMA=true`, startup falls back to SQLAlchemy metadata creation.
- Metadata bootstrap is intended mainly for local/development usage.
- If `SEED_DEMO_DATA=true`, the app inserts demo trading data and local users when the database is empty.

