.PHONY: %

DOCKER_COMPOSE_ENV_FILE=.env.dev

# Local development #

requirements:
	uv export --no-dev --format requirements-txt > backend/requirements.txt

requirements-dev:
	uv export --format requirements-txt > backend/requirements-dev.txt

format:
	uv run ruff format backend

lint:
	uv run ruff check backend

lint-fix:
	uv run ruff check backend --fix

check-types:
	uv run mypy backend/app

code-analysis-cc:
	uv run radon cc backend -a -s

code-analysis-metrics:
	uv run radon raw backend -s

# Backend #

DOCKER_COMPOSE_COMMAND_DEV=\
	docker compose \
	--env-file $(DOCKER_COMPOSE_ENV_FILE) \
	--project-name fastapi-backend \
	--file docker-compose.yaml

up:
	$(DOCKER_COMPOSE_COMMAND_DEV) up api --build $(ARGS)

down:
	$(DOCKER_COMPOSE_COMMAND_DEV) down $(ARGS)

# Alembic (database migrations) #

alembic-new:
	$(DOCKER_COMPOSE_COMMAND_DEV) exec api alembic revision --autogenerate -m "$(MSG)"

alembic-upgrade:
	$(DOCKER_COMPOSE_COMMAND_DEV) exec api alembic upgrade head

# Postgres #

postgres-up:
	$(DOCKER_COMPOSE_COMMAND_DEV) up postgres -d

postgres-down:
	$(DOCKER_COMPOSE_COMMAND_DEV) down postgres

access-postgres:
	$(DOCKER_COMPOSE_COMMAND_DEV) exec postgres psql -U postgres $(ARGS)

# Run SQL file and get CSV output
# Usage: make run-sql SQL_FILE=path/to/query.sql
run-sql:
	$(DOCKER_COMPOSE_COMMAND_DEV) cp $(SQL_FILE) postgres:/tmp/query.sql
	$(DOCKER_COMPOSE_COMMAND_DEV) exec postgres bash -c "psql -U postgres --csv -f /tmp/query.sql > /tmp/output.csv"
	$(DOCKER_COMPOSE_COMMAND_DEV) cp postgres:/tmp/output.csv ./output.csv

# Deletes postgres data by deleting the Docker volumes
# Launches a Postgres container with the dir with the backup file mounted
# Waits for Postgres to be ready, and executes pg_restore
# Stops the Postgres container; and relaunches a new container
# without the backup directory mounted in the background
DB_DUMP_PATH=

load-database-backup:
	$(DOCKER_COMPOSE_COMMAND_DEV) down --volumes
	$(DOCKER_COMPOSE_COMMAND_DEV) run --rm --name pg-backup -d -v $(DB_DUMP_PATH):/db-dump postgres

	while true; do \
		$(DOCKER_COMPOSE_COMMAND_DEV) exec postgres pg_isready -U postgres && break; \
	done

	@sleep 2

	$(DOCKER_COMPOSE_COMMAND_DEV) exec -T postgres psql -U postgres -d postgres -f /db-dump || true
	docker stop pg-backup
	$(DOCKER_COMPOSE_COMMAND_DEV) up -d postgres

# Tests #

DOCKER_COMPOSE_COMMAND_TEST=\
	docker compose \
	--env-file $(DOCKER_COMPOSE_ENV_FILE) \
	--project-name test-backend \
	--file docker-compose.yaml \
	--file docker-compose.test.yaml

test:
	$(DOCKER_COMPOSE_COMMAND_TEST) run --rm --build --remove-orphans api \
	bash -c "alembic upgrade head && \
	python3 /src/scripts/initial_data.py && \
	pytest /src/tests $(ARGS)"

test-down:
	$(DOCKER_COMPOSE_COMMAND_TEST) down -v

test-with-cleanup:
	$(MAKE) test; $(MAKE) test-down

test-access-postgres:
	$(DOCKER_COMPOSE_COMMAND_TEST) exec postgres psql -U postgres $(ARGS)

# Helper #

help:
	@echo "Available commands:"
	@echo "  make requirements         - Export production dependencies to requirements.txt"
	@echo "  make requirements-dev     - Export development dependencies to requirements-dev.txt"
	@echo "  make format               - Format code with ruff"
	@echo "  make lint                 - Check code with ruff"
	@echo "  make lint-fix             - Fix linting issues with ruff"
	@echo "  make check-types          - Check types with mypy"
	@echo "  make up                   - Start containers"
	@echo "  make down                 - Stop containers"
	@echo "  make alembic-new MSG=..   - Create new Alembic migration (autogenerate)"
	@echo "  make alembic-upgrade      - Upgrade Alembic to head"
	@echo "  make postgres-up          - Start only Postgres container"
	@echo "  make postgres-down        - Stop only Postgres container"
	@echo "  make access-postgres      - Access Postgres container with psql"
	@echo "  make run-sql              - Run SQL file and get CSV output"
	@echo "  make load-database-backup - Load database backup from SQL file"
	@echo "  make test                 - Run tests in a test container"
	@echo "  make help                 - Show this help message"
