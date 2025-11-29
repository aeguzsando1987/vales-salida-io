"""
Modelo de Voucher (Vale de Entrada/Salida)

Entidad central del sistema que representa vales de entrada y salida de material.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base

# Imports para logs de auditoría (forward references)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entities.vouchers.models.entry_log import EntryLog, EntryStatusEnum
    from app.entities.vouchers.models.out_log import OutLog, ValidationStatusEnum


class VoucherTypeEnum(str, enum.Enum):
    """Tipo de vale"""
    ENTRY = "ENTRY"  # Vale de entrada
    EXIT = "EXIT"    # Vale de salida


class VoucherStatusEnum(str, enum.Enum):
    """Estados del voucher"""
    PENDING = "PENDING"        # Recién creado, pendiente aprobación
    APPROVED = "APPROVED"      # Aprobado por gerente/supervisor
    IN_TRANSIT = "IN_TRANSIT"  # Escaneado y en tránsito
    OVERDUE = "OVERDUE"        # Vencido o entrada incompleta
    CLOSED = "CLOSED"          # Proceso completado
    CANCELLED = "CANCELLED"    # Cancelado


class Voucher(Base):
    """
    Modelo de Vale de Entrada/Salida

    Representa un vale que puede ser de entrada (ENTRY) o salida (EXIT) de material.
    Incluye sistema de firmas digitales, tracking de estados y generación de folios.
    """
    __tablename__ = "vouchers"

    # ==================== CAMPOS PRINCIPALES ====================

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Identificación del vale
    folio = Column(String(50), unique=True, nullable=False, index=True,
                   comment="Folio único: {company_code}-{type}-{year}-{seq}")

    voucher_type = Column(SQLEnum(VoucherTypeEnum), nullable=False, index=True,
                         comment="ENTRY o EXIT")

    status = Column(SQLEnum(VoucherStatusEnum), nullable=False,
                   default=VoucherStatusEnum.PENDING, index=True,
                   comment="Estado actual del voucher")

    # ==================== RELACIONES CON OTRAS ENTIDADES ====================

    # Empresa a la que pertenece el vale
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"),
                       nullable=False, index=True,
                       comment="Empresa dueña del vale")

    # Sucursales (origen y destino)
    origin_branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"),
                             nullable=True, index=True,
                             comment="Sucursal de origen (opcional)")

    destination_branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"),
                                  nullable=True, index=True,
                                  comment="Sucursal de destino (opcional)")

    # ==================== SISTEMA DE FIRMAS DIGITALES ====================
    # Trazabilidad completa de responsables

    approved_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                           nullable=True, index=True,
                           comment="Gerente/Supervisor que aprobó")

    delivered_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                            nullable=False, index=True,
                            comment="Responsable de entregar el material")

    received_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                           nullable=True, index=True,
                           comment="Responsable que recibió el material")

    # ==================== INFORMACIÓN DE CONTROL ====================

    with_return = Column(Boolean, nullable=False, default=False,
                        comment="¿Requiere retorno del material?")

    estimated_return_date = Column(Date, nullable=True,
                                  comment="Fecha estimada de retorno")

    actual_return_date = Column(Date, nullable=True,
                               comment="Fecha real de retorno")

    # ==================== INFORMACIÓN ADICIONAL ====================

    notes = Column(Text, nullable=True,
                  comment="Observaciones y notas adicionales")

    internal_notes = Column(Text, nullable=True,
                           comment="Notas internas (no visibles en PDF)")

    # QR Token para validación (generado automáticamente)
    qr_token = Column(String(255), nullable=True, index=True,
                     comment="Token de seguridad para QR")

    # ==================== CAMPOS DE AUDITORÍA ====================

    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ==================== RELATIONSHIPS ====================

    company = relationship("Company", foreign_keys=[company_id])
    origin_branch = relationship("Branch", foreign_keys=[origin_branch_id])
    destination_branch = relationship("Branch", foreign_keys=[destination_branch_id])

    # Firmas digitales
    approved_by = relationship("Individual", foreign_keys=[approved_by_id])
    delivered_by = relationship("Individual", foreign_keys=[delivered_by_id])
    received_by = relationship("Individual", foreign_keys=[received_by_id])

    # Auditoría
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Relación con detalles (líneas del vale)
    details = relationship("VoucherDetail", back_populates="voucher",
                          cascade="all, delete-orphan")

    # Relationships a logs de auditoría (uno a uno)
    entry_log = relationship(
        "EntryLog",
        back_populates="voucher",
        uselist=False,  # Uno a uno
        cascade="all, delete-orphan"
    )

    out_log = relationship(
        "OutLog",
        back_populates="voucher",
        uselist=False,  # Uno a uno
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Voucher(folio='{self.folio}', type='{self.voucher_type}', status='{self.status}')>"
