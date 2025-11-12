"""
Modelo PermissionTemplateItem - Items individuales de un template de permisos

Vincula un PermissionTemplate con Permissions específicos, definiendo el nivel
y scope de acceso para cada permiso dentro del template.

Autor: Eric Guzman
Fecha: 2025-01-04
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class PermissionTemplateItem(Base):
    """
    Item que vincula un template con un permiso específico.

    Define el nivel de permiso (0-4) y el scope (all/own/team/department) que tendrá
    un usuario con ese template para una acción específica sobre una entidad.

    Relaciones:
        - template: Template al que pertenece este item
        - permission: Permiso específico que otorga

    Ejemplo:
        item = PermissionTemplateItem(
            template_id=1,  # Admin template
            permission_id=5,  # "read individuals"
            permission_level=4,  # DELETE (acceso total)
            scope="all"  # Ve todos los registros
        )
    """

    __tablename__ = "permission_template_items"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    template_id = Column(
        Integer,
        ForeignKey("permission_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Nivel y alcance del permiso
    permission_level = Column(Integer, nullable=False)  # 0-4 (None to Delete)
    scope = Column(String(20), default="all", nullable=False)  # all, own, team, department, none

    # Auditoría (sin is_deleted ni updated_at según spec original)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    template = relationship(
        "PermissionTemplate",
        back_populates="items"
    )

    permission = relationship(
        "Permission",
        back_populates="template_items"
    )

    def __repr__(self):
        return f"<PermissionTemplateItem(id={self.id}, template_id={self.template_id}, permission_id={self.permission_id}, level={self.permission_level}, scope='{self.scope}')>"

    def to_dict(self):
        """Convierte el item a diccionario para serialización."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "permission_id": self.permission_id,
            "permission_level": self.permission_level,
            "scope": self.scope,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }