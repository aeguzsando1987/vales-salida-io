"""
Datos semilla para el sistema de permisos granulares

Define los permisos base, templates por rol, y la matriz de permisos inicial.
Todos los scopes están configurados en 'all' por defecto (acceso total).

IMPORTANTE: Este archivo se ejecuta en cada inicio del servidor de forma idempotente.
Solo se insertan datos si las tablas están vacías.

NOTA SOBRE AUTODISCOVERY (Phase 2):
A partir de la version 1.1.1, el sistema incluye autodiscovery automatico de permisos.
Los permisos definidos aqui sirven como SEED INICIAL y EJEMPLO.
El autodiscovery escanea automaticamente todos los endpoints al iniciar el servidor y:
  1. Detecta nuevas rutas y las agrega a la tabla permissions
  2. No duplica permisos existentes
  3. Permite agregar entidades sin modificar manualmente este archivo

Para entidades nuevas:
  - Opcion 1 (Recomendado): Dejar que autodiscovery las detecte automaticamente
  - Opcion 2: Agregarlas manualmente aqui si necesitas descripciones custom
  - Opcion 3: Usar comando CLI: python scripts.py autodiscover --dry-run

Autor: Eric Guzman
Fecha creacion: 2025-01-04
Ultima actualizacion: 2025-11-06 (Phase 2: Autodiscovery)
"""

# ==================== PERMISOS BASE ====================
# Convención:
# - CRUD estándar: list, get, create, update, delete
# - Custom: <action_descriptive> para endpoints especiales
#
# NOTA: Los permisos aqui definidos son EJEMPLOS de las entidades existentes.
# El sistema de autodiscovery complementa esta lista automaticamente.

BASE_PERMISSIONS = [
    # ==================== INDIVIDUALS ====================
    # CRUD estándar
    {
        "entity": "individuals",
        "action": "list",
        "endpoint": "/individuals/",
        "http_method": "GET",
        "description": "List all individuals"
    },
    {
        "entity": "individuals",
        "action": "get",
        "endpoint": "/individuals/{id}",
        "http_method": "GET",
        "description": "Get individual by ID"
    },
    {
        "entity": "individuals",
        "action": "create",
        "endpoint": "/individuals/",
        "http_method": "POST",
        "description": "Create new individual"
    },
    {
        "entity": "individuals",
        "action": "update",
        "endpoint": "/individuals/{id}",
        "http_method": "PUT",
        "description": "Update individual"
    },
    {
        "entity": "individuals",
        "action": "delete",
        "endpoint": "/individuals/{id}",
        "http_method": "DELETE",
        "description": "Delete individual (soft delete)"
    },

    # Operaciones especiales
    {
        "entity": "individuals",
        "action": "create_with_user",
        "endpoint": "/individuals/with-user",
        "http_method": "POST",
        "description": "Create individual with new user"
    },
    {
        "entity": "individuals",
        "action": "search",
        "endpoint": "/individuals/search",
        "http_method": "GET",
        "description": "Advanced search with dynamic filters"
    },
    {
        "entity": "individuals",
        "action": "verify",
        "endpoint": "/individuals/{id}/verify",
        "http_method": "PATCH",
        "description": "Verify individual"
    },
    {
        "entity": "individuals",
        "action": "view_statistics",
        "endpoint": "/individuals/statistics",
        "http_method": "GET",
        "description": "View global statistics"
    },

    # Gestión de skills
    {
        "entity": "individuals",
        "action": "manage_skills",
        "endpoint": "/individuals/{id}/skills",
        "http_method": "POST",
        "description": "Manage individual skills (add/update/delete)"
    },
    {
        "entity": "individuals",
        "action": "view_skills",
        "endpoint": "/individuals/{id}/skills/*",
        "http_method": "GET",
        "description": "View individual skills and summaries"
    },

    # Countries (solo lectura)
    {
        "entity": "countries",
        "action": "read",
        "endpoint": "/countries/",
        "http_method": "GET",
        "description": "List and read countries"
    },

    # States (solo lectura)
    {
        "entity": "states",
        "action": "read",
        "endpoint": "/states/by-country/{country_id}",
        "http_method": "GET",
        "description": "List states by country"
    },

    # Users (gestión de usuarios - solo roles elevados)
    {
        "entity": "users",
        "action": "read",
        "endpoint": "/users/",
        "http_method": "GET",
        "description": "List and read users"
    },
    {
        "entity": "users",
        "action": "create",
        "endpoint": "/users/",
        "http_method": "POST",
        "description": "Create new user"
    },
    {
        "entity": "users",
        "action": "update",
        "endpoint": "/users/{id}",
        "http_method": "PATCH",
        "description": "Update user"
    },
    {
        "entity": "users",
        "action": "delete",
        "endpoint": "/users/{id}",
        "http_method": "DELETE",
        "description": "Delete user"
    },

    # ==================== COMPANIES ====================
    # CRUD estándar
    {
        "entity": "companies",
        "action": "list",
        "endpoint": "/companies/",
        "http_method": "GET",
        "description": "List all companies"
    },
    {
        "entity": "companies",
        "action": "get",
        "endpoint": "/companies/{id}",
        "http_method": "GET",
        "description": "Get company by ID"
    },
    {
        "entity": "companies",
        "action": "create",
        "endpoint": "/companies/",
        "http_method": "POST",
        "description": "Create new company"
    },
    {
        "entity": "companies",
        "action": "update",
        "endpoint": "/companies/{id}",
        "http_method": "PUT",
        "description": "Update company"
    },
    {
        "entity": "companies",
        "action": "delete",
        "endpoint": "/companies/{id}",
        "http_method": "DELETE",
        "description": "Delete company (soft delete)"
    },

    # Operaciones especiales
    {
        "entity": "companies",
        "action": "search",
        "endpoint": "/companies/search/*",
        "http_method": "GET",
        "description": "Search companies by TIN or advanced filters"
    },
    {
        "entity": "companies",
        "action": "view_statistics",
        "endpoint": "/companies/statistics/overview",
        "http_method": "GET",
        "description": "View company statistics"
    },
]


# ==================== TEMPLATES DE PERMISOS POR ROL ====================

PERMISSION_TEMPLATES = [
    {
        "role_name": "Admin",
        "description": "Full access - All operations on all entities"
    },
    {
        "role_name": "Manager",
        "description": "CRUD on users and entities - Management level access"
    },
    {
        "role_name": "Collaborator",
        "description": "CRUD on entities only - No user management"
    },
    {
        "role_name": "Reader",
        "description": "Read-only access to all entities"
    },
    {
        "role_name": "Guest",
        "description": "Limited read access - Countries and states only"
    },
    {
        "role_name": "Checker",
        "description": "Security guard - QR validation and limited read access for vouchers"
    },
]


# ==================== MATRIZ DE PERMISOS POR ROL ====================

TEMPLATE_PERMISSION_MATRIX = {
    # Admin: Acceso total (level 4) a todo, scope="all"
    "Admin": [
        # Individuals - CRUD estándar
        {"entity": "individuals", "action": "list", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "get", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "create", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "update", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "delete", "level": 4, "scope": "all"},
        # Individuals - Operaciones especiales
        {"entity": "individuals", "action": "create_with_user", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "search", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "verify", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "view_statistics", "level": 4, "scope": "all"},
        # Individuals - Skills
        {"entity": "individuals", "action": "manage_skills", "level": 4, "scope": "all"},
        {"entity": "individuals", "action": "view_skills", "level": 4, "scope": "all"},
        # Catálogos
        {"entity": "countries", "action": "read", "level": 4, "scope": "all"},
        {"entity": "states", "action": "read", "level": 4, "scope": "all"},
        # Users
        {"entity": "users", "action": "read", "level": 4, "scope": "all"},
        {"entity": "users", "action": "create", "level": 4, "scope": "all"},
        {"entity": "users", "action": "update", "level": 4, "scope": "all"},
        {"entity": "users", "action": "delete", "level": 4, "scope": "all"},
        # Companies - CRUD estándar
        {"entity": "companies", "action": "list", "level": 4, "scope": "all"},
        {"entity": "companies", "action": "get", "level": 4, "scope": "all"},
        {"entity": "companies", "action": "create", "level": 4, "scope": "all"},
        {"entity": "companies", "action": "update", "level": 4, "scope": "all"},
        {"entity": "companies", "action": "delete", "level": 4, "scope": "all"},
        # Companies - Operaciones especiales
        {"entity": "companies", "action": "search", "level": 4, "scope": "all"},
        {"entity": "companies", "action": "view_statistics", "level": 4, "scope": "all"},
    ],

    # Manager: CRUD completo en individuals y users (level 3)
    "Manager": [
        # Individuals - CRUD estándar
        {"entity": "individuals", "action": "list", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "get", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "create", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "update", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "delete", "level": 3, "scope": "all"},
        # Individuals - Operaciones especiales
        {"entity": "individuals", "action": "create_with_user", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "search", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "verify", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "view_statistics", "level": 3, "scope": "all"},
        # Individuals - Skills
        {"entity": "individuals", "action": "manage_skills", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "view_skills", "level": 3, "scope": "all"},
        # Catálogos
        {"entity": "countries", "action": "read", "level": 1, "scope": "all"},
        {"entity": "states", "action": "read", "level": 1, "scope": "all"},
        # Users
        {"entity": "users", "action": "read", "level": 3, "scope": "all"},
        {"entity": "users", "action": "create", "level": 3, "scope": "all"},
        {"entity": "users", "action": "update", "level": 3, "scope": "all"},
        {"entity": "users", "action": "delete", "level": 3, "scope": "all"},
        # Companies - CRUD estándar
        {"entity": "companies", "action": "list", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "get", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "create", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "update", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "delete", "level": 3, "scope": "all"},
        # Companies - Operaciones especiales
        {"entity": "companies", "action": "search", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "view_statistics", "level": 3, "scope": "all"},
    ],

    # Collaborator: CRUD en individuals (level 3), sin gestión de users
    "Collaborator": [
        # Individuals - CRUD estándar
        {"entity": "individuals", "action": "list", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "get", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "create", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "update", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "delete", "level": 2, "scope": "all"},  # Nivel 2: no puede eliminar
        # Individuals - Operaciones especiales (limitadas)
        {"entity": "individuals", "action": "create_with_user", "level": 2, "scope": "all"},
        {"entity": "individuals", "action": "search", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "verify", "level": 2, "scope": "all"},
        {"entity": "individuals", "action": "view_statistics", "level": 1, "scope": "all"},  # Solo lectura
        # Individuals - Skills
        {"entity": "individuals", "action": "manage_skills", "level": 3, "scope": "all"},
        {"entity": "individuals", "action": "view_skills", "level": 3, "scope": "all"},
        # Catálogos
        {"entity": "countries", "action": "read", "level": 1, "scope": "all"},
        {"entity": "states", "action": "read", "level": 1, "scope": "all"},
        # Users - solo lectura
        {"entity": "users", "action": "read", "level": 1, "scope": "all"},
        # Companies - CRUD (sin delete)
        {"entity": "companies", "action": "list", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "get", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "create", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "update", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "delete", "level": 2, "scope": "all"},  # Nivel 2: no puede eliminar
        # Companies - Operaciones especiales
        {"entity": "companies", "action": "search", "level": 3, "scope": "all"},
        {"entity": "companies", "action": "view_statistics", "level": 1, "scope": "all"},  # Solo lectura
        # Branches - lectura para seleccionar ubicación
        {"entity": "branches", "action": "list", "level": 1, "scope": "all"},
        {"entity": "branches", "action": "get", "level": 1, "scope": "all"},
        # Vouchers - crear y gestionar propios (COLABORADOR role)
        {"entity": "vouchers", "action": "create", "level": 3, "scope": "own"},
        {"entity": "vouchers", "action": "list", "level": 1, "scope": "own"},
        {"entity": "vouchers", "action": "get", "level": 1, "scope": "own"},
        {"entity": "vouchers", "action": "update", "level": 2, "scope": "own"},
        # Products - crear productos frecuentes
        {"entity": "products", "action": "create", "level": 3, "scope": "all"},
        {"entity": "products", "action": "list", "level": 1, "scope": "all"},
        {"entity": "products", "action": "get", "level": 1, "scope": "all"},
    ],

    # Reader: Solo lectura (level 1) en todo
    "Reader": [
        # Individuals - solo lectura
        {"entity": "individuals", "action": "list", "level": 1, "scope": "all"},
        {"entity": "individuals", "action": "get", "level": 1, "scope": "all"},
        {"entity": "individuals", "action": "search", "level": 1, "scope": "all"},
        {"entity": "individuals", "action": "view_statistics", "level": 1, "scope": "all"},
        {"entity": "individuals", "action": "view_skills", "level": 1, "scope": "all"},
        # Catálogos
        {"entity": "countries", "action": "read", "level": 1, "scope": "all"},
        {"entity": "states", "action": "read", "level": 1, "scope": "all"},
        # Users - solo lectura
        {"entity": "users", "action": "read", "level": 1, "scope": "all"},
        # Companies - solo lectura
        {"entity": "companies", "action": "list", "level": 1, "scope": "all"},
        {"entity": "companies", "action": "get", "level": 1, "scope": "all"},
        {"entity": "companies", "action": "search", "level": 1, "scope": "all"},
        {"entity": "companies", "action": "view_statistics", "level": 1, "scope": "all"},
    ],

    # Guest: Solo lectura de catálogos (countries/states)
    "Guest": [
        {"entity": "countries", "action": "read", "level": 1, "scope": "all"},
        {"entity": "states", "action": "read", "level": 1, "scope": "all"},
    ],

    # Checker: Security guard role - QR scanning and limited voucher read access
    "Checker": [
        # Vouchers - solo lectura para validación
        {"entity": "vouchers", "action": "list", "level": 1, "scope": "all"},
        {"entity": "vouchers", "action": "get", "level": 1, "scope": "all"},
        # Out logs - crear escaneos y ver propios
        {"entity": "out_logs", "action": "create", "level": 3, "scope": "all"},
        {"entity": "out_logs", "action": "read", "level": 1, "scope": "own"},
        # Branches - lectura para validar ubicaciones
        {"entity": "branches", "action": "read", "level": 1, "scope": "all"},
        # Products - lectura para validar artículos
        {"entity": "products", "action": "read", "level": 1, "scope": "all"},
        # Catálogos básicos
        {"entity": "countries", "action": "read", "level": 1, "scope": "all"},
        {"entity": "states", "action": "read", "level": 1, "scope": "all"},
    ],
}


# ==================== UTILIDADES ====================

def get_permission_by_entity_action(permissions_list, entity, action):
    """
    Busca un permiso por entity + action en una lista de permisos.

    Args:
        permissions_list: Lista de objetos Permission
        entity: Nombre de la entidad
        action: Acción del permiso

    Returns:
        Permission object o None
    """
    for perm in permissions_list:
        if perm.entity == entity and perm.action == action:
            return perm
    return None


def get_template_by_role(templates_list, role_name):
    """
    Busca un template por nombre de rol en una lista de templates.

    Args:
        templates_list: Lista de objetos PermissionTemplate
        role_name: Nombre del rol

    Returns:
        PermissionTemplate object o None
    """
    for template in templates_list:
        if template.role_name == role_name:
            return template
    return None