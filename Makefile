
COMPOSE = docker compose -f infra/docker-compose.yml
SERVICES = delivery_service warehouse_service shipment_service saga_coordinator blockchain_service auth_service

.PHONY: up down restart logs ps build migrate-% install-% install-all lint-% test-% test-all coverage-% generate-user

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f $(service)

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build --no-cache

# ---------------------------------------------------------------------------
# Per-service shortcuts:  make migrate-delivery_service
# ---------------------------------------------------------------------------

migrate-%:
	cd services/$* && poetry run yoyo apply --database "$(shell grep DATABASE_URL services/$*/.env | cut -d= -f2-)" ./migrations

install-%:
	cd services/$* && poetry install

install-all:
	@for svc in $(SERVICES); do \
		echo "→ Installing $$svc..."; \
		cd services/$$svc && poetry install && cd ../..; \
	done

lint-%:
	cd services/$* && poetry run ruff check src/

lint-all:
	@for svc in $(SERVICES); do \
		echo "→ Linting $$svc..."; \
		cd services/$$svc && poetry run ruff check src/ && cd ../..; \
	done

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test-%:
	cd services/$* && poetry run pytest tests/ -v

test-all:
	@for svc in $(SERVICES); do \
		echo "→ Testing $$svc..."; \
		cd services/$$svc && poetry run pytest tests/ -q && cd ../..; \
	done

coverage-%:
	cd services/$* && poetry run pytest tests/ --cov=src --cov-report=term-missing

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

## Generate bcrypt hash for a password:
##   make generate-user PASSWORD=mysecret
generate-user:
	@python3 -c "import bcrypt; h = bcrypt.hashpw('$(PASSWORD)'.encode(), bcrypt.gensalt(12)); print('Hash:', h.decode())"
