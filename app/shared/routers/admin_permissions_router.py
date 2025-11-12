"""
Router: Admin User Permissions (Phase 3)

Endpoints de administración para gestionar permisos a nivel de usuario.
Solo accesibles para Admins.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db, User
from app.shared.dependencies import require_admin
from app.shared.services.user_permission_service import UserPermissionService
from app.shared.schemas.user_permission_schemas import (
    UserPermissionResponse,
    UserPermissionGrant,
    UserPermissionRevoke,
    UserPermissionListResponse,
    UserPermissionWithDetails,
    EffectivePermissionsResponse
)
from app.shared.models.user_permission import UserPermission
from app.shared.models.permission import Permission
from datetime import datetime

router = APIRouter(
    prefix="/admin/user-permissions",
    tags=["Admin - User Permissions"]
)


@router.post(
    "/grant/{user_id}",
    response_model=UserPermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Otorgar permiso a usuario"
)
def grant_user_permission(
    user_id: int,
    grant_data: UserPermissionGrant,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Otorga un permiso específico a un usuario (override).

    **Solo Admins**

    Args:
        user_id: ID del usuario a quien otorgar el permiso
        grant_data: Datos del permiso a otorgar

    Request Body:
        ```json
        {
            "entity": "companies",
            "action": "delete",
            "level": 4,
            "hours": 24,  // opcional, null = permanente
            "reason": "Acceso temporal para limpieza de datos"
        }
        ```

    Returns:
        UserPermission creado

    Ejemplos de uso:
        - Otorgar delete a Collaborator por 48 horas
        - Denegar acceso a Manager (level=0) permanentemente
        - Elevar Reader a Create (level=3) temporalmente
    """
    service = UserPermissionService(db)

    return service.grant_permission_by_entity_action(
        user_id=user_id,
        entity=grant_data.entity,
        action=grant_data.action,
        level=grant_data.level,
        granted_by_user_id=current_user.id,
        hours=grant_data.hours,
        reason=grant_data.reason
    )


@router.delete(
    "/{user_permission_id}",
    response_model=UserPermissionResponse,
    summary="Revocar permiso de usuario"
)
def revoke_user_permission(
    user_permission_id: int,
    revoke_data: UserPermissionRevoke,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Revoca un permiso de usuario específico (soft delete).

    **Solo Admins**

    Args:
        user_permission_id: ID del user permission a revocar
        revoke_data: Razón de la revocación

    Returns:
        UserPermission revocado (is_active=False)
    """
    service = UserPermissionService(db)
    return service.revoke_permission(user_permission_id, revoke_data.reason)


@router.get(
    "/user/{user_id}",
    response_model=List[UserPermissionResponse],
    summary="Listar permisos de usuario"
)
def list_user_permissions(
    user_id: int,
    active_only: bool = True,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Lista todos los permisos override de un usuario.

    **Solo Admins**

    Args:
        user_id: ID del usuario
        active_only: Si solo mostrar permisos activos

    Returns:
        Lista de UserPermission
    """
    service = UserPermissionService(db)
    return service.get_user_permissions(user_id, active_only)


@router.get(
    "/user/{user_id}/effective",
    response_model=dict,
    summary="Ver permisos efectivos de usuario"
)
def get_effective_permissions(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene un resumen completo de los permisos efectivos de un usuario.

    Muestra:
    - Permisos del rol (template)
    - Permisos override de usuario
    - Nivel efectivo para cada entity:action
    - Fuente del permiso (template vs user_override)

    **Solo Admins**

    Args:
        user_id: ID del usuario

    Returns:
        Resumen completo de permisos efectivos

    Response Example:
        ```json
        {
            "user_id": 5,
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "user_role": "Collaborator",
            "permissions": [
                {
                    "entity": "companies",
                    "action": "delete",
                    "effective_level": 4,
                    "source": "user_override",
                    "has_override": true,
                    "override_expires": "2025-11-08T10:00:00"
                },
                {
                    "entity": "individuals",
                    "action": "create",
                    "effective_level": 3,
                    "source": "template",
                    "has_override": false,
                    "override_expires": null
                }
            ]
        }
        ```
    """
    service = UserPermissionService(db)
    return service.get_effective_permissions_summary(user_id)


@router.get(
    "/user/{user_id}/details",
    response_model=List[dict],
    summary="Ver permisos de usuario con detalles completos"
)
def get_user_permissions_with_details(
    user_id: int,
    active_only: bool = True,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Lista permisos de usuario con detalles completos de permiso y estado.

    **Solo Admins**

    Args:
        user_id: ID del usuario
        active_only: Si solo mostrar activos

    Returns:
        Lista de permisos con detalles extendidos
    """
    service = UserPermissionService(db)
    user_permissions = service.get_user_permissions(user_id, active_only)

    result = []
    for up in user_permissions:
        # Obtener detalles del permiso
        permission = db.query(Permission).filter(
            Permission.id == up.permission_id
        ).first()

        # Obtener detalles del usuario que otorgó
        granted_by_user = None
        if up.granted_by:
            granted_by_user = db.query(User).filter(User.id == up.granted_by).first()

        # Verificar si está expirado
        is_expired = False
        if up.valid_until:
            is_expired = up.valid_until < datetime.utcnow()

        is_valid = up.is_active and not is_expired

        result.append({
            "id": up.id,
            "user_id": up.user_id,
            "permission_id": up.permission_id,
            "permission_level": up.permission_level,
            "valid_from": up.valid_from,
            "valid_until": up.valid_until,
            "reason": up.reason,
            "granted_by": up.granted_by,
            "is_active": up.is_active,
            "created_at": up.created_at,
            # Detalles del permiso
            "permission_entity": permission.entity if permission else None,
            "permission_action": permission.action if permission else None,
            "permission_endpoint": permission.endpoint if permission else None,
            "permission_http_method": permission.http_method if permission else None,
            # Detalles del usuario que otorgó
            "granted_by_name": granted_by_user.name if granted_by_user else None,
            "granted_by_email": granted_by_user.email if granted_by_user else None,
            # Estado
            "is_expired": is_expired,
            "is_valid": is_valid
        })

    return result


@router.patch(
    "/{user_permission_id}/extend",
    response_model=UserPermissionResponse,
    summary="Extender fecha de expiración"
)
def extend_permission_expiration(
    user_permission_id: int,
    additional_hours: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Extiende la fecha de expiración de un permiso temporal.

    **Solo Admins**

    Args:
        user_permission_id: ID del user permission
        additional_hours: Horas adicionales a agregar

    Returns:
        UserPermission con nueva fecha de expiración

    Raises:
        BusinessRuleError: Si es un permiso permanente
    """
    service = UserPermissionService(db)
    return service.extend_expiration(user_permission_id, additional_hours)


@router.post(
    "/cleanup-expired",
    response_model=dict,
    summary="Limpiar permisos expirados"
)
def cleanup_expired_permissions(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Desactiva todos los permisos temporales que han expirado.

    **Solo Admins**

    Esta operación debe ejecutarse periódicamente (ej: cronjob diario).

    Returns:
        Número de permisos desactivados

    Response Example:
        ```json
        {
            "message": "Permisos expirados limpiados exitosamente",
            "count": 5
        }
        ```
    """
    service = UserPermissionService(db)
    count = service.cleanup_expired_permissions()

    return {
        "message": "Permisos expirados limpiados exitosamente",
        "count": count
    }


@router.get(
    "/levels",
    response_model=List[dict],
    summary="Obtener información de niveles de permiso"
)
def get_permission_levels(
    current_user: User = Depends(require_admin),
):
    """
    Retorna información sobre los niveles de permiso disponibles.

    **Solo Admins**

    Returns:
        Lista de niveles con descripción

    Response Example:
        ```json
        [
            {
                "level": 0,
                "name": "None",
                "description": "Sin acceso",
                "includes": "-"
            },
            {
                "level": 1,
                "name": "Read",
                "description": "Solo lectura (GET)",
                "includes": "-"
            },
            ...
        ]
        ```
    """
    return [
        {
            "level": 0,
            "name": "None",
            "description": "Sin acceso",
            "includes": "-"
        },
        {
            "level": 1,
            "name": "Read",
            "description": "Solo lectura (GET endpoints)",
            "includes": "-"
        },
        {
            "level": 2,
            "name": "Update",
            "description": "Modificar registros (PATCH/PUT)",
            "includes": "Read"
        },
        {
            "level": 3,
            "name": "Create",
            "description": "Crear registros (POST)",
            "includes": "Read + Update"
        },
        {
            "level": 4,
            "name": "Delete",
            "description": "Eliminar registros (DELETE) - Acceso total",
            "includes": "Read + Update + Create"
        }
    ]
