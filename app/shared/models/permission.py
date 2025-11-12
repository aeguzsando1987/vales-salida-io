"""
Modelo Permission - Catálogo de permisos disponibles en el sistema

Almacena todos los permisos que existen en la API (auto-discovered o manuales).
Cada permiso representa una acción específica sobre una entidad.

Autor: Eric Guzman
Fecha: 2025-01-04
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Permission(Base):
    """
    Catálogo de permisos disponibles en el sistema.

    Un permiso define una acción específica sobre una entidad (ej: "read individuals").
    Los permisos se descubren automáticamente escaneando los endpoints de FastAPI,
    o se pueden crear manualmente.

    Relaciones:
        - template_items: Items de templates que referencian este permiso
        - user_permissions: Permisos específicos de usuarios que usan este permiso

    Ejemplo:
        permission = Permission(
            entity="individuals",
            action="read",
            endpoint="/individuals/",
            http_method="GET",
            description="List all individuals"
        )
    """

    __tablename__ = "permissions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Identificación del permiso
    entity = Column(String(100), nullable=False, index=True)  # "individuals", "countries", etc.
    action = Column(String(50), nullable=False, index=True)   # "read", "create", "update", "delete"
    endpoint = Column(String(255), nullable=False)            # "/individuals/{id}"
    http_method = Column(String(10), nullable=False)          # "GET", "POST", "PATCH", "DELETE"
    description = Column(Text, nullable=True)                 # Descripción del permiso

    # Estado
    is_active = Column(Boolean, default=True, nullable=False)

    # Auditoría (sin is_deleted ni updated_at según spec original)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    template_items = relationship(
        "PermissionTemplateItem",
        back_populates="permission",
        cascade="all, delete-orphan"
    )

    user_permissions = relationship(
        "UserPermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, entity='{self.entity}', action='{self.action}', method='{self.http_method}')>"

    def to_dict(self):
        """Convierte el permiso a diccionario para serialización."""
        return {
            "id": self.id,
            "entity": self.entity,
            "action": self.action,
            "endpoint": self.endpoint,
            "http_method": self.http_method,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }