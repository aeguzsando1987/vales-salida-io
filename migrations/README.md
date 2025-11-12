# Migraciones de Base de Datos

## Aplicar Migración: Add User Soft Delete Fields

Esta migración agrega los campos `deleted_at` y `deleted_by` a la tabla `users` para completar la auditoría del soft delete.

### Opción 1: Con psql (recomendado)

```bash
psql -U postgres -d bapta_simple_template -f migrations/add_user_soft_delete_fields.sql
```

### Opción 2: Con Python

```python
from database import engine
from sqlalchemy import text

with open('migrations/add_user_soft_delete_fields.sql', 'r') as f:
    sql = f.read()

with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()
```

### Opción 3: Desde Python (ejecutar este script)

```bash
python -c "
from database import engine
from sqlalchemy import text

with open('migrations/add_user_soft_delete_fields.sql', 'r') as f:
    sql = f.read()

with engine.begin() as conn:
    for statement in sql.split(';'):
        if statement.strip():
            conn.execute(text(statement))

print('Migración aplicada exitosamente')
"
```

## Verificar Migración

```sql
-- Ver estructura de la tabla users
\d users

-- O con SQL
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('deleted_at', 'deleted_by');
```

## Cambios Realizados

1. **Modelo User** (`database.py`):
   - Agregado `deleted_at = Column(DateTime, nullable=True)`
   - Agregado `deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)`
   - Agregado relación `deleted_by_user`

2. **PersonRepository** (`person_repository.py`):
   - `soft_delete_person()` ahora actualiza `deleted_at` y `deleted_by`

3. **PersonService** (`person_service.py`):
   - `_validate_deletion_rules()` ahora elimina el usuario asociado (si existe)
   - Al eliminar Person con usuario, ambos se eliminan con soft delete

## Funcionalidad Nueva

Al eliminar una persona:
1. Se actualiza `is_deleted = True`
2. Se actualiza `deleted_at = ahora()`
3. Se actualiza `deleted_by = current_user_id`
4. Si tiene usuario asociado, el usuario también se elimina con soft delete

---

## Dockerización del Proyecto (Futuro)

### Quick Start con Docker

```bash
# Levantar toda la aplicación (API + PostgreSQL)
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Detener contenedores
docker-compose down

# Detener y eliminar volúmenes (CUIDADO: elimina datos)
docker-compose down -v
```

### Estructura de Archivos Docker

**Archivos a crear en la raíz del proyecto:**

1. **`Dockerfile`** - Contenedor de FastAPI
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["python", "main.py"]
```

2. **`docker-compose.yml`** - Orquestación de servicios
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
    volumes:
      - .:/app

  db:
    image: postgres:12
    environment:
      POSTGRES_DB: db_test_template
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: root
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

3. **`.dockerignore`**
```
venv/
__pycache__/
*.pyc
.env
.git/
.vscode/
*.log
```

### Variables de Entorno

Crear `.env` para Docker:
```env
DATABASE_URL=postgresql://postgres:root@db:5432/db_test_template
SECRET_KEY=supersecret:99999...
PORT=8001
```

### Comandos Útiles

```bash
# Rebuild sin caché
docker-compose build --no-cache

# Ejecutar migraciones en contenedor
docker-compose exec api python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Acceder a shell del contenedor
docker-compose exec api bash

# Acceder a PostgreSQL
docker-compose exec db psql -U postgres -d db_test_template

# Ver estado de contenedores
docker-compose ps
```

### Notas Importantes

- El servicio `db` debe estar disponible antes de `api` (usar `depends_on`)
- Los datos de PostgreSQL persisten en el volumen `postgres_data`
- Para desarrollo, montar `.:/app` permite hot-reload
- En producción, remover el volume mount y usar imagen compilada
