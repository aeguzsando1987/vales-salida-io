"""
EntryLog Model - Registro de Entradas Físicas de Material

PROPÓSITO:
Este modelo NO es una entidad CRUD completa. Es un registro de auditoría automático
que se crea cuando se confirma la recepción física de material en un vale.

FLUJOS:
- Salida con retorno: Al regresar material → gerente/supervisor registra entry_log
- Solo entrada: Al entregar material → gerente/supervisor registra entry_log
- Intercompañía: Al llegar a sucursal destino → gerente/supervisor registra entry_log

REGLAS:
- Solo UN entry_log por voucher (UNIQUE constraint)
- Si entry_status = COMPLETE → voucher.status = CLOSED
- Si entry_status = INCOMPLETE/DAMAGED → voucher.status = OVERDUE
- Si INCOMPLETE/DAMAGED, missing_items_description es OBLIGATORIO
"""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from database import Base


class EntryStatusEnum(str, Enum):
    """Estados de recepción de material"""
    COMPLETE = "COMPLETE"           # Todo llegó completo y en buen estado
    INCOMPLETE = "INCOMPLETE"       # Faltaron artículos (parcial)
    DAMAGED = "DAMAGED"             # Artículos llegaron dañados


class EntryLog(Base):
    """
    Registro de entrada física de material.

    Representa la "firma digital" de recepción por parte de gerente/supervisor.
    Se crea automáticamente al confirmar entrada vía endpoint /vouchers/{id}/confirm-entry
    """
    __tablename__ = "entry_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    voucher_id = Column(
        Integer,
        ForeignKey("vouchers.id", ondelete="RESTRICT"),
        unique=True,  # Solo un entry_log por voucher
        nullable=False,
        index=True
    )

    # Datos de recepción
    entry_status = Column(SQLEnum(EntryStatusEnum), nullable=False)

    # Firma digital: quién recibió el material
    received_by_id = Column(
        Integer,
        ForeignKey("individuals.id"),
        nullable=False,
        comment="Individual que recibe el material (gerente/supervisor)"
    )

    # Detalles opcionales
    missing_items_description = Column(
        Text,
        nullable=True,
        comment="Obligatorio si entry_status = INCOMPLETE o DAMAGED"
    )

    notes = Column(Text, nullable=True, comment="Observaciones adicionales")

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="Usuario que registró la entrada"
    )

    # Relationships
    voucher = relationship("Voucher", back_populates="entry_log")
    received_by = relationship("Individual", foreign_keys=[received_by_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<EntryLog(id={self.id}, voucher_id={self.voucher_id}, status={self.entry_status})>"
