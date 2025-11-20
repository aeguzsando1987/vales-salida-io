"""
Modelo SQLAlchemy para la entidad Branch (Sucursal/Ubicación).

Representa ubicaciones genéricas donde se puede enviar o recibir material:
- Almacenes
- Proyectos/Obras
- Plantas
- Oficinas

Autor: E. Guzman
Fecha: 2025-11-12
"""

# ==================== IMPORTS ====================
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# ==================== CLASE ====================
class Branch(Base):
    """
    Modelo de Sucursal/Ubicación

    Representa ubicaciones físicas donde se puede enviar o recibir material.
    Puede ser un almacén, proyecto, obra, planta u oficina.
    """
    __tablename__ = "branches"

    # ==================== CAMPOS PRINCIPALES ====================

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Identificación de la sucursal
    branch_code = Column(String(50), nullable=False, unique=True, index=True,
                        comment="Código único de la sucursal (ej: ALM-01, PROY-CDMX)")
    branch_name = Column(String(200), nullable=False, index=True,
                        comment="Nombre de la sucursal/ubicación")
    branch_type = Column(String(50), nullable=False, index=True,
                        comment="Tipo: warehouse, project, plant, office, site")

    # Descripción opcional
    description = Column(Text, nullable=True,
                        comment="Descripción detallada de la ubicación")

    # Relación con empresa (una sucursal pertenece a una empresa)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"),
                       nullable=False, index=True,
                       comment="Empresa a la que pertenece esta sucursal")

    # Ubicación geográfica
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="RESTRICT"),
                       nullable=False, index=True,
                       comment="País según ISO-3166")
    state_id = Column(Integer, ForeignKey("states.id", ondelete="RESTRICT"),
                     nullable=True, index=True,
                     comment="Estado/Provincia/Departamento")
    city = Column(String(100), nullable=True,
                 comment="Ciudad")
    address = Column(String(255), nullable=True,
                    comment="Dirección física")
    postal_code = Column(String(10), nullable=True,
                        comment="Código postal")

    # Información de contacto
    phone = Column(String(20), nullable=True,
                  comment="Teléfono de contacto")
    email = Column(String(150), nullable=True,
                  comment="Correo de contacto")

    # Responsable de la sucursal (opcional)
    manager_id = Column(Integer, ForeignKey("individuals.id", ondelete="SET NULL"),
                       nullable=True, index=True,
                       comment="Responsable/Gerente de la sucursal")

    # Coordenadas GPS (opcional - útil para mapas)
    latitude = Column(String(20), nullable=True,
                     comment="Latitud GPS")
    longitude = Column(String(20), nullable=True,
                      comment="Longitud GPS")

    # Estado operativo
    operational_status = Column(String(20), nullable=False, default="active", index=True,
                               comment="Estado operativo: active, inactive, maintenance, closed")

    # ==================== CAMPOS DE AUDITORÍA ====================

    is_active = Column(Boolean, default=True, nullable=False, index=True,
                      comment="Indica si el registro está activo")
    is_deleted = Column(Boolean, default=False, nullable=False, index=True,
                       comment="Soft delete flag")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False,
                       comment="Fecha de creación del registro")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                       nullable=True,
                       comment="Usuario que creó el registro")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                       nullable=True,
                       comment="Fecha de última actualización")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                       nullable=True,
                       comment="Usuario que actualizó el registro")

    deleted_at = Column(DateTime, nullable=True,
                       comment="Fecha de eliminación (soft delete)")
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                       nullable=True,
                       comment="Usuario que eliminó el registro")

    # ==================== RELACIONES ====================

    # Relación con Company
    company = relationship("Company", foreign_keys=[company_id], back_populates="branches")

    # Relaciones geográficas
    country = relationship("Country", foreign_keys=[country_id])
    state = relationship("State", foreign_keys=[state_id])

    # Relación con responsable
    manager = relationship("Individual", foreign_keys=[manager_id])

    # Relaciones de auditoría
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Relaciones inversas (se definirán cuando se creen las entidades)
    # vouchers = relationship("Voucher", back_populates="branch")

    # ==================== MÉTODOS ====================

    def __repr__(self):
        return f"<Branch(id={self.id}, code='{self.branch_code}', name='{self.branch_name}')>"

    def __str__(self):
        return f"{self.branch_code} - {self.branch_name}"
