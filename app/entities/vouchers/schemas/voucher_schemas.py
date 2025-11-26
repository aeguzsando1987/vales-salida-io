"""
Schemas Pydantic para Voucher

Validación de entrada/salida para vales de entrada y salida.
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator

from app.entities.vouchers.models.voucher import VoucherTypeEnum, VoucherStatusEnum


# ==================== SCHEMAS BASE ====================

class VoucherBase(BaseModel):
    """Schema base para Voucher"""
    voucher_type: VoucherTypeEnum = Field(..., description="ENTRY o EXIT")
    company_id: int = Field(..., gt=0, description="ID de la empresa")
    origin_branch_id: Optional[int] = Field(None, gt=0, description="ID sucursal origen")
    destination_branch_id: Optional[int] = Field(None, gt=0, description="ID sucursal destino")
    delivered_by_id: int = Field(..., gt=0, description="ID de quien entrega")
    with_return: bool = Field(False, description="¿Requiere retorno?")
    estimated_return_date: Optional[date] = Field(None, description="Fecha estimada de retorno")
    notes: Optional[str] = Field(None, max_length=2000, description="Observaciones")
    internal_notes: Optional[str] = Field(None, max_length=2000, description="Notas internas")


class VoucherCreate(VoucherBase):
    """
    Schema para crear un voucher

    El folio se genera automáticamente.
    Estado inicial: PENDING
    """
    pass

    @field_validator('estimated_return_date')
    @classmethod
    def validate_return_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validar que la fecha de retorno sea futura si se especifica"""
        if v and v < date.today():
            raise ValueError('La fecha de retorno debe ser futura')
        return v


class VoucherUpdate(BaseModel):
    """
    Schema para actualizar un voucher

    Todos los campos son opcionales.
    """
    origin_branch_id: Optional[int] = Field(None, gt=0)
    destination_branch_id: Optional[int] = Field(None, gt=0)
    with_return: Optional[bool] = None
    estimated_return_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)


class VoucherApprove(BaseModel):
    """Schema para aprobar un voucher"""
    approved_by_id: int = Field(..., gt=0, description="ID de quien aprueba")
    notes: Optional[str] = Field(None, max_length=500, description="Observaciones de aprobación")


class VoucherCancel(BaseModel):
    """Schema para cancelar un voucher"""
    cancellation_reason: str = Field(..., min_length=10, max_length=500,
                                     description="Motivo de cancelación")


# ==================== SCHEMAS DE RESPUESTA ====================

class VoucherResponse(BaseModel):
    """Schema de respuesta completo"""
    id: int
    folio: str
    voucher_type: VoucherTypeEnum
    status: VoucherStatusEnum

    # Relaciones
    company_id: int
    origin_branch_id: Optional[int]
    destination_branch_id: Optional[int]

    # Firmas digitales
    approved_by_id: Optional[int]
    delivered_by_id: int
    received_by_id: Optional[int]

    # Control
    with_return: bool
    estimated_return_date: Optional[date]
    actual_return_date: Optional[date]

    # Info adicional
    notes: Optional[str]
    internal_notes: Optional[str]
    qr_token: Optional[str]

    # Auditoría
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]

    model_config = {
        "from_attributes": True
    }


class VoucherDetailedResponse(VoucherResponse):
    """
    Schema de respuesta con información expandida (nombres)

    Para mostrar en detalle con nombres de las relaciones.
    """
    company_name: Optional[str] = None
    origin_branch_name: Optional[str] = None
    destination_branch_name: Optional[str] = None

    # Nombres de firmas digitales
    approved_by_name: Optional[str] = None
    delivered_by_name: Optional[str] = None
    received_by_name: Optional[str] = None

    creator_name: Optional[str] = None


class VoucherWithDetailsResponse(VoucherDetailedResponse):
    """
    Schema de respuesta con líneas de detalle incluidas.

    Usado cuando include_details=true en GET /vouchers/{id}
    Incluye información completa del voucher + todas las líneas de detalle.
    """
    details: List['VoucherDetailWithProduct'] = []

    model_config = {
        "from_attributes": True
    }


class VoucherListResponse(BaseModel):
    """Schema para lista paginada de vouchers"""
    vouchers: List[VoucherResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class VoucherSearchResponse(BaseModel):
    """Schema simplificado para búsqueda/autocomplete"""
    id: int
    folio: str
    voucher_type: VoucherTypeEnum
    status: VoucherStatusEnum
    company_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class VoucherStatistics(BaseModel):
    """Estadísticas de vouchers"""
    total_vouchers: int
    by_status: dict
    by_type: dict
    pending_approval: int
    overdue: int
    in_transit: int


# Resolver forward references después de que todos los modelos estén definidos
# Este import se coloca al final para evitar importes circulares
try:
    from app.entities.voucher_details.schemas.voucher_detail_schemas import VoucherDetailWithProduct
    # Reconstruir el modelo para resolver la referencia forward 'VoucherDetailWithProduct'
    VoucherWithDetailsResponse.model_rebuild()
except ImportError:
    # Si voucher_details aún no está implementado, continuar sin error
    pass
