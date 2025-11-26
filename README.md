# Sistema de Vales de Entrada/Salida de Material

> Sistema para automatizar la emisión y gestión de vales de entrada y salida de material con validación QR, gestión de retornos y control de estados.

# Tags
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-blue)](https://www.postgresql.org/)
[![Development](https://img.shields.io/badge/Status-In%20Development-yellow)](https://github.com/aeguzsando1987/vales-salida-io)

# Información General
**Repositorio:** https://github.com/aeguzsando1987/vales-salida-io
**Última Actualización:** 2025-11-19
**Estado de desarrollo:** Fase 1 - 40% Completado
Aún en desarrollo. Se agregaron nuevas entidades y se implementaron las principales funcionalidades para vauchers de entrada y salida. Se agregaron los permisos para los endpoints y se implementaron los controladores y servicios para los vauchers. Aun hacen falta entidades de trazabalidad de transacciones y un demo de GUI.

---

##  Características Core del Sistema

### Core Feats.
- **Validación QR** - Códigos QR con tokens seguros para validación de salidas
- **Gestión de Retornos** - Seguimiento de material con y sin retorno
- **Control de Estados** - 6 estados: PENDING, APPROVED, IN_TRANSIT, OVERDUE, CLOSED, CANCELLED
- **Múltiples Ubicaciones** - Sucursales, almacenes, proyectos, obras
- **Firmas Digitales** - Trazabilidad completa con approved_by, delivered_by, received_by
- **Generación de PDF** - Templates profesionales para impresión (Pendiente)
- **Sistema de Notificaciones** - Alertas por email/SMS (Pendiente)

### Arquitectura Técnica
- **7-Layer Architecture** - Router → Controller → Service → Repository → Model → Database
- **JWT Authentication** - OAuth2 con Swagger UI integrado
- **Autodiscovery de Permisos** - Sistema automático que detecta nuevos endpoints
- **Permisos Granulares** - 4 niveles (Read, Update, Create, Delete) con user-level overrides
- **Soft Delete & Audit** - Auditoría completa en todas las entidades
- **BaseRepository Genérico** - CRUD reutilizable con TypeVar[T]

### 📦 Entidades Implementadas

**Completas (100%):**
- **Users** - Usuarios del sistema (20 endpoints)
- **Individuals** - Personas/trabajadores (40+ campos, sistema JSONB)
- **Countries** - Países ISO 3166 (3 precargados)
- **States** - Estados/provincias (114 precargados)
- **Companies** - Empresas con validación fiscal (20 endpoints)
- **Branches** - Sucursales/ubicaciones genéricas
- **Products** - Cache de productos frecuentes (8 categorías, 10 endpoints)
- **Vaucher** - Vales unificados ENTRY/EXIT (20 endpoints)
- **VaucherDetails** - Líneas de artículos (máx 20 por vale)

**En Desarrollo:**
- **EntryLogs** - Registro de entradas físicas
- **OutLogs** - Registro de escaneos QR


---

## Instalación rápida

### Requisitos

- Python 3.8+
- PostgreSQL 12+
- Git

### Instalación

```bash
# Clonar y configurar el proyecto
git clone <repository-url> my-api-project
cd my-api-project
python -m venv venv

# Activar entorno virtual
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos (opcional)
createdb my_project_db
```

### Configuración

El proyecto cuenta con un archivo `.env.example` que debe ser copiado y renombrado a `.env`. Este nuevo archivo debe ser configurado con los valores correspondientes a su entorno de desarrollo.

Create `.env` file:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/my_project_db
SECRET_KEY=tu-super-mega-duper-llave-secreta-aqui
DEFAULT_ADMIN_EMAIL=admin@tuempresa.com
DEFAULT_ADMIN_PASSWORD=tu-super-secreto-password-aqui
PORT=8001 # Puerto de la API. Por defecto es 8001 en .env.example
```


Puedes generar una llave segura con el siguiente comando:
```bash
python scripts.py cmd_genkey
```

### Correr servidor

```bash
python main.py
```

**Acceso:**
- Swagger para documentación: http://localhost:8001/docs
- ReDoc para documentación: http://localhost:8001/redoc

**Default Admin:**
- Email: `admin@tuempresa.com`
- Password: `root`
---

## Documentación

### Guías de Desarrollo

- **[PATRON_DESARROLLO.md](PATRON_DESARROLLO.md)** - Patron completo para desarrollo con ejemplos
 **[ADDING_ENTITIES.md](ADDING_ENTITIES.md)** - Guia paso a paso en ingles para agregar nuevas entidades

### Agregar nueva entidad: Descripción general

1. Leer [PATRON_DESARROLLO.md](PATRON_DESARROLLO.md). Aqui encontrara detalles sobre el patron de desarrollo y como funciona el proyecto. 
2. Leer [ADDING_ENTITIES.md](ADDING_ENTITIES.md). Aqui encontrara una guia paso a paso en ingles para agregar nuevas entidades en ingles.
2. Crear `app/entities/<entity_name>/` con 6 archivos mas sus correspondientes __init__.py para importaciones correctas:
   - `models/<entity>_model.py` para la definicion de la entidad
   - `schemas/<entity>_schemas.py` para la validacion de la entidad
   - `repositories/<entity>_repository.py` para la logica de negocio de la entidad
   - `services/<entity>_service.py` para logicas adicionales y especiales de la entidad
   - `controllers/<entity>_controller.py` para la logica de negocio de la entidad
   - `routers/<entity>_router.py` para la logica de negocio de la entidad
3. Registtrar router en `main.py`
4. Correr `python main.py` y verificar que no haya errores
5. Ir a http://localhost:8001/docs o http://localhost:8001/redoc
6. Test en Swagger o ReDoc sus nuevos endpoints

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

### User Permission Overrides (Phase 3) 
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

### Permission Autodiscovery (Phase 2) 
Automatic endpoint scanning and permission registration eliminates manual permission definition:
- **Automatic sync on startup** - Permissions table always reflects actual API routes
- **CLI command** - `python scripts.py autodiscover` with dry-run mode
- **79 endpoints discovered** - All entities automatically registered
- **Zero manual maintenance** - New entities auto-register permissions
- **Intelligent inference** - Extracts entity/action from HTTP method + path

### Companies Entity (v1.1.0) 
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
