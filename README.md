# FastAPI Microservices Template

Template for building scalable microservices with FastAPI and modern
Python (3.14).

## Features

- ⚡ Backend development with `FastAPI`
- 📦 Blazing-fast dependency management with `uv`
- 🧹 Linting + formatting with `ruff`
- 🧠 Static type checking with `mypy`
- 🧪 Testing + coverage with `pytest` and `asyncio`
- 🐳 Dockerized environment for reproducible dev & CI
- 🗃 `PostgreSQL` + `SQLAlchemy 2.0`
- 🔁 `Alembic` migrations
- 🔐 Service-to-service authentication ready
- 🧰 `Makefile` for common tasks
- 🔒 Optional `pre-commit` hooks

## Project Structure

```text
.
├── backend/
│   ├── app/           # Main application code
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Configuration, security, utils
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic layer
│   ├── docker/        # Docker files
│   ├── migrations/    # Alembic migrations
│   ├── scripts/       # Startup and initialization scripts
│   └── tests/         # Pytest suite
├── docker-compose.yaml
├── docker-compose.test.yaml
├── Makefile
└── pyproject.toml
```

## Goals

It is a simple yet opinionated starter project that aims to provide:

- **Speed of Development**: Pre-configured stack allows developers to focus on
business logic from day one.

- **Consistency**: Standardized project structure, formatting, linting rules
and type checking.

- **Modern Tooling**: High-performance Python tools across the board.

- **Testability**: Isolated database and containerized tests for reliable CI.

### Intentionally not included

Some features are project-specific and therefore left out:

- Redis / caching
- Celery / background jobs
- Identity providers (Auth0, Keycloak, etc.)
- Deployment pipelines

### Authentication

Designed primarily for service-to-service (M2M) communication using
[Oauth Client Credentials flow](https://oauth.net/2/grant-types/client-credentials/).

Not intended as-is for public-facing authentication without customization.

## Local Development

### Prerequisites

Install:
- [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

### Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/brunosilvagrego/fastapi-template-microservices.git
   cd fastapi-template-microservices
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Environment Configuration**:
   The template uses `.env.dev` for development by default. You can modify it
   if needed.

4. **Run the application**:
   The application automatically runs migrations on startup.

   ```bash
   make up
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000).
   You can access the interactive documentation at
   [http://localhost:8000/docs](http://localhost:8000/docs).

### Common Tasks

The project uses a `Makefile` to simplify common development tasks:

| Command | Description |
|---------|-------------|
| `make up` | Start the API and Database |
| `make down` | Stop all containers |
| `make down ARGS=-v` | Stop all containers and delete database |
| `make format` | Run ruff format |
| `make lint-fix` | Run ruff check and fix issues |
| `make check-types` | Run mypy type checking |
| `make code-cleanup` | Run format, lint-fix and check-types at once |
| `make requirements-all` | Export production and development requirements to corresponding files |
| `make precommit-install` | Install pre-commit hooks for automatic code cleanup |
| `make alembic-new MSG="..."` | Create a new database migration |
| `make alembic-upgrade` | Apply database migrations |
| `make test` | Run tests with coverage inside a container |
| `make test-with-cleanup` | Run tests and cleanup docker resources |
| `make help` | Show all available commands |

### Handling Dependencies

Add new packages with boundaries:

```bash
uv add --bounds major fastapi
uv add --dev --bounds major pytest ruff
```

Update requirements files:

```bash
make requirements-all
```

## References

This template was inspired by the following repos:

- [fastapi/full-stack-fastapi-template](https://github.com/Kludex/fastapi-microservices)
- [Kludex/fastapi-microservices](https://github.com/Kludex/fastapi-microservices)
- [adr1enbe4udou1n/fastapi-realworld-example-app](https://github.com/adr1enbe4udou1n/fastapi-realworld-example-app)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
