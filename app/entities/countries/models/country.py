"""
Modelo de Datos: Country (Pais)

Entidad base de la plantilla que representa paises usando codigos ISO 3166.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Country(Base):
    """
    Modelo Country

    Representa un pais con codigos estandar ISO 3166.
    Relacion: Un Country tiene muchos States (1:N)
    """
    __tablename__ = "countries"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Campos principales
    name = Column(String(200), nullable=False, index=True, comment="Nombre del pais")
    iso_code_2 = Column(String(2), unique=True, nullable=False, index=True, comment="Codigo ISO 3166-1 alpha-2 (ej: US, MX, CO)")
    iso_code_3 = Column(String(3), unique=True, nullable=False, index=True, comment="Codigo ISO 3166-1 alpha-3 (ej: USA, MEX, COL)")
    numeric_code = Column(String(3), nullable=True, comment="Codigo numerico ISO 3166-1 (ej: 840, 484, 170)")

    # Informacion adicional
    phone_code = Column(String(10), nullable=True, comment="Codigo telefonico internacional (ej: +1, +52, +57)")
    currency_code = Column(String(3), nullable=True, comment="Codigo de moneda ISO 4217 (ej: USD, MXN, COP)")
    currency_name = Column(String(50), nullable=True, comment="Nombre de la moneda")

    # Campos de auditoria
    is_active = Column(Boolean, default=True, nullable=False, comment="Indica si el pais esta activo")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="Borrado logico")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Fecha de creacion")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Fecha de ultima actualizacion")

    # Relaciones
    states = relationship("State", back_populates="country", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="country")

    def __repr__(self):
        return f"<Country(id={self.id}, name={self.name}, iso={self.iso_code_2})>"

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "iso_code_2": self.iso_code_2,
            "iso_code_3": self.iso_code_3,
            "numeric_code": self.numeric_code,
            "phone_code": self.phone_code,
            "currency_code": self.currency_code,
            "currency_name": self.currency_name,
            "is_active": self.is_active,
        }