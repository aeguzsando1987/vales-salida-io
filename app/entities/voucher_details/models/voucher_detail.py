"""
VoucherDetail Model
Representa las líneas de detalle (artículos) de un vale.
Máximo 20 líneas por vale.
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class VoucherDetail(Base):
    """
    Modelo de Detalle de Vale (Líneas de Artículos)

    Representa cada artículo/producto en un vale.
    Máximo 20 líneas por vale (validado en múltiples capas).
    Relación opcional con Products (cache).
    """
    __tablename__ = "voucher_details"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    voucher_id = Column(
        Integer,
        ForeignKey("vouchers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,  # Opcional: puede ser item libre
        index=True
    )

    # Line Information
    line_number = Column(
        Integer,
        nullable=False,
        index=True
    )

    # Item Details (SIEMPRE obligatorios, incluso si hay product_id)
    item_name = Column(String(300), nullable=False, index=True)
    item_description = Column(Text, nullable=True)

    # Quantity and Measures
    quantity = Column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    unit_of_measure = Column(String(20), nullable=False, default='PZA')

    # Optional Fields
    serial_number = Column(String(100), nullable=True)
    part_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Audit fields (Foreign Keys to users)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    voucher = relationship("Voucher", back_populates="details")
    product = relationship("Product", lazy="joined")  # Cache opcional

    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    updater = relationship("User", foreign_keys=[updated_by], lazy="joined")
    deleter = relationship("User", foreign_keys=[deleted_by], lazy="joined")

    # Constraints
    __table_args__ = (
        # Line number debe estar entre 1 y 20
        CheckConstraint('line_number >= 1 AND line_number <= 20', name='chk_line_number_range'),

        # Quantity debe ser positiva
        CheckConstraint('quantity > 0', name='chk_positive_quantity'),

        # Unique constraint: un solo line_number por voucher
        Index('idx_voucher_line_unique', 'voucher_id', 'line_number', unique=True),

        # Indexes compuestos
        Index('idx_voucher_detail_active_deleted', 'is_active', 'is_deleted'),
        Index('idx_voucher_detail_voucher_line', 'voucher_id', 'line_number'),
    )

    def __repr__(self):
        return f"<VoucherDetail(id={self.id}, voucher_id={self.voucher_id}, line={self.line_number}, item='{self.item_name}', qty={self.quantity})>"
