.PHONY: %

DOCKER_COMPOSE_ENV_FILE=.env.dev

# Local development #

requirements:
	cd backend && uv export --no-dev --format requirements-txt > requirements.txt

requirements-dev:
	cd backend && uv export --format requirements-txt > requirements-dev.txt

format:
	cd backend && uv run ruff format .

lint:
	cd backend && uv run ruff check .

lint-fix:
	cd backend && uv run ruff check . --fix

check-types:
	cd backend && uv run mypy app

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
	$(DOCKER_COMPOSE_COMMAND_TEST) run --rm --build --remove-orphans api pytest /src/tests $(ARGS); \
	$(DOCKER_COMPOSE_COMMAND_TEST) down -v

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
	@echo "  make postgres-up          - Start only Postgres container"
	@echo "  make postgres-down        - Stop only Postgres container"
	@echo "  make access-postgres      - Access Postgres container with psql"
	@echo "  make run-sql              - Run SQL file and get CSV output"
	@echo "  make load-database-backup - Load database backup from SQL file"
	@echo "  make test                 - Run tests in a test container"
	@echo "  make help                 - Show this help message"
