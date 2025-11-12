"""
Modelo UserPermission - Permisos específicos por usuario (overrides)

Permite asignar permisos específicos a usuarios individuales, sobreescribiendo
los permisos definidos por su template/rol. Soporta permisos temporales con expiración.

Autor: Eric Guzman
Fecha: 2025-01-04
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class UserPermission(Base):
    """
    Permiso específico asignado a un usuario individual.

    Permite otorgar permisos personalizados que sobrescriben los del template/rol,
    con soporte para permisos temporales que expiran automáticamente.

    Prioridad de resolución:
        1. UserPermission activo y no expirado (más alta)
        2. Template permission (del rol del usuario)
        3. Sin acceso (default)

    Relaciones:
        - user: Usuario al que se otorga el permiso (via user_id)
        - permission: Permiso específico otorgado
        - granted_by_user: Usuario que otorgó el permiso (via granted_by)

    Ejemplo:
        # Permiso temporal para eliminar individuals por 24 horas
        user_perm = UserPermission(
            user_id=10,
            permission_id=8,  # "delete individuals"
            permission_level=4,
            scope="all",
            valid_until=datetime.utcnow() + timedelta(hours=24),
            granted_by=1,  # Admin user
            reason="Emergency data cleanup"
        )
    """

    __tablename__ = "user_permissions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Nivel y alcance del permiso (override del template)
    permission_level = Column(Integer, nullable=False)  # 0-4, sobreescribe template
    scope = Column(String(20), default="all", nullable=False)  # all, own, team, department, none

    # Temporalidad del permiso
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=True)  # NULL = permanente

    # Auditoría del otorgamiento
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Quién otorgó el permiso
    reason = Column(Text, nullable=True)  # Razón del otorgamiento

    # Estado
    is_active = Column(Boolean, default=True, nullable=False)

    # Auditoría temporal
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    permission = relationship(
        "Permission",
        back_populates="user_permissions"
    )

    # Nota: Las relaciones con User se definen en database.py debido a que User
    # está definido ahí (legacy). Estas son las relaciones esperadas:
    # user = relationship("User", foreign_keys=[user_id], back_populates="permissions")
    # granted_by_user = relationship("User", foreign_keys=[granted_by])

    def __repr__(self):
        return f"<UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id}, level={self.permission_level}, scope='{self.scope}')>"

    def is_valid(self) -> bool:
        """
        Verifica si el permiso está activo y no ha expirado.

        Returns:
            bool: True si el permiso es válido, False si ha expirado o está inactivo
        """
        if not self.is_active:
            return False

        if self.valid_until is None:
            return True  # Permiso permanente

        return datetime.utcnow() <= self.valid_until

    def to_dict(self):
        """Convierte el permiso de usuario a diccionario para serialización."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "permission_id": self.permission_id,
            "permission_level": self.permission_level,
            "scope": self.scope,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "granted_by": self.granted_by,
            "reason": self.reason,
            "is_active": self.is_active,
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }