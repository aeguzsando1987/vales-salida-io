"""
Modelo de Voucher (Vale de Entrada/Salida)

Entidad central del sistema que representa vales de entrada y salida de material.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base

# Imports para relationships (forward references)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entities.vouchers.models.entry_log import EntryLog, EntryStatusEnum
    from app.entities.vouchers.models.out_log import OutLog, ValidationStatusEnum
    from app.entities.voucher_details.models.voucher_detail import VoucherDetail


class VoucherTypeEnum(str, enum.Enum):
    """Tipo de vale"""
    ENTRY = "ENTRY"  # Vale de entrada
    EXIT = "EXIT"    # Vale de salida


class VoucherStatusEnum(str, enum.Enum):
    """Estados del voucher"""
    PENDING = "PENDING"                        # Recién creado, pendiente aprobación del jefe directo
    PENDING_IO_APPROVAL = "PENDING_IO_APPROVAL"  # 1ª aprobación dada; pendiente de contraloría (io manager)
    APPROVED = "APPROVED"                      # Doble aprobación completa (jefe directo + contraloría)
    IN_TRANSIT = "IN_TRANSIT"                  # Escaneado y en tránsito
    OVERDUE = "OVERDUE"                        # Vencido por tiempo (solo scheduler)
    INCOMPLETE_DAMAGED = "INCOMPLETE_DAMAGED"  # Entrada con faltantes/daños
    CLOSED = "CLOSED"                          # Proceso completado exitosamente
    CANCELLED = "CANCELLED"                    # Cancelado


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

    # Destino externo (cuando NO es intercompañía)
    outer_destination = Column(String(255), nullable=True,
                              comment="Destino en texto libre cuando NO es intercompañía")

    # ==================== SISTEMA DE FIRMAS DIGITALES ====================
    # Trazabilidad completa de responsables

    approved_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                           nullable=True, index=True,
                           comment="Jefe directo que dio la 1ª aprobación")

    # Segunda aprobación (contraloría / io manager)
    io_approved_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                              nullable=True, index=True,
                              comment="Contralor (io manager) que dio la 2ª aprobación")

    delivered_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                            nullable=False, index=True,
                            comment="Responsable de entregar el material")

    received_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                           nullable=True, index=True,
                           comment="Responsable que recibió el material")

    # ==================== INFORMACIÓN DE CONTROL ====================

    with_return = Column(Boolean, nullable=False, default=False,
                        comment="¿Requiere retorno del material?")

    is_intercompany = Column(Boolean, nullable=False, default=False,
                            comment="¿Es transferencia entre empresas? (requiere entry_log)")

    estimated_return_date = Column(Date, nullable=True,
                                  comment="Fecha estimada de retorno")

    actual_return_date = Column(Date, nullable=True,
                               comment="Fecha real de retorno")

    # Timestamps del flujo de doble aprobación
    first_approved_at = Column(DateTime, nullable=True,
                              comment="Momento de la 1ª aprobación (jefe directo)")

    io_approved_at = Column(DateTime, nullable=True,
                           comment="Momento de la 2ª aprobación (contraloría)")

    # Trazabilidad de cancelación / rechazo
    cancelled_by_id = Column(Integer, ForeignKey("individuals.id", ondelete="RESTRICT"),
                            nullable=True, index=True,
                            comment="Individual que canceló/rechazó el vale")

    cancelled_at = Column(DateTime, nullable=True,
                         comment="Momento de la cancelación/rechazo")

    cancelled_from_status = Column(String(30), nullable=True,
                                  comment="Estado previo a la cancelación (define la capacidad: "
                                          "PENDING=rechazo jefe directo, PENDING_IO_APPROVAL=rechazo "
                                          "contraloría, APPROVED=cancelación)")

    cancellation_reason = Column(Text, nullable=True,
                                comment="Razón de la cancelación/rechazo (columna dedicada)")

    # ==================== INFORMACIÓN ADICIONAL ====================

    notes = Column(Text, nullable=True,
                  comment="Observaciones y notas adicionales")

    internal_notes = Column(Text, nullable=True,
                           comment="Notas internas (no visibles en PDF)")

    # QR Token para validación (generado automáticamente)
    qr_token = Column(String(255), nullable=True, index=True,
                     comment="Token de seguridad para QR")

    # ==================== PDF Y QR TRACKING (Phase 4) ====================

    pdf_last_generated_at = Column(DateTime, nullable=True,
                                   comment="Timestamp de última generación de PDF")

    qr_image_last_generated_at = Column(DateTime, nullable=True,
                                       comment="Timestamp de última generación de imagen QR")

    # ==================== CAMPOS DE AUDITORÍA ====================

    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
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
    io_approved_by = relationship("Individual", foreign_keys=[io_approved_by_id])
    cancelled_by = relationship("Individual", foreign_keys=[cancelled_by_id])
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
