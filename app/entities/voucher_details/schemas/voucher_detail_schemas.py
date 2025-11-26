"""
VoucherDetail Pydantic Schemas
Validación de entrada/salida con Pydantic v2
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ==================== BASE SCHEMAS ====================

class VoucherDetailBase(BaseModel):
    """Schema base con campos comunes"""
    line_number: int = Field(..., ge=1, le=20, description="Número de línea (1-20)")
    item_name: str = Field(..., min_length=1, max_length=300, description="Nombre del artículo")
    item_description: Optional[str] = Field(None, description="Descripción del artículo")
    quantity: Decimal = Field(..., gt=0, description="Cantidad (debe ser mayor a 0)")
    unit_of_measure: str = Field(default="PZA", max_length=20, description="Unidad de medida")
    serial_number: Optional[str] = Field(None, max_length=100, description="Número de serie")
    part_number: Optional[str] = Field(None, max_length=100, description="Número de parte")
    notes: Optional[str] = Field(None, description="Notas adicionales")


# ==================== CREATE SCHEMA ====================

class VoucherDetailCreate(VoucherDetailBase):
    """
    Schema para crear detalle de vale.

    Flujo inteligente:
    1. Si product_id se proporciona → usar ese producto
    2. Si no, buscar por item_name (similitud)
    3. Si encuentra matches → devolver para selección
    4. Si no encuentra → auto-crear producto en cache
    """
    voucher_id: int = Field(..., description="ID del vale")
    product_id: Optional[int] = Field(None, description="ID del producto (opcional, si ya seleccionó)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Ejemplo 1: Crear línea con auto-cache (producto nuevo)",
                    "description": "Sistema buscará productos similares. Si no encuentra, auto-creará en cache.",
                    "value": {
                        "voucher_id": 1,
                        "line_number": 1,
                        "item_name": "Martillo de acero 500g",
                        "item_description": "Martillo de bola con mango de madera",
                        "quantity": 2,
                        "unit_of_measure": "PZA",
                        "notes": "Para obra en construcción"
                    }
                },
                {
                    "title": "Ejemplo 2: Crear con producto existente (seleccionado)",
                    "description": "Usar cuando usuario ya seleccionó producto de lista de similitudes",
                    "value": {
                        "voucher_id": 1,
                        "line_number": 2,
                        "product_id": 5,
                        "item_name": "Taladro Bosch 750W",
                        "quantity": 1,
                        "unit_of_measure": "PZA",
                        "serial_number": "SN-TB-2024-001"
                    }
                },
                {
                    "title": "Ejemplo 3: Material consumible",
                    "description": "Ejemplo de material consumible sin número de serie",
                    "value": {
                        "voucher_id": 1,
                        "line_number": 3,
                        "item_name": "Cable eléctrico calibre 12",
                        "quantity": 50,
                        "unit_of_measure": "MTS",
                        "notes": "Cable azul para instalación eléctrica"
                    }
                },
                {
                    "title": "Ejemplo 4: Equipo con número de parte",
                    "description": "Equipo electrónico con part_number y serial_number",
                    "value": {
                        "voucher_id": 1,
                        "line_number": 4,
                        "item_name": "Laptop HP Pavilion 15",
                        "item_description": "i5-12th Gen, 16GB RAM, 512GB SSD",
                        "quantity": 1,
                        "unit_of_measure": "PZA",
                        "part_number": "15-EH3000LA",
                        "serial_number": "5CD1234567",
                        "notes": "Para gerente de proyecto"
                    }
                },
                {
                    "title": "Ejemplo 5: Línea simple (mínimo)",
                    "description": "Campos mínimos requeridos",
                    "value": {
                        "voucher_id": 1,
                        "line_number": 5,
                        "item_name": "Casco de seguridad",
                        "quantity": 3,
                        "unit_of_measure": "PZA"
                    }
                }
            ]
        }
    )

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v

    @field_validator('item_name')
    @classmethod
    def validate_item_name(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre del artículo no puede estar vacío")
        return v.strip()


# ==================== UPDATE SCHEMA ====================

class VoucherDetailUpdate(BaseModel):
    """Schema para actualizar detalle (campos opcionales)"""
    line_number: Optional[int] = Field(None, ge=1, le=20, description="Número de línea")
    item_name: Optional[str] = Field(None, min_length=1, max_length=300)
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    serial_number: Optional[str] = Field(None, max_length=100)
    part_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    product_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Ejemplo 1: Actualizar cantidad",
                    "description": "Cambiar solo la cantidad de un artículo",
                    "value": {
                        "quantity": 5
                    }
                },
                {
                    "title": "Ejemplo 2: Agregar número de serie",
                    "description": "Agregar serial_number a artículo existente",
                    "value": {
                        "serial_number": "SN-2024-12345",
                        "notes": "Serial asignado al recibir artículo"
                    }
                },
                {
                    "title": "Ejemplo 3: Corrección de datos",
                    "description": "Corregir nombre y descripción",
                    "value": {
                        "item_name": "Martillo de acero 1kg (corregido)",
                        "item_description": "Martillo profesional con mango ergonómico"
                    }
                },
                {
                    "title": "Ejemplo 4: Cambiar unidad de medida",
                    "description": "Actualizar unidad y cantidad",
                    "value": {
                        "quantity": 100,
                        "unit_of_measure": "MTS"
                    }
                }
            ]
        }
    )


# ==================== RESPONSE SCHEMAS ====================

class VoucherDetailResponse(VoucherDetailBase):
    """Schema de respuesta básico"""
    id: int
    voucher_id: int
    product_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ProductMatchResponse(BaseModel):
    """Schema para producto encontrado en búsqueda por similitud"""
    id: int
    name: str
    code: Optional[str]
    category: Optional[str]
    unit_of_measure: str
    usage_count: int
    description: Optional[str]

    model_config = {"from_attributes": True}


class ProductMatchesFound(BaseModel):
    """
    Respuesta cuando se encuentran productos similares.
    Frontend debe mostrar lista para selección.
    """
    status: str = "matches_found"
    matches: List[ProductMatchResponse]
    message: str = "Se encontraron productos similares. Selecciona uno o crea nuevo."
    search_term: str


class VoucherDetailWithProduct(VoucherDetailResponse):
    """Schema con información del producto relacionado"""
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    product_category: Optional[str] = None
    auto_created: bool = Field(default=False, description="Indica si el producto fue auto-creado")

    model_config = {"from_attributes": True}


# ==================== BATCH OPERATIONS ====================

class VoucherDetailBatchCreate(BaseModel):
    """Schema para crear múltiples detalles de una vez"""
    voucher_id: int
    details: List[VoucherDetailCreate] = Field(..., max_length=20, description="Máximo 20 líneas")

    @field_validator('details')
    @classmethod
    def validate_max_lines(cls, v):
        if len(v) > 20:
            raise ValueError("Máximo 20 líneas por vale")
        if len(v) == 0:
            raise ValueError("Debe proporcionar al menos una línea")

        # Validar que line_numbers sean únicos
        line_numbers = [detail.line_number for detail in v]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError("Los números de línea deben ser únicos")

        return v


class VoucherDetailBatchResponse(BaseModel):
    """Respuesta de creación batch"""
    created_count: int
    details: List[VoucherDetailResponse]
    auto_created_products: List[ProductMatchResponse] = []
