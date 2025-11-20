"""
Product Model
Representa productos frecuentes para cache opcional (NO inventario)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class ProductCategoryEnum(str, enum.Enum):
    """Categorías de productos"""
    TOOL = "TOOL"
    MACHINE = "MACHINE"
    COMPUTER_EQUIPMENT = "COMPUTER_EQUIPMENT"
    FINISHED_PRODUCT = "FINISHED_PRODUCT"
    RAW_MATERIAL = "RAW_MATERIAL"
    SPARE_PART = "SPARE_PART"
    CONSUMABLE = "CONSUMABLE"
    OTHER = "OTHER"


class Product(Base):
    """
    Modelo de Producto

    Cache opcional de productos frecuentes para acelerar captura.
    NO es sistema de inventario.
    usage_count se incrementa automáticamente al usar en vales.
    """
    __tablename__ = "products"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Identification
    code = Column(String(100), unique=True, nullable=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=True)
    part_number = Column(String(100), nullable=True)

    # Classification
    category = Column(
        SQLEnum(ProductCategoryEnum),
        nullable=True,
        default=ProductCategoryEnum.OTHER
    )

    # Characteristics
    unit_of_measure = Column(String(20), nullable=False, default='PZA')
    is_serialized = Column(Boolean, nullable=False, default=False)

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0, index=True)

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
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    updater = relationship("User", foreign_keys=[updated_by], lazy="joined")
    deleter = relationship("User", foreign_keys=[deleted_by], lazy="joined")

    # Indexes (ya definidos arriba con index=True, pero podemos agregar compuestos)
    __table_args__ = (
        Index('idx_product_active_deleted', 'is_active', 'is_deleted'),
        Index('idx_product_usage_desc', usage_count.desc()),
        Index('idx_product_name_search', 'name'),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', code='{self.code}', usage_count={self.usage_count})>"
