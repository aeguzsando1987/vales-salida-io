# Resolución de Problemas de Permisos - 2025-11-24

## Problema Identificado

Los endpoints de `voucher-details` retornaban error 403 "Permiso insuficiente" para el usuario Admin:

```
"Permiso insuficiente para voucher_details:create. Requiere nivel 3, tienes nivel 0"
```

## Causa Raíz

**Inconsistencia en nomenclatura de entidades:**

- **Router**: Usa guiones bajos `voucher_details` en decorador `require_permission("voucher_details", "create", min_level=3)`
- **Autodiscovery**: Extrae nombre desde path `/voucher-details/` → guarda como `voucher-details` (con guiones) en tabla `permissions`
- **Resolución de permisos**: Buscaba `voucher_details` pero en BD existe `voucher-details` → no encontraba match → retornaba nivel 0

## Solución Implementada

### 1. Fix en `dependencies.py` (Línea 455)

Agregada normalización en `get_effective_permission()`:

```python
# NORMALIZACIÓN: Convertir guiones bajos a guiones para compatibilidad
# Ejemplo: voucher_details -> voucher-details
normalized_entity = entity.replace("_", "-")

# Buscar con entidad normalizada
permission = db.query(Permission).filter(
    Permission.entity == normalized_entity,
    Permission.action == action
).first()
```

**Ventaja:** Funciona con ambos formatos (`voucher_details` o `voucher-details`).

### 2. Sistema de Auto-Asignación de Permisos (Nuevo)

Creado módulo `app/shared/test_auto_assign_permissions.py` con:

- **Función principal**: `auto_assign_new_permissions(db, dry_run=False)`
  - Detecta permisos sin asignaciones en `permission_template_items`
  - Asigna automáticamente a todos los roles con niveles predeterminados
  - Soporta modo dry-run para preview

- **Función específica**: `assign_permissions_for_entity(entity_name, db, dry_run=False)`
  - Asigna permisos de una entidad en particular
  - Útil para fix rápido

- **Configuración por rol** (`ROLE_PERMISSION_DEFAULTS`):
  ```python
  "Admin": default_level=4, scope="all"
  "Manager": default_level=3, scope="all"
  "Collaborator": default_level=3, scope="own"
  "Reader": default_level=1, scope="own"
  "Guest": default_level=0, scope="none"
  "Checker": default_level=0 + excepciones para QR
  ```

### 3. Integración con Autodiscovery

Modificado `autodiscover_permissions.py`:

```python
def autodiscover_and_sync(app, db, dry_run=False, auto_assign=True):
    # ... descubrimiento de endpoints ...

    # Auto-asignar permisos a roles si está habilitado
    if auto_assign:
        from app.shared.test_auto_assign_permissions import auto_assign_after_discovery
        stats = auto_assign_after_discovery(stats, db, dry_run=dry_run)
```

Ahora `autodiscover` automáticamente asigna permisos nuevos a roles.

### 4. Nuevo Comando CLI

Agregado a `scripts.py`:

```bash
# Vista previa de asignaciones faltantes
python scripts.py assign-permissions --dry-run

# Asignar todos los permisos faltantes
python scripts.py assign-permissions

# Asignar permisos de una entidad específica
python scripts.py assign-permissions --entity=voucher-details
```

## Verificación del Fix

### Test Manual con curl

```bash
# 1. Login como Admin
curl -X POST "http://localhost:8001/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alonso.guzman@gpamex.com&password=root"

# Respuesta:
# {"access_token":"eyJh...","token_type":"bearer"}

# 2. Crear detalle de voucher (requiere nivel 3)
curl -X POST "http://localhost:8001/voucher-details/?skip_similarity_search=true" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"voucher_id": 1, "line_number": 1, "item_name": "Laptop HP", "quantity": 2.0, "unit": "PZA"}'

# Respuesta exitosa (201 Created):
# {"id":1,"voucher_id":1,"product_id":3,"line_number":1,...}
```

### Verificación en Base de Datos

```python
# Verificar asignaciones para voucher-details
from database import SessionLocal
from app.shared.models.permission import Permission
from app.shared.models.permission_template import PermissionTemplate
from app.shared.models.permission_template_item import PermissionTemplateItem

db = SessionLocal()

# Admin template
admin = db.query(PermissionTemplate).filter(
    PermissionTemplate.role_name == 'Admin'
).first()

# Permisos de voucher-details
vd_perms = db.query(Permission).filter(
    Permission.entity == 'voucher-details'
).all()

# Items asignados
items = db.query(PermissionTemplateItem).filter(
    PermissionTemplateItem.template_id == admin.id,
    PermissionTemplateItem.permission_id.in_([p.id for p in vd_perms])
).all()

# Resultado esperado:
# 6 items con permission_level=4 (Delete/Full access)
```

## Archivos Modificados

1. **`app/shared/dependencies.py`** (línea 455)
   - Agregada normalización de entidad con `replace("_", "-")`

2. **`app/shared/autodiscover_permissions.py`** (línea 238)
   - Agregado parámetro `auto_assign=True`
   - Integración con sistema de auto-asignación

3. **`scripts.py`**
   - Nueva función `cmd_assign_permissions()` (línea 580)
   - Agregado comando en diccionario (línea 685)
   - Actualizada documentación (líneas 15, 18-25, 703)

## Archivos Creados

1. **`app/shared/test_auto_assign_permissions.py`** (449 líneas)
   - Sistema completo de auto-asignación de permisos
   - Configuración de niveles por rol
   - Funciones de asignación masiva y específica

2. **`PERMISSION_FIX_SUMMARY.md`** (este archivo)
   - Documentación del problema y solución

## Comandos Útiles

```bash
# Ver todos los permisos de una entidad
python scripts.py assign-permissions --entity=voucher-details --dry-run

# Asignar permisos faltantes después de crear nueva entidad
python scripts.py assign-permissions

# Autodiscovery + auto-asignación automática
python scripts.py restart
# (ejecuta autodiscovery en startup con auto_assign=True)
```

## Prevención Futura

**Para nuevas entidades:**

1. Usar guiones en nombres de router prefix: `/voucher-details/` (recomendado)
2. O usar guiones bajos en decorador: `require_permission("voucher-details", "create")`
3. El sistema ahora normaliza automáticamente, así que ambos formatos funcionan

**Flujo automatizado:**

```bash
# Después de crear nueva entidad
python scripts.py restart
# Autodiscovery detecta endpoints y asigna permisos automáticamente
```

## Estado Final

- ✅ Problema de permisos resuelto
- ✅ Sistema de auto-asignación implementado
- ✅ Integración con autodiscovery completada
- ✅ Comando CLI agregado
- ✅ Testing manual exitoso
- ✅ Normalización de entidades implementada

## Próximos Pasos (Opcional)

1. Renombrar `test_auto_assign_permissions.py` → `auto_assign_permissions.py` (remover prefijo "test" cuando esté en producción)
2. Agregar tests unitarios para auto-asignación
3. Documentar en CLAUDE.md la nueva funcionalidad
4. Crear endpoint API para asignación de permisos (opcional)

---

**Desarrollado por:** E. Guzman
**Fecha:** 2025-11-24
**Versión Sistema:** 1.2.0 (Phase 3)
