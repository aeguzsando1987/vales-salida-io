"""
Modelo PermissionTemplate - Templates de permisos por rol

Define conjuntos de permisos que se asignan a roles específicos.
Mapea 1:1 con los 5 roles existentes del sistema (Admin, Manager, Collaborator, Reader, Guest).

Autor: Eric Guzman
Fecha: 2025-01-04
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class PermissionTemplate(Base):
    """
    Template de permisos asociado a un rol del sistema.

    Un template agrupa múltiples permisos con sus niveles y scopes correspondientes,
    definiendo qué puede hacer un usuario con un rol específico.

    Relaciones:
        - items: Items que definen los permisos específicos del template

    Ejemplo:
        template = PermissionTemplate(
            role_name="Manager",
            description="Full access to users and entities with read/write permissions"
        )
    """

    __tablename__ = "permission_templates"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Identificación del template
    role_name = Column(String(50), unique=True, nullable=False, index=True)  # "Admin", "Manager", etc.
    description = Column(Text, nullable=True)  # Descripción del rol

    # Estado
    is_active = Column(Boolean, default=True, nullable=False)

    # Auditoría (sin is_deleted ni updated_at según spec original)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    items = relationship(
        "PermissionTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<PermissionTemplate(id={self.id}, role_name='{self.role_name}')>"

    def to_dict(self):
        """Convierte el template a diccionario para serialización."""
        return {
            "id": self.id,
            "role_name": self.role_name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def get_permission_level(self, entity: str, action: str) -> int:
        """
        Obtiene el nivel de permiso para una entidad/acción específica en este template.

        Args:
            entity: Nombre de la entidad (ej: "individuals")
            action: Acción a verificar (ej: "read")

        Returns:
            int: Nivel de permiso (0-4), o 0 si no existe

        Ejemplo:
            level = admin_template.get_permission_level("individuals", "delete")
            # Retorna 4 para Admin
        """
        for item in self.items:
            if item.permission.entity == entity and item.permission.action == action:
                return int(item.permission_level)
        return 0  # Sin permiso por defecto