"""
Modelo IOManager (Contralor / Encargado de Entradas y Salidas)

Fuente de verdad transversal de "quién ES io manager / contralor".
La pertenencia activa a esta tabla habilita la SEGUNDA aprobación de vales
(nivel contraloría), independientemente del rol del usuario.

NOTA: distinto de Individual.io_manager_id (que indica "quién es el io manager
asignado a una persona"). Aquí registramos a las personas que SON contralores.
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class IOManager(Base):
    """Contralor transversal habilitado para la 2ª aprobación de vales."""
    __tablename__ = "io_managers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Quién es contralor (único: una persona no se registra dos veces)
    individual_id = Column(
        Integer,
        ForeignKey("individuals.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
        comment="Individual que es contralor (io manager)"
    )

    # ==================== AUDITORÍA ====================
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ==================== RELATIONSHIPS ====================
    individual = relationship("Individual", foreign_keys=[individual_id])

    def __repr__(self):
        return f"<IOManager(id={self.id}, individual_id={self.individual_id}, active={self.is_active})>"
