"""
Modelo de Datos: State (Estado/Provincia/Departamento)

Entidad base de la plantilla que representa estados, provincias o departamentos.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class State(Base):
    """
    Modelo State

    Representa un estado, provincia o departamento de un pais.
    Relacion: Muchos States pertenecen a un Country (N:1)
    """
    __tablename__ = "states"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Campos principales
    name = Column(String(200), nullable=False, index=True, comment="Nombre del estado/provincia/departamento")
    code = Column(String(10), nullable=False, index=True, comment="Codigo del estado (ej: CA, TX, AGS)")

    # Relacion con Country
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False, index=True)
    country = relationship("Country", back_populates="states")

    # Relacion con Companies
    companies = relationship("Company", back_populates="state")

    # Campos de auditoria
    is_active = Column(Boolean, default=True, nullable=False, comment="Indica si el estado esta activo")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="Borrado logico")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Fecha de creacion")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Fecha de ultima actualizacion")

    def __repr__(self):
        return f"<State(id={self.id}, name={self.name}, code={self.code}, country_id={self.country_id})>"

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "country_id": self.country_id,
            "is_active": self.is_active,
        }