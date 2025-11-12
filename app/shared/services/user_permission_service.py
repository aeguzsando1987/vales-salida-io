"""
Service: User Permission (Phase 3)

Servicio para gestionar permisos a nivel de usuario que sobrescriben
los permisos del rol. Soporta permisos temporales con expiración.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.shared.models.user_permission import UserPermission
from app.shared.models.permission import Permission
from database import User
from app.shared.exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleError
)


class UserPermissionService:
    """Servicio para lógica de negocio de User Permissions."""

    def __init__(self, db: Session):
        self.db = db

    def grant_permission(
        self,
        user_id: int,
        permission_id: int,
        level: int,
        granted_by_user_id: int,
        hours: Optional[int] = None,
        reason: Optional[str] = None
    ) -> UserPermission:
        """
        Otorga un permiso específico a un usuario.

        Args:
            user_id: ID del usuario a quien se otorga el permiso
            permission_id: ID del permiso a otorgar
            level: Nivel de permiso (0-4)
            granted_by_user_id: ID del usuario que otorga el permiso
            hours: Duración en horas (None = permanente)
            reason: Razón del override

        Returns:
            UserPermission creado

        Raises:
            EntityNotFoundError: Si el usuario o permiso no existe
            EntityAlreadyExistsError: Si ya existe un override activo
            BusinessRuleError: Si las validaciones fallan
        """
        # Validar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EntityNotFoundError("User", user_id)

        # Validar que el permiso existe
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise EntityNotFoundError("Permission", permission_id)

        # Validar nivel de permiso
        if level < 0 or level > 4:
            raise BusinessRuleError(
                message="Nivel de permiso inválido",
                details={"level": "Debe ser entre 0 (None) y 4 (Delete)"}
            )

        # Verificar si ya existe un override activo
        existing = self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,
            UserPermission.is_active == True
        ).first()

        if existing:
            raise EntityAlreadyExistsError(
                "UserPermission",
                "user_permission",
                f"user_id={user_id}, permission_id={permission_id}"
            )

        # Calcular fecha de expiración si es temporal
        valid_until = None
        if hours:
            valid_until = datetime.utcnow() + timedelta(hours=hours)

        # Crear user permission
        user_permission = UserPermission(
            user_id=user_id,
            permission_id=permission_id,
            permission_level=level,
            valid_from=datetime.utcnow(),
            valid_until=valid_until,
            granted_by=granted_by_user_id,
            reason=reason,
            is_active=True
        )

        try:
            self.db.add(user_permission)
            self.db.commit()
            self.db.refresh(user_permission)
            return user_permission
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(
                message="Error al otorgar permiso",
                details={"error": str(e)}
            )

    def grant_permission_by_entity_action(
        self,
        user_id: int,
        entity: str,
        action: str,
        level: int,
        granted_by_user_id: int,
        hours: Optional[int] = None,
        reason: Optional[str] = None
    ) -> UserPermission:
        """
        Otorga un permiso a un usuario usando entity:action en lugar de permission_id.

        Wrapper conveniente para grant_permission que busca el permission_id
        a partir de entity y action.

        Args:
            user_id: ID del usuario
            entity: Entidad (ej: "companies")
            action: Acción (ej: "delete")
            level: Nivel de permiso (0-4)
            granted_by_user_id: ID del admin que otorga
            hours: Duración en horas
            reason: Razón del override

        Returns:
            UserPermission creado

        Raises:
            EntityNotFoundError: Si el permiso entity:action no existe
        """
        # Buscar el permiso
        permission = self.db.query(Permission).filter(
            Permission.entity == entity,
            Permission.action == action
        ).first()

        if not permission:
            raise EntityNotFoundError(
                "Permission",
                f"{entity}:{action} (no registrado en sistema)"
            )

        return self.grant_permission(
            user_id=user_id,
            permission_id=permission.id,
            level=level,
            granted_by_user_id=granted_by_user_id,
            hours=hours,
            reason=reason
        )

    def revoke_permission(
        self,
        user_permission_id: int,
        reason: Optional[str] = None
    ) -> UserPermission:
        """
        Revoca un permiso de usuario (soft delete).

        Args:
            user_permission_id: ID del user permission
            reason: Razón de la revocación

        Returns:
            UserPermission revocado

        Raises:
            EntityNotFoundError: Si el user permission no existe
        """
        user_permission = self.db.query(UserPermission).filter(
            UserPermission.id == user_permission_id
        ).first()

        if not user_permission:
            raise EntityNotFoundError("UserPermission", user_permission_id)

        user_permission.is_active = False
        if reason:
            user_permission.reason = f"{user_permission.reason or ''} | Revocado: {reason}"

        try:
            self.db.commit()
            self.db.refresh(user_permission)
            return user_permission
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(
                message="Error al revocar permiso",
                details={"error": str(e)}
            )

    def get_user_permissions(
        self,
        user_id: int,
        active_only: bool = True
    ) -> List[UserPermission]:
        """
        Obtiene todos los permisos de un usuario.

        Args:
            user_id: ID del usuario
            active_only: Si solo mostrar permisos activos

        Returns:
            Lista de UserPermission
        """
        query = self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id
        )

        if active_only:
            query = query.filter(UserPermission.is_active == True)

        return query.all()

    def get_user_permission_by_id(self, user_permission_id: int) -> UserPermission:
        """
        Obtiene un user permission por ID.

        Args:
            user_permission_id: ID del user permission

        Returns:
            UserPermission

        Raises:
            EntityNotFoundError: Si no existe
        """
        user_permission = self.db.query(UserPermission).filter(
            UserPermission.id == user_permission_id
        ).first()

        if not user_permission:
            raise EntityNotFoundError("UserPermission", user_permission_id)

        return user_permission

    def update_permission_level(
        self,
        user_permission_id: int,
        new_level: int
    ) -> UserPermission:
        """
        Actualiza el nivel de un permiso existente.

        Args:
            user_permission_id: ID del user permission
            new_level: Nuevo nivel (0-4)

        Returns:
            UserPermission actualizado

        Raises:
            EntityNotFoundError: Si no existe
            BusinessRuleError: Si el nivel es inválido
        """
        if new_level < 0 or new_level > 4:
            raise BusinessRuleError(
                message="Nivel de permiso inválido",
                details={"level": "Debe ser entre 0 y 4"}
            )

        user_permission = self.get_user_permission_by_id(user_permission_id)
        user_permission.permission_level = new_level

        try:
            self.db.commit()
            self.db.refresh(user_permission)
            return user_permission
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(
                message="Error al actualizar nivel",
                details={"error": str(e)}
            )

    def extend_expiration(
        self,
        user_permission_id: int,
        additional_hours: int
    ) -> UserPermission:
        """
        Extiende la fecha de expiración de un permiso temporal.

        Args:
            user_permission_id: ID del user permission
            additional_hours: Horas adicionales a agregar

        Returns:
            UserPermission actualizado

        Raises:
            EntityNotFoundError: Si no existe
            BusinessRuleError: Si no es un permiso temporal
        """
        user_permission = self.get_user_permission_by_id(user_permission_id)

        if not user_permission.valid_until:
            raise BusinessRuleError(
                message="No se puede extender un permiso permanente",
                details={"valid_until": "NULL (permanente)"}
            )

        user_permission.valid_until += timedelta(hours=additional_hours)

        try:
            self.db.commit()
            self.db.refresh(user_permission)
            return user_permission
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(
                message="Error al extender expiración",
                details={"error": str(e)}
            )

    def cleanup_expired_permissions(self) -> int:
        """
        Desactiva permisos temporales expirados.

        Esta función debe ejecutarse periódicamente (ej: cronjob).

        Returns:
            Número de permisos desactivados
        """
        expired_permissions = self.db.query(UserPermission).filter(
            UserPermission.is_active == True,
            UserPermission.valid_until.isnot(None),
            UserPermission.valid_until < datetime.utcnow()
        ).all()

        count = 0
        for perm in expired_permissions:
            perm.is_active = False
            perm.reason = f"{perm.reason or ''} | Auto-desactivado por expiración"
            count += 1

        try:
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(
                message="Error al limpiar permisos expirados",
                details={"error": str(e)}
            )

    def get_effective_permissions_summary(self, user_id: int) -> dict:
        """
        Obtiene un resumen de los permisos efectivos de un usuario.

        Muestra tanto los permisos del rol como los overrides de usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con resumen de permisos efectivos
        """
        from app.shared.dependencies import get_effective_permission

        # Obtener usuario
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EntityNotFoundError("User", user_id)

        # Obtener todos los permisos del sistema
        all_permissions = self.db.query(Permission).all()

        # Calcular nivel efectivo para cada permiso
        permissions_summary = []
        for permission in all_permissions:
            effective_level = get_effective_permission(
                user_id,
                permission.entity,
                permission.action,
                self.db
            )

            # Determinar fuente del permiso
            user_override = self.db.query(UserPermission).filter(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission.id,
                UserPermission.is_active == True
            ).first()

            if user_override:
                # Verificar si está expirado
                if user_override.valid_until:
                    is_expired = user_override.valid_until < datetime.utcnow()
                    source = "template" if is_expired else "user_override"
                else:
                    source = "user_override"
            else:
                source = "template"

            permissions_summary.append({
                "entity": permission.entity,
                "action": permission.action,
                "effective_level": effective_level,
                "source": source,
                "has_override": user_override is not None,
                "override_expires": user_override.valid_until if user_override else None
            })

        role_mapping = {
            1: "Admin",
            2: "Manager",
            3: "Collaborator",
            4: "Reader",
            5: "Guest"
        }

        return {
            "user_id": user_id,
            "user_name": user.name,
            "user_email": user.email,
            "user_role": role_mapping.get(user.role, "Unknown"),
            "permissions": permissions_summary
        }
