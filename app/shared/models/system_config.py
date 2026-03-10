"""
SystemConfig - Tabla para configuraciones del sistema persistidas en BD.

Permite configurar parámetros como SMTP desde el panel de administración
sin necesidad de reiniciar el servidor o editar archivos .env.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    updated_by_user = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value[:20] if self.value else None}')>"
