# Supply Chain Tracker

<p align="right">
  <a href="README.md">🇷🇺 Русский</a> | <a href="README.en.md">🇬🇧 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.123-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Apache_Kafka-7.6-231F20?style=for-the-badge&logo=apachekafka&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Prometheus-Grafana-E6522C?style=for-the-badge&logo=prometheus&logoColor=white"/>
</p>

> A distributed microservices platform for tracking supply chains — from shipment creation to final delivery and blockchain recording.

---

## Table of Contents

- [About](#about)
- [Architecture](#architecture)
- [Services](#services)
- [Key Technical Decisions](#key-technical-decisions)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API](#api)
- [Authentication & RBAC](#authentication--rbac)
- [Saga Pattern](#saga-pattern)
- [Event-Driven Messaging](#event-driven-messaging)
- [Observability](#observability)
- [Configuration](#configuration)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)

---

## About

**Supply Chain Tracker** is a backend platform modelling a real-world supply chain in a distributed systems context. The project demonstrates advanced enterprise architecture patterns:

- **Saga Pattern (Orchestration)** — guaranteed compensation on any step failure without two-phase commit (2PC)
- **Hexagonal Architecture (Ports & Adapters)** — complete isolation of business logic from infrastructure
- **Event-Driven Architecture** — loose coupling between services via Apache Kafka
- **Stateless JWT RBAC** — authorization without DB lookups on downstream services

---

## Architecture

### Infrastructure (Docker Compose)

All services, Kafka, PostgreSQL (dedicated DB per service), Redis, Prometheus and Grafana are started via a single `docker-compose.yml`.

![Infrastructure](docs/infrastructure.drawio.svg)

### Kafka Topics Topology

Three event topics (publishing business events) and three command topics (saga_coordinator publishes compensating commands).

![Kafka Topics](docs/kafka-topics.drawio.svg)

### Happy Path — Event Sequence

Full flow from shipment creation to the final blockchain record.

![Happy Path](docs/happy-path-sequence.drawio.svg)

---

## Services

| Service | Port | Responsibility | Publishes |
|---------|------|----------------|-----------|
| **auth_service** | 8005 | User registration, JWT issuance, refresh token rotation | — |
| **delivery_service** | 8000 | Courier and delivery management | `CourierAssigned`, `DeliveryInTransit`, `DeliveryCompleted` |
| **warehouse_service** | 8001 | Warehouse inventory, reservation | `InventoryReserved`, `InventoryReleased`, `InventoryUpdated` |
| **shipment_service** | 8002 | Shipment creation and tracking | `ShipmentCreated`, `ShipmentUpdated`, `ShipmentCancelled` |
| **saga_coordinator** | 8003 | Distributed transaction orchestration, compensation | `ReleaseInventoryCommand`, `CancelShipmentCommand`, `UnassignCourierCommand` (commands) |
| **blockchain_service** | 8004 | Immutable event recording on-chain | — (consumer only) |

---

## Key Technical Decisions

### Hexagonal Architecture (Ports & Adapters)

Each service enforces strict layer separation. Business logic (`domain/`) has no knowledge of FastAPI or PostgreSQL.

```
Dependencies flow one way:

API handlers → App Services → Domain Ports ← Infra Repositories
                                          ↑
                               asyncpg Pool (via FastAPI Depends)
```

- `domain/entities/` — pure Python classes with no framework imports
- `domain/ports/` — abstract ABC repository interfaces
- `infra/db/` — concrete implementations via asyncpg + raw SQL
- `api/handlers/` — HTTP adapters, delegate everything to services

### Stateless JWT Authorization

Downstream services (delivery, warehouse, shipment) **never call** `auth_service` per request. They validate the token signature locally and extract `role` from claims. This:
- Eliminates a single point of failure
- Reduces per-request latency
- Scales horizontally without changes

```python
# libs/auth/provider.py
auth_provider = JWTAuthProvider(secret_key=..., stateless=True)
get_current_user = auth_provider()  # FastAPI dependency
```

### Asyncpg Without ORM

All queries are written in raw SQL via `asyncpg`. Benefits:
- Full control over the query planner
- No N+1 and other ORM pitfalls
- Transparency — every query can be explained and optimised
- UPSERT pattern (`ON CONFLICT DO UPDATE`) for idempotency

### Lifespan Resource Management

All services manage resource lifecycle via `@asynccontextmanager lifespan`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_provider.startup()           # asyncpg connection pool
    await event_queue_provider.startup()  # Kafka / In-Memory adapter
    worker_task = asyncio.create_task(command_worker.run())
    yield                                 # application accepts requests
    worker_task.cancel()                  # graceful worker shutdown
    await event_queue_provider.shutdown()
    await db_provider.shutdown()
```

This guarantees clean connection teardown and no coroutine leaks.

---

## Tech Stack

| Category | Technology | Rationale |
|----------|-----------|-----------|
| **Language** | Python 3.13 | Latest stable, `asyncio.timeout()`, improved GIL |
| **Web Framework** | FastAPI 0.123 | Native async, auto OpenAPI generation, dependency injection |
| **Database** | PostgreSQL 16 | ACID, JSONB for payloads, window functions |
| **DB Driver** | asyncpg (raw SQL) | Maximum performance, full query control |
| **Migrations** | yoyo-migrations | Versioned SQL migrations, rollback, numbering |
| **Message Broker** | Apache Kafka + aiokafka | At-least-once delivery, log-based storage, partitioning |
| **Authentication** | python-jose + bcrypt | HS256 JWT, PBKDF2 password hashing |
| **Blockchain** | Web3.py | EVM-compatible networks, mock mode for development |
| **Cache** | Redis 7 | Nonce manager for blockchain transactions |
| **Metrics** | Prometheus + Grafana | request rate, error rate, latency percentiles |
| **Logging** | Structured JSON | correlation_id across all services |
| **Infrastructure** | Docker Compose | Reproducible environment, health checks |
| **CI/CD** | GitHub Actions | Tests, linting, docker build per service |
| **Linting** | ruff | 100x faster than flake8, includes isort |

---

## Project Structure

```
supply_chain_tracker/
│
├── infra/                          # Infrastructure configs
│   ├── docker-compose.yml          # PostgreSQL, Kafka, Redis, Prometheus, Grafana
│   ├── prometheus/prometheus.yml   # Scrape config
│   └── grafana/
│       ├── dashboards/             # JSON dashboards (auto-provisioned)
│       └── provisioning/           # Datasource + dashboard discovery
│
├── libs/                           # Shared library for all services
│   └── libs/
│       ├── auth/                   # JWT provider, RBAC, TokenPayload
│       ├── cache/                  # Redis + In-Memory adapters
│       ├── deps/                   # PostgresPoolProvider, EventQueueProvider
│       ├── errors/                 # handlers.py — exception handler factory
│       ├── health/                 # create_health_router(), PostgresHealthCheck
│       ├── messaging/              # Event/Command dataclasses, Kafka/Memory adapters
│       ├── middlewares/            # HttpLoggingMiddleware
│       └── observability/          # JSON logger, PrometheusMiddleware
│
└── services/
    ├── auth_service/               # Registration, JWT, refresh tokens
    ├── delivery_service/           # Couriers and deliveries
    ├── warehouse_service/          # Warehouses and inventory
    ├── shipment_service/           # Shipments
    ├── saga_coordinator/           # Distributed saga orchestration
    └── blockchain_service/         # On-chain event recording
```

### Per-Service Structure

```
services/<service>/
├── Dockerfile
├── pyproject.toml
├── migrations/
│   └── 001_create_table.py        # yoyo migration
└── src/
    ├── config.py                   # Pydantic Settings
    ├── main.py                     # FastAPI app + lifespan
    ├── domain/
    │   ├── entities/               # Pure domain models
    │   ├── ports/                  # ABC repository interfaces
    │   ├── errors/                 # Domain exceptions
    │   └── value_objects/          # Immutable value types
    ├── app/
    │   ├── services/               # Application services
    │   └── workers/                # Kafka command consumers
    ├── infra/
    │   └── db/                     # asyncpg repository implementations
    └── api/
        ├── handlers/               # FastAPI routers
        ├── dto/                    # Pydantic request/response models
        ├── mappers/                # Entity ↔ DTO conversion
        └── deps/                   # FastAPI dependency providers
```

---

## Quick Start

### Prerequisites

- Docker 24+
- Docker Compose v2
- Make

### Running

```bash
# 1. Clone the repository
git clone <repo-url>
cd supply_chain_tracker

# 2. Create .env files for each service (copy from example)
cp infra/env.example services/auth_service/.env
cp infra/env.example services/delivery_service/.env
cp infra/env.example services/warehouse_service/.env
cp infra/env.example services/shipment_service/.env
cp infra/env.example services/saga_coordinator/.env

# 3. Start all infrastructure
make up

# 4. Check container status
make ps
```

### Applying Migrations

```bash
make migrate-delivery_service
make migrate-warehouse_service
make migrate-shipment_service
make migrate-auth_service
make migrate-saga_coordinator
make migrate-blockchain_service
```

### Stopping

```bash
make down
```

### Useful Commands

```bash
make logs                          # all logs
make logs service=delivery_service # single service logs
make build                         # rebuild images
make ps                            # container status
```

---

## API

Swagger UI is available in `development` mode:

| Service | Swagger UI |
|---------|-----------|
| auth_service | http://localhost:8005/docs |
| delivery_service | http://localhost:8000/docs |
| warehouse_service | http://localhost:8001/docs |
| shipment_service | http://localhost:8002/docs |
| saga_coordinator | http://localhost:8003/docs |

### Registration & Token

```bash
# Register
curl -X POST http://localhost:8005/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "secret123"}'
# → 201 {"user_id": "...", "username": "alice", "role": "operator"}

# Get tokens
curl -X POST http://localhost:8005/api/v1/auth/token \
  -d "username=alice&password=secret123"
# → {"access_token": "eyJ...", "refresh_token": "...", "token_type": "bearer"}

# Refresh token
curl -X POST http://localhost:8005/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### Core Operations

```bash
TOKEN="Bearer eyJ..."

# Create a courier
curl -X POST http://localhost:8000/api/v1/couriers \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Ivan", "last_name": "Petrov", "phone": "+79001234567"}'

# List couriers (with pagination)
curl "http://localhost:8000/api/v1/couriers?limit=20&offset=0" \
  -H "Authorization: $TOKEN"

# Create a shipment
curl -X POST http://localhost:8002/api/v1/shipments \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Moscow",
    "destination": "Saint Petersburg",
    "departure_date": "2026-04-01"
  }'

# Create a warehouse
curl -X POST http://localhost:8001/api/v1/warehouses \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Warehouse A", "address": "Moscow, Industrialnaya 5"}'

# Delete (admin only)
curl -X DELETE http://localhost:8000/api/v1/couriers/<id> \
  -H "Authorization: $ADMIN_TOKEN"
# operator → 403, admin → 204
```

### Health Checks

```bash
# Liveness probe
curl http://localhost:8000/api/v1/health
# → {"service": "delivery_service", "status": "HEALTHY"}

# Readiness probe (checks DB, Kafka)
curl http://localhost:8000/api/v1/ready
# → {"service": "delivery_service", "status": "HEALTHY", "components": {...}}
```

---

## Authentication & RBAC

### Token Schema

```
JWT payload:
{
  "sub": "alice",
  "role": "operator",   ← claim used for RBAC
  "exp": 1234567890
}
```

### Permission Matrix

| Role | GET | POST / PATCH | DELETE |
|------|-----|-------------|--------|
| `viewer` | ✓ | ✗ 403 | ✗ 403 |
| `operator` | ✓ | ✓ | ✗ 403 |
| `admin` | ✓ | ✓ | ✓ |

### How Stateless Auth Works

```
Client → delivery_service → JWTAuthProvider.decode_token()
                            ↓
                   HMAC-SHA256 signature verification
                            ↓
                   Extract role from claims
                            ↓
                   require_role("admin") → 403 or pass
```

**No call to `auth_service`** per request. The JWT secret is shared via the `JWT_SECRET_KEY` environment variable.

---

## Saga Pattern

### Why Saga Instead of 2PC?

Two-phase commit locks resources across all participants during the prepare phase, which is unacceptable in a microservices architecture. Saga implements compensatable transactions — each step has a corresponding rollback operation.

### Saga Lifecycle

![Saga Lifecycle](docs/saga-lifecycle.drawio.svg)

| Status | Description |
|--------|-------------|
| `STARTED` | Saga created, steps executing |
| `COMPLETED` | All steps completed successfully |
| `COMPENSATING` | Failure detected, rolling back |
| `FAILED` | Compensation complete, saga failed |

### Compensation Table

| Failure | Compensating Commands |
|---------|-----------------------|
| `delivery.failed` | `UnassignCourierCommand` + `ReleaseInventoryCommand` + `CancelShipmentCommand` |
| `courier.unassigned` | `ReleaseInventoryCommand` + `CancelShipmentCommand` |
| `inventory.insufficient` | `CancelShipmentCommand` |

### correlation_id

Every event and command carries a `correlation_id` (saga_id), enabling:
- Linking all events of a single saga
- Idempotent processing
- Traces in distributed tracing

```python
event = Event(
    event_type="shipment.created",
    aggregate_id=shipment_id,
    correlation_id=saga_id,   # ← cross-cutting identifier
    payload={...}
)
```

---

## Event-Driven Messaging

Full topic topology — in the [Kafka Topics](docs/kafka-topics.drawio.svg) diagram.

### Switching Kafka ↔ In-Memory

All services support local development without Kafka:

```bash
# .env
USE_KAFKA=false   # In-Memory (for tests and local dev)
USE_KAFKA=true    # Apache Kafka (production / docker-compose)
```

Implemented via `EventQueueProvider` in `libs/deps/queue.py` — a single configuration point.

---

## Observability

### Prometheus + Grafana

```bash
# Prometheus
open http://localhost:9090

# Grafana (admin / admin)
open http://localhost:3000
```

The **"Supply Chain Tracker"** dashboard is available immediately after startup (auto-provisioned). Includes:
- **HTTP Request Rate** — req/s per service
- **Error Rate 5xx** — error percentage
- **Latency P99 / P50** — latency percentiles in ms
- **Stat panels** — active services, total requests, error %

### Metrics

Each service exports metrics at `/metrics` (Prometheus format):

```
http_requests_total{service, method, path, status}
http_request_duration_seconds{service, method, path}
```

### Structured Logs

All logs are JSON with mandatory fields:

```json
{
  "timestamp": "2026-03-10T12:00:00Z",
  "level": "INFO",
  "service": "delivery_service",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Processing command",
  "command_type": "courier.unassign"
}
```

`correlation_id` is propagated across all services, enabling full request path tracing.

---

## Configuration

All settings are via environment variables (Pydantic Settings):

| Variable | Services | Default | Description |
|----------|---------|---------|-------------|
| `DATABASE_URL` | all | — | PostgreSQL DSN |
| `JWT_SECRET_KEY` | all | `dev-secret` | Shared HS256 secret |
| `JWT_ALGORITHM` | all | `HS256` | Signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | all | `60` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | auth_service | `30` | Refresh token TTL |
| `USE_KAFKA` | delivery/warehouse/shipment/saga | `false` | Kafka vs In-Memory |
| `KAFKA_BOOTSTRAP_SERVERS` | all | `localhost:9092` | Kafka brokers |
| `KAFKA_GROUP_ID` | all | per-service | Consumer group |
| `DB_POOL_MIN_SIZE` | all | `5` | Min connections |
| `DB_POOL_MAX_SIZE` | all | `20` | Max connections |
| `USE_MOCK_BLOCKCHAIN` | blockchain_service | `false` | Mock Web3 gateway |
| `REDIS_URL` | blockchain_service | `redis://localhost` | Nonce manager |
| `ENVIRONMENT` | all | `development` | local/development/production |

Example `.env` — see `infra/env.example`.

---

## Testing

### Running Tests

```bash
# Tests for one service
make test-delivery_service

# Tests for all services
make test-all

# With coverage
make coverage-delivery_service
```

### Test Structure

```
tests/
└── unit/
    ├── api/
    │   ├── test_courier_router.py    # HTTP handler tests
    │   ├── test_delivery_router.py
    │   └── test_auth.py              # Auth middleware tests
    └── infra/
        └── repositories/
            ├── test_courier_repository.py
            └── test_delivery_repository.py
```

### Testing Pattern

Each test creates an isolated FastAPI instance — **without importing `src.main`**. This ensures test independence from lifespan and allows dependency overrides:

```python
def test_create_courier():
    app = FastAPI()
    app.include_router(courier_router)
    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: UserInDB(username="alice", role="operator")

    client = TestClient(app)
    response = client.post("/couriers", json={...})
    assert response.status_code == 201
```

Repositories are tested with a mock asyncpg pool — no real DB connection required.

---

## CI/CD

### GitHub Actions Pipeline

`.github/workflows/ci.yml` contains three jobs:

```
push/PR → main
    │
    ├── test (matrix: all services)
    │   ├── poetry install
    │   ├── pytest --cov
    │   └── upload coverage → Codecov
    │
    ├── lint
    │   └── ruff check (all services)
    │
    └── build (matrix: all services)
        └── docker build
```

### Pre-commit Hooks

```bash
# Install
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

Hooks: `ruff` (lint + format), `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `debug-statements`.

### Makefile

```bash
make up                        # start all services
make down                      # stop
make build                     # rebuild Docker images
make logs service=delivery_service  # logs for a specific service
make ps                        # container status

make test-delivery_service     # service tests
make test-all                  # all service tests
make coverage-warehouse_service # coverage report

make lint-shipment_service     # ruff check
make lint-all                  # lint all services

make migrate-delivery_service  # apply migrations
make install-all               # poetry install for all services
```

---

## Design Decisions & Trade-offs

### Why Not 2PC / XA Transactions?

Two-phase commit requires locking resources across all participants during the prepare phase. In a microservices architecture this creates tight coupling and reduces availability. Saga Pattern + compensating transactions provide eventual consistency without distributed locks.

### Why Stateless JWT Instead of Sessions?

Stateful sessions require shared storage (Redis) and an additional round-trip per request. Stateless JWT lets each service validate authorization independently — horizontal scaling without changes.

### Why Raw SQL Instead of SQLAlchemy?

asyncpg is used directly. SQLAlchemy adds an abstraction layer that hides generated queries and complicates optimisation. Raw SQL is predictable, transparent, and equally maintainable with the repository pattern.

### Why In-Memory Adapter for Kafka?

Swappable queue adapters (`EventQueuePort`) allow running the entire service without Kafka in tests and local development — just set `USE_KAFKA=false`. No business code changes required.
