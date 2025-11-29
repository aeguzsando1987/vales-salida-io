"""
OutLog Model - Registro de Validación de Salida (QR Scanning)

PROPÓSITO:
Este modelo NO es una entidad CRUD completa. Es un registro de auditoría automático
que se crea cuando vigilancia valida la salida escaneando el QR del vale.

FLUJOS:
- Salida con retorno: vigilancia escanea QR → crea out_log(APPROVED) → voucher.status = IN_TRANSIT
- Salida sin retorno: vigilancia escanea QR → crea out_log(APPROVED) → voucher.status = CLOSED
- Intercompañía: vigilancia escanea QR → crea out_log(APPROVED) → voucher.status = IN_TRANSIT

REGLAS:
- Solo UN out_log por voucher (UNIQUE constraint)
- Solo se crea si voucher.status = APPROVED
- validation_status puede ser APPROVED, REJECTED, OBSERVATION
- El campo observations es opcional pero recomendado si validation_status != APPROVED
"""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from database import Base


class ValidationStatusEnum(str, Enum):
    """Estados de validación de salida"""
    APPROVED = "APPROVED"           # Validación exitosa, todo correcto
    REJECTED = "REJECTED"           # Rechazado por discrepancias
    OBSERVATION = "OBSERVATION"     # Aprobado con observaciones


class OutLog(Base):
    """
    Registro de validación de salida por vigilancia.

    Representa el escaneo del QR y la validación visual del material.
    Se crea automáticamente al validar salida vía endpoint /vouchers/{id}/validate-exit
    """
    __tablename__ = "out_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    voucher_id = Column(
        Integer,
        ForeignKey("vouchers.id", ondelete="RESTRICT"),
        unique=True,  # Solo un out_log por voucher
        nullable=False,
        index=True
    )

    # Datos de validación
    validation_status = Column(SQLEnum(ValidationStatusEnum), nullable=False)

    # Firma digital: quién validó la salida (vigilante)
    scanned_by_id = Column(
        Integer,
        ForeignKey("individuals.id"),
        nullable=False,
        comment="Individual que validó la salida (vigilante/checker)"
    )

    # Observaciones de inspección visual
    observations = Column(
        Text,
        nullable=True,
        comment="Notas de la inspección visual (recomendado si status != APPROVED)"
    )

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="Usuario que registró la validación"
    )

    # Relationships
    voucher = relationship("Voucher", back_populates="out_log")
    scanned_by = relationship("Individual", foreign_keys=[scanned_by_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<OutLog(id={self.id}, voucher_id={self.voucher_id}, status={self.validation_status})>"
