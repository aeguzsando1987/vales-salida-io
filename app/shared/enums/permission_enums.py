"""
Enums para el Sistema de Permisos Granulares

Define los niveles de permisos jerárquicos y scopes que se utilizan en el sistema.

Autor: Eric Guzman
Fecha: 2025-01-04
"""

from enum import Enum


class PermissionScopeEnum(str, Enum):
    """
    Alcance (scope) de los permisos - Define qué registros puede acceder un usuario.

    Por defecto, la plantilla usa solo 'all'. Los demás valores están disponibles
    para implementación futura cuando se agreguen campos team/department a las entidades.

    Uso actual (Fase 1):
        - ALL: Todos los registros (usado en todos los templates por defecto)

    Uso futuro (cuando se implemente):
        - OWN: Solo registros propios (requiere user_id en entidad)
        - TEAM: Registros del equipo (requiere team_id en entidad)
        - DEPARTMENT: Registros del departamento (requiere department_id en entidad)
        - NONE: Sin acceso
    """
    ALL = "all"              # Acceso a todos los registros
    OWN = "own"              # Solo registros propios (futuro)
    TEAM = "team"            # Registros del equipo (futuro)
    DEPARTMENT = "department"  # Registros del departamento (futuro)
    NONE = "none"            # Sin acceso


class PermissionLevelEnum(str, Enum):
    """
    Niveles de permiso jerárquicos para el sistema granular de permisos.

    Los niveles son acumulativos: un nivel superior incluye automáticamente
    todos los permisos de los niveles inferiores.

    Uso:
        # En PermissionTemplateItem o UserPermission:
        permission_level = PermissionLevelEnum.READ  # "1"

        # Comparación numérica:
        if int(user_level) >= int(PermissionLevelEnum.CREATE):
            # Usuario puede crear

        # En validaciones:
        required_level = PermissionLevelEnum.DELETE
        if int(effective_level) < int(required_level):
            raise InsufficientPermissionsError()

    Mapeo HTTP:
        - NONE (0): Sin acceso a ningún endpoint
        - READ (1): GET
        - UPDATE (2): GET, PATCH, PUT
        - CREATE (3): GET, PATCH, PUT, POST
        - DELETE (4): GET, PATCH, PUT, POST, DELETE
    """

    NONE = "0"      # Sin acceso - Sin permisos
    READ = "1"      # Solo lectura - GET endpoints
    UPDATE = "2"    # Lectura + modificación - GET, PATCH, PUT
    CREATE = "3"    # Lectura + Update + creación - GET, POST, PATCH, PUT
    DELETE = "4"    # Acceso total - Todas las operaciones (GET, POST, PATCH, PUT, DELETE)


# Mapeos para display y validaciones

PERMISSION_LEVEL_DISPLAY_NAMES = {
    PermissionLevelEnum.NONE: "Sin Acceso",
    PermissionLevelEnum.READ: "Lectura (GET)",
    PermissionLevelEnum.UPDATE: "Lectura + Modificación (GET, PATCH, PUT)",
    PermissionLevelEnum.CREATE: "Lectura + Update + Creación (GET, POST, PATCH, PUT)",
    PermissionLevelEnum.DELETE: "Acceso Total (Todas las operaciones)",
}


PERMISSION_LEVEL_HTTP_METHODS = {
    PermissionLevelEnum.NONE: [],
    PermissionLevelEnum.READ: ["GET"],
    PermissionLevelEnum.UPDATE: ["GET", "PATCH", "PUT"],
    PermissionLevelEnum.CREATE: ["GET", "PATCH", "PUT", "POST"],
    PermissionLevelEnum.DELETE: ["GET", "PATCH", "PUT", "POST", "DELETE"],
}


def get_permission_level_display(level: PermissionLevelEnum) -> str:
    """
    Obtiene el nombre de display para un nivel de permiso.

    Args:
        level: Nivel de permiso (enum)

    Returns:
        str: Nombre descriptivo del nivel

    Ejemplo:
        >>> get_permission_level_display(PermissionLevelEnum.CREATE)
        'Lectura + Update + Creación (GET, POST, PATCH, PUT)'
    """
    return PERMISSION_LEVEL_DISPLAY_NAMES.get(level, str(level))


def get_allowed_methods(level: PermissionLevelEnum) -> list:
    """
    Obtiene la lista de métodos HTTP permitidos para un nivel de permiso.

    Args:
        level: Nivel de permiso (enum)

    Returns:
        list: Lista de métodos HTTP permitidos

    Ejemplo:
        >>> get_allowed_methods(PermissionLevelEnum.UPDATE)
        ['GET', 'PATCH', 'PUT']
    """
    return PERMISSION_LEVEL_HTTP_METHODS.get(level, [])


def is_level_sufficient(effective_level: int, required_level: int) -> bool:
    """
    Verifica si el nivel efectivo es suficiente para el nivel requerido.

    Args:
        effective_level: Nivel de permiso que tiene el usuario (0-4)
        required_level: Nivel de permiso requerido para la acción (0-4)

    Returns:
        bool: True si el nivel efectivo es >= al requerido

    Ejemplo:
        >>> is_level_sufficient(3, 2)  # Usuario con CREATE, requiere UPDATE
        True
        >>> is_level_sufficient(1, 3)  # Usuario con READ, requiere CREATE
        False
    """
    return effective_level >= required_level
