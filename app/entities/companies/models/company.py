"""
Modelo SQLAlchemy para la entidad Company (o Empresa en español).

Representa empresas/compañías con información fiscal, ubicación geográfica y datos de contacto.

Esta es una entridad base de la plantilla.
"""

# ==================== IMPORTS ====================
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# ==================== CLASE ====================
class Company(Base):
    """
    Modelo de Empresa/Compañía

    Almacena información de empresas incluyendo datos fiscales,
    ubicación geográfica y datos de contacto.
    """
    __tablename__ = "companies" # Nombre que la entidad tendra como tabla en la base de datos

    # ==================== CAMPOS PRINCIPALES ====================

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Información de la empresa
    company_name = Column(String(200), nullable=False, index=True,
                         comment="Nombre comercial o razón social")
    legal_name = Column(String(200), nullable=True,
                       comment="Nombre legal completo si difiere del comercial")

    # Información fiscal (de TAX ID NUMBER que es un termino genérico)
    tin = Column(String(30), nullable=False, unique=True, index=True,
                comment="Tax Identification Number (RFC, EIN, NIF, CUIT, etc.)")
    tax_system = Column(String(10), nullable=False,
                       comment="Tipo de sistema fiscal: RFC, EIN, NIF, CUIT, etc.")

    # Ubicación geográfica de pais (relacionada con la entidad Country)
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="RESTRICT"),
                       nullable=False, index=True,
                       comment="País según ISO-3166")
    # Ubicación geográfica de estado (relacionada con la entidad State)
    state_id = Column(Integer, ForeignKey("states.id", ondelete="RESTRICT"),
                     nullable=True, index=True,
                     comment="Estado/Provincia/Departamento")
    # Ubicación geográfica de ciudad (sin relacion con alguna entidad)
    city = Column(String(100), nullable=True,
                 comment="Ciudad")
    # Ubicación geográfica de domicilio fiscal o principal (sin relacion con alguna entidad)
    address = Column(String(255), nullable=True,
                    comment="Domicilio fiscal o principal")
    # Ubicación geográfica de código postal (sin relacion con alguna entidad)
    postal_code = Column(String(10), nullable=True,
                        comment="Código postal")

    # Información de contacto
    phone = Column(String(20), nullable=True,
                  comment="Teléfono principal")
    email = Column(String(150), nullable=True, index=True,
                  comment="Correo de contacto o facturación")
    website = Column(String(150), nullable=True,
                    comment="Sitio web de la empresa")

    # Estado de la empresa de manera administrativa (no en sistema). Util para suscripciones
    status = Column(String(20), nullable=False, default="active", index=True,
                   comment="Estado: active, inactive, suspended, waiting")

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

    updated_at = Column(DateTime, default=datetime.utcnow,
                       onupdate=datetime.utcnow, nullable=True,
                       comment="Fecha de última actualización")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                       nullable=True,
                       comment="Usuario que realizó la última actualización")

    deleted_at = Column(DateTime, nullable=True,
                       comment="Fecha de eliminación (soft delete)")
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                       nullable=True,
                       comment="Usuario que eliminó el registro")

    # ==================== RELACIONES ====================

    # Relación con países
    country = relationship("Country", foreign_keys=[country_id],
                          back_populates="companies")

    # Relación con estados
    state = relationship("State", foreign_keys=[state_id],
                        back_populates="companies")

    # Relaciones de auditoría
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    def __repr__(self):
        return f"<Company(id={self.id}, company_name='{self.company_name}', tin='{self.tin}', status='{self.status}')>"
