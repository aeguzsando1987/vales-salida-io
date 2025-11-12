# FastAPI Dynamic API Template

> Enterprise-ready FastAPI template with 7-layer architecture and granular permissions system.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Key Features

- **7-Layer Architecture** - Router → Controller → Service → Repository → Model → Database
- **JWT Authentication** - OAuth2 integration with Swagger UI
- **Generic BaseRepository** - TypeVar[T] for reusable CRUD operations
- **Granular Permissions System** - Entity-level access control with 5 hierarchical levels
- **Geographic Data** - Pre-loaded countries (3) and states (114) with ISO codes
- **4 Production-Ready Entities**:
  - **Individuals** - Complete example with 40+ fields, JSONB skills system
  - **Countries** - ISO 3166 countries
  - **States** - States/provinces by country
  - **Companies** - NEW: Full CRUD with 20 endpoints, TIN validation, advanced search
- **Soft Delete & Audit** - Track created_by, updated_by, deleted_by on all entities
- **Hybrid Configuration** - config.toml (public) + .env (secrets)

---

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### Installation

```bash
# Clone and setup
git clone <repository-url> my-api-project
cd my-api-project
python -m venv venv

# Activate virtual environment
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure database
createdb my_project_db
```

### Configuration

Create `.env` file:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/my_project_db
SECRET_KEY=your-super-secret-key-here
DEFAULT_ADMIN_EMAIL=admin@yourcompany.com
DEFAULT_ADMIN_PASSWORD=change-in-production
PORT=8001
```

Generate secure secret key:
```bash
python generate_secret_key.py
```

### Run Server

```bash
python main.py
```

**Access:**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

**Default Admin:**
- Email: `admin@tuempresa.com`
- Password: `root`
---

## Documentation

### Developer Guides

- **[PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)** - Complete development pattern with examples
- **[ADDING_ENTITIES.md](ADDING_ENTITIES.md)** - Step-by-step guide to add entities

### Add New Entity (30-45 minutes)

1. Read [PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)
2. Create `app/entities/<entity_name>/` with 6 files:
   - `models/<entity>_model.py`
   - `schemas/<entity>_schemas.py`
   - `repositories/<entity>_repository.py`
   - `services/<entity>_service.py`
   - `controllers/<entity>_controller.py`
   - `routers/<entity>_router.py`
3. Register router in `main.py`
4. Test in Swagger UI

---

## Architecture

### Project Structure

```
app/
├── entities/
│   ├── individuals/    # 40+ fields, JSONB skills
│   ├── countries/      # ISO 3166 data
│   ├── states/         # Geographic data
│   ├── companies/      # NEW: 20 endpoints
│   └── users/          # System users
├── shared/
│   ├── base_repository.py
│   ├── exceptions.py
│   ├── dependencies.py
│   ├── models/         # Permission system
│   └── data/           # Seed data
└── tests/
```

### 7-Layer Pattern

**Flow:** Request → Router → Controller → Service → Repository → Model → Database

Each layer has a specific responsibility:
- **Router:** FastAPI endpoints and dependencies
- **Controller:** Request/response orchestration
- **Service:** Business logic and validations
- **Repository:** Database queries (extends BaseRepository)
- **Model:** SQLAlchemy table definitions
- **Schemas:** Pydantic validation models
- **Database:** PostgreSQL via SQLAlchemy ORM

---

## Permissions System

### Permission Levels

| Level | Description | Access |
|-------|-------------|--------|
| 0 | None | No access |
| 1 | Read | GET endpoints |
| 2 | Update | Read + PUT/PATCH |
| 3 | Create | Read + Update + POST |
| 4 | Delete | All operations |

### Role Matrix

| Role | Level | Companies Access |
|------|-------|-----------------|
| Admin | 1 | Full (Level 4) |
| Manager | 2 | Cannot delete (Level 3) |
| Collaborator | 3 | Cannot delete (Level 3) |
| Reader | 4 | Read-only (Level 1) |
| Guest | 5 | No access |

### Usage

```python
from app.shared.dependencies import require_permission

@router.delete("/companies/{id}")
def delete_company(
    id: int,
    current_user: User = Depends(require_permission("companies", "delete", min_level=4))
):
    return company_service.delete(id)
```

---

## Available Endpoints

### Authentication
- `POST /token` - Get JWT token

### Users
- `POST /users` - Create user
- `GET /users` - List users
- `GET /users/me` - Current user profile

### Individuals (25+ endpoints)
- CRUD operations
- Skills management (JSONB)
- Advanced search and statistics

### Companies (20 endpoints)
- **CRUD:** POST, GET, PUT, DELETE
- **Search:** By TIN, country, state, advanced filters
- **Operations:** Activate, suspend, deactivate
- **Analytics:** Statistics and aggregations
- **Details:** With geographic relationships

### Countries & States
- `GET /countries/` - 3 pre-loaded
- `GET /states/by-country/{id}` - 114 pre-loaded

NOTE: The countries and states are pre-loaded in the database. You can find the data in the `app/shared/data/` folder. Curently working on a method and UI to load the countries and states from a CSV file.
---

## Utilities

This project includes a consolidated CLI for common maintenance tasks. This is the list of available commands and how to use them:

```bash
# Generate a secret key for production deployment
python scripts.py genkey

# Create a postgres database using the DATABASE_URL from .env
python scripts.py createdb

# Iniciar servidor en puerto libre Start the server using the PORT from .env
python scripts.py start

# Restart the server (useful when you change the port or kill all the processes)
python scripts.py restart

# Truncates the whole database
python scripts.py truncate

# Truncates the whole database (alternative method)
python scripts.py truncate-hard

# Scan endpoints and sync permissions (Phase 2 - Autodiscovery)
python scripts.py autodiscover           # Production mode (applies changes)
python scripts.py autodiscover --dry-run # Preview mode (no changes)

# Show help
python scripts.py help
```
---

## Deployment

### Production Checklist

- Generate secure `SECRET_KEY`
- Configure production `DATABASE_URL`
- Change `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` by your own preferences
- Set `DEBUG=false` in config.toml
- Configure CORS for your domain
- Use ASGI server (gunicorn + uvicorn)

### Run with Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### Docker Deployment

This project can be dockerized. Create these files in the root of the project:

**`Dockerfile`:**
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["python", "main.py"]
```

**`docker-compose.yml`:**
```yaml
services:
  api:
    build: .
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql://postgres:root@db:5432/db_test_template
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - db
  db:
    image: postgres:12
    environment:
      POSTGRES_DB: db_test_template
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: root
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
```

**`.dockerignore`:**
```
venv/
__pycache__/
*.pyc
.env
.git/
```

**Run:**
```bash
docker-compose up -d
```

Instructions in [migrations/README.md](migrations/README.md#estructura-de-archivos-docker).

---

## What's New (v1.2.0)

### User Permission Overrides (Phase 3) 🆕
Complete implementation of user-level permission overrides with temporal permissions support:
- **10 admin endpoints** - Full CRUD for managing user-specific permissions
- **3-tier priority system** - User overrides → Role templates → Default (none)
- **Temporal permissions** - Grant time-limited access with automatic expiration
- **Effective permissions API** - View complete permission resolution for any user
- **Permission extension** - Extend expiration dates for temporary permissions
- **Cleanup automation** - Endpoint to deactivate expired permissions
- **Audit trail** - Track who granted permissions and why

**New Admin Endpoints:**
- `POST /admin/user-permissions/grant/{user_id}` - Grant permission override
- `DELETE /admin/user-permissions/{id}` - Revoke permission
- `GET /admin/user-permissions/user/{user_id}` - List user's overrides
- `GET /admin/user-permissions/user/{user_id}/effective` - View effective permissions
- `GET /admin/user-permissions/user/{user_id}/details` - Detailed view with relations
- `PATCH /admin/user-permissions/{id}/extend` - Extend expiration
- `POST /admin/user-permissions/cleanup-expired` - Clean up expired permissions
- `GET /admin/user-permissions/levels` - Get permission level information

### Permission Autodiscovery (Phase 2) ✅
Automatic endpoint scanning and permission registration eliminates manual permission definition:
- **Automatic sync on startup** - Permissions table always reflects actual API routes
- **CLI command** - `python scripts.py autodiscover` with dry-run mode
- **79 endpoints discovered** - All entities automatically registered
- **Zero manual maintenance** - New entities auto-register permissions
- **Intelligent inference** - Extracts entity/action from HTTP method + path

### Companies Entity (v1.1.0) ✅
A base entity that can be of great initial use for any project. The entity has the following features:
- 20 production-ready endpoints
- 7 granular permissions
- TIN validation for 9 tax systems (RFC, EIN, NIF, VAT, CUIT, RUC, RUT, CNPJ, OTHER)
- Geographic relationships with countries/states
- Advanced search and statistics
- Status management (active, inactive, suspended, waiting)

### Bug Fixes
- Fixed Pydantic Field validation for optional fields with constraints (Phase 3)
- Fixed User.username AttributeError in /details endpoint (Phase 2)
- Updated bidirectional relationships in Country/State models (Phase 2)

### Improvements
- User-level permission override system with temporal support (Phase 3)
- Effective permission resolution with priority handling (Phase 3)
- Permission grant/revoke audit trail (Phase 3)
- N+1 query prevention with joinedload() (Phase 2)
- Indexed critical fields (tin, email, status) (Phase 2)
- Optimized search queries (Phase 2)

## Next Steps

- Add a method and UI to load the countries and states from a CSV file.
- UI demo to interact with base entities.
- Phase 4: Scope-based permissions (own/team/department filtering)

---

## Security Features

- JWT token authentication with expiration
- Password hashing (bcrypt via passlib)
- Role-based access control (5 levels)
- Granular entity-level permissions
- SQL injection prevention (ORM)
- Soft delete for data safety
- Complete audit trail
- CORS configuration

---

## License

MIT License - Free for personal and commercial use.

---

## Author

**Eric Guzman**

---

**Version:** 1.2.0
**Last Updated:** 2025-11-11
