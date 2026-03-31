# Architecture Overview

## Service flow

1. Client calls a FastAPI trading, reporting, portfolio, reconciliation, or admin endpoint.
2. Request middleware assigns a correlation ID and logs request timing.
3. The API builds a `TradingOrchestrator`, `TradingQueryService`, `PortfolioService`, `ReconciliationService`, or `OperationalStatusService` based on the endpoint.
4. Trading writes flow through market data, strategy evaluation, portfolio-aware risk validation, execution, and persistence.
5. Read APIs expose orders, positions, strategy runs, audit logs, reconciliation history, and admin system status.
6. Reconciliation compares internal positions against broker state and persists every run for operator review.
7. Celery workers can run reconciliation asynchronously, and Celery beat schedules periodic reconciliation.
8. Startup bootstraps the schema, optionally runs migrations, and seeds demo data for template usability.
9. Structured logs and persisted records support monitoring, replay, and compliance workflows.
