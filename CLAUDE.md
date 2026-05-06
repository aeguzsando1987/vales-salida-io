# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Backend API for a material voucher management system (vales de entrada/salida). FastAPI + PostgreSQL + Celery. Handles voucher lifecycle with QR validation, PDF generation, and a 3-tier permission system.

## Development Setup

### Prerequisites
- Python 3.8+, PostgreSQL 12+, Docker (for Redis)

### First-time setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env with your DB credentials
```

Required `.env` values:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_db
SECRET_KEY=<generate with: python scripts.py genkey>
DEFAULT_ADMIN_EMAIL=admin@tuempresa.com
DEFAULT_ADMIN_PASSWORD=yourpassword
PORT=8001
```

## Running Locally (3 services required)

**Terminal 1 — Redis:**
```bash
docker run -d --name redis-vales -p 6379:6379 redis:alpine
# If container already exists: docker start redis-vales
```

**Terminal 1 — API server:**
```bash
python scripts.py start     # first time / clean start
python scripts.py restart   # if already running
# Accessible at: http://localhost:8001/docs
```

**Terminal 2 — Celery worker** (required for PDF/QR generation):
```bash
# Windows:
celery -A app.shared.tasks.celery_app worker --loglevel=info --pool=solo
# Linux/Mac:
celery -A app.shared.tasks.celery_app worker --loglevel=info
```

## Common Commands

```bash
# Run tests
pytest                                      # all tests
pytest app/tests/test_vouchers/ -v         # single module
pytest -m unit                             # by marker (unit/integration/slow)

# Database utilities
python scripts.py createdb                 # create postgres DB from DATABASE_URL
python scripts.py truncate                 # truncate all tables
python scripts.py autodiscover             # scan endpoints and sync permissions table
python scripts.py autodiscover --dry-run   # preview only
python scripts.py genkey                   # generate a new SECRET_KEY
python scripts.py help                     # list all commands
```

## Architecture

### 7-Layer Pattern (strictly enforced)

```
HTTP Request → Router → Controller → Service → Repository → Model → Database
```

- **Router** (`routers/`): FastAPI endpoint definitions, `Depends(require_permission(...))` on every route
- **Controller** (`controllers/`): Receives validated request, calls service, returns Pydantic schema response
- **Service** (`services/`): All business logic and validations live here
- **Repository** (`repositories/`): Database queries only, extends `BaseRepository[T]` from `app/shared/base_repository.py`
- **Model** (`models/`): SQLAlchemy table definitions — always include audit fields (`is_active`, `is_deleted`, `created_at`, `updated_at`)
- **Schemas** (`schemas/`): Pydantic v2 models (Base/Create/Update/Response/ListResponse pattern)

### Entity structure

Each entity lives in `app/entities/<entity_name>/` with 6 subdirectories:
```
app/entities/vouchers/
├── models/voucher_model.py
├── schemas/voucher_schemas.py
├── repositories/voucher_repository.py
├── services/voucher_service.py
├── controllers/voucher_controller.py
└── routers/voucher_router.py
```

Implemented entities: `individuals`, `countries`, `states`, `companies`, `branches`, `products`, `vouchers`, `voucher_details`.

To add a new entity, follow `ADDING_ENTITIES.md`. Register the router in `main.py` and restart — autodiscovery handles the permissions table automatically.

### Shared infrastructure (`app/shared/`)

- `base_repository.py` — generic CRUD: `create()`, `get_by_id()`, `get_all()`, `update()`, `delete()`, `exists()`, `filter_by()`
- `dependencies.py` — `get_db()` and `require_permission(entity, action, min_level)` FastAPI dependencies
- `exceptions.py` — `EntityNotFoundError`, `EntityAlreadyExistsError`, `EntityValidationError`
- `autodiscover_permissions.py` — runs on startup; infers entity/action from HTTP method + path
- `init_db.py` — seeds countries, states, and role permission templates on startup
- `tasks/voucher_tasks.py` — Celery tasks for async PDF/QR generation

### Permission system

3-tier resolution: **User override → Role template → None**

Levels: 0=None, 1=Read, 2=Update, 3=Create, 4=Delete (each level includes lower ones)

Usage in routers:
```python
current_user = Depends(require_permission("vouchers", "delete", min_level=4))
```

Roles: Admin(1), Gerente(2), Supervisor(3), Lector(4), Invitado(5), Vigilante(6)

### Configuration

Hybrid system: `config.toml` (base) → `.env` (overrides). Accessed via `app.config.settings` (singleton `Settings` object). Database connection, Celery broker URL, pool sizes, scheduler toggle all live here.

### Async tasks (PDF/QR)

Celery tasks are triggered from voucher service endpoints. Flow:
1. `POST /vouchers/{id}/generate-pdf` → returns `task_id`
2. `GET /vouchers/tasks/{task_id}/status` → poll until `"SUCCESS"`
3. `GET /vouchers/{id}/download-pdf` → download the file

### Authentication

JWT via `auth.py`. Two endpoints: `POST /token` (OAuth2 form) and `POST /login` (JSON body). Token stored by frontend in `localStorage`. All entities use `require_permission()`, never the bare `get_current_user()`.

### Soft delete

All entities use `is_deleted = False` flag. **Always filter `Model.is_deleted == False`** in repository queries. Hard delete exists only on `/users/{id}/hard` for admin use.
