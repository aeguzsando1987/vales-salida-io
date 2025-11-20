"""
Product Pydantic Schemas
Validación y serialización de datos de productos
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class ProductCategoryEnum(str, Enum):
    """Categorías de productos"""
    TOOL = "TOOL"
    MACHINE = "MACHINE"
    COMPUTER_EQUIPMENT = "COMPUTER_EQUIPMENT"
    FINISHED_PRODUCT = "FINISHED_PRODUCT"
    RAW_MATERIAL = "RAW_MATERIAL"
    SPARE_PART = "SPARE_PART"
    CONSUMABLE = "CONSUMABLE"
    OTHER = "OTHER"


class ProductBase(BaseModel):
    """Schema base de Product"""
    code: Optional[str] = Field(None, max_length=100, description="Código único del producto")
    name: str = Field(..., min_length=2, max_length=300, description="Nombre del producto")
    description: Optional[str] = Field(None, description="Descripción detallada")
    part_number: Optional[str] = Field(None, max_length=100, description="Número de parte")
    category: Optional[ProductCategoryEnum] = Field(
        ProductCategoryEnum.OTHER,
        description="Categoría del producto"
    )
    unit_of_measure: str = Field(
        "PZA",
        max_length=20,
        description="Unidad de medida (PZA, KG, LT, M, etc.)"
    )
    is_serialized: bool = Field(
        False,
        description="¿Requiere número de serie?"
    )

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Valida que el nombre no sea solo espacios"""
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

    @field_validator('code')
    @classmethod
    def code_must_be_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza código a mayúsculas"""
        if v:
            return v.strip().upper()
        return v

    @field_validator('unit_of_measure')
    @classmethod
    def unit_must_be_uppercase(cls, v: str) -> str:
        """Normaliza unidad de medida a mayúsculas"""
        return v.strip().upper()


class ProductCreate(ProductBase):
    """Schema para crear Product"""
    pass


class ProductUpdate(BaseModel):
    """Schema para actualizar Product (todos los campos opcionales)"""
    code: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    description: Optional[str] = None
    part_number: Optional[str] = Field(None, max_length=100)
    category: Optional[ProductCategoryEnum] = None
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    is_serialized: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el nombre no sea solo espacios"""
        if v is not None:
            if not v.strip():
                raise ValueError('El nombre no puede estar vacío')
            return v.strip()
        return v

    @field_validator('code')
    @classmethod
    def code_must_be_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza código a mayúsculas"""
        if v:
            return v.strip().upper()
        return v

    @field_validator('unit_of_measure')
    @classmethod
    def unit_must_be_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza unidad de medida a mayúsculas"""
        if v:
            return v.strip().upper()
        return v


class ProductResponse(ProductBase):
    """Schema de respuesta de Product"""
    id: int
    usage_count: int = Field(..., description="Número de veces usado en vales")
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema para lista de productos"""
    products: list[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ProductSearchResponse(BaseModel):
    """Schema para búsqueda de productos (autocomplete)"""
    id: int
    name: str
    code: Optional[str] = None
    unit_of_measure: str
    usage_count: int

    class Config:
        from_attributes = True
