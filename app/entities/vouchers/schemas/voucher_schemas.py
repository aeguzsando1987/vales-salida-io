"""
Schemas Pydantic para Voucher

Validación de entrada/salida para vales de entrada y salida.
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, model_validator

from app.entities.vouchers.models.voucher import VoucherTypeEnum, VoucherStatusEnum
from app.entities.vouchers.models.entry_log import EntryStatusEnum
from app.entities.vouchers.models.out_log import ValidationStatusEnum


# ==================== SCHEMAS BASE ====================

class VoucherBase(BaseModel):
    """Schema base para Voucher"""
    voucher_type: VoucherTypeEnum = Field(..., description="ENTRY o EXIT")
    company_id: int = Field(..., gt=0, description="ID de la empresa")
    origin_branch_id: Optional[int] = Field(None, gt=0, description="ID sucursal origen")
    destination_branch_id: Optional[int] = Field(None, gt=0, description="ID sucursal destino")
    outer_destination: Optional[str] = Field(None, max_length=255, description="Destino externo cuando NO es intercompañía")
    delivered_by_id: int = Field(..., gt=0, description="ID de quien entrega")
    with_return: bool = Field(False, description="¿Requiere retorno?")
    is_intercompany: bool = Field(False, description="¿Es transferencia entre empresas?")
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
    outer_destination: Optional[str] = Field(None, max_length=255)
    with_return: Optional[bool] = None
    is_intercompany: Optional[bool] = None
    estimated_return_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)


class VoucherApprove(BaseModel):
    """
    Schema para aprobar un voucher.

    El campo approved_by_id es opcional. Si no se proporciona,
    el voucher se aprueba sin asignar un individual específico.
    """
    approved_by_id: Optional[int] = Field(None, gt=0,
                                          description="ID del individual que aprueba (opcional)")
    notes: Optional[str] = Field(None, max_length=500,
                                description="Observaciones de aprobación")


class VoucherCancel(BaseModel):
    """Schema para cancelar un voucher"""
    cancellation_reason: str = Field(..., min_length=10, max_length=500,
                                     description="Motivo de cancelación")


# ==================== SCHEMAS DE LOGS DE AUDITORÍA ====================

# -------- EntryLog Schemas --------

class EntryLogBase(BaseModel):
    """Schema base para EntryLog"""
    entry_status: EntryStatusEnum = Field(..., description="COMPLETE, INCOMPLETE o DAMAGED")
    received_by_id: Optional[int] = Field(None, gt=0, description="ID de quien recibe (opcional - se usa current_user si no se especifica)")
    missing_items_description: Optional[str] = Field(None, max_length=2000,
                                                     description="Requerido si INCOMPLETE/DAMAGED")
    notes: Optional[str] = Field(None, max_length=2000, description="Observaciones")


class EntryLogCreate(EntryLogBase):
    """
    Schema para crear un entry_log

    Se valida que missing_items_description sea obligatorio si entry_status != COMPLETE
    """

    @model_validator(mode='after')
    def validate_missing_items(self):
        """Si entry_status != COMPLETE, missing_items_description es obligatorio"""
        if self.entry_status in [EntryStatusEnum.INCOMPLETE, EntryStatusEnum.DAMAGED]:
            if not self.missing_items_description or len(self.missing_items_description.strip()) == 0:
                raise ValueError("missing_items_description es obligatorio cuando entry_status es INCOMPLETE o DAMAGED")
        return self


class EntryLogResponse(BaseModel):
    """Schema de respuesta para EntryLog"""
    id: int
    voucher_id: int
    entry_status: EntryStatusEnum
    received_by_id: int
    received_by_name: Optional[str] = None  # Nombre del individual
    missing_items_description: Optional[str]
    notes: Optional[str]
    created_at: datetime
    created_by: int
    creator_name: Optional[str] = None  # Nombre del usuario creador

    model_config = {
        "from_attributes": True
    }


# -------- OutLog Schemas --------

class OutLogBase(BaseModel):
    """Schema base para OutLog"""
    validation_status: ValidationStatusEnum = Field(..., description="APPROVED, REJECTED o OBSERVATION")
    scanned_by_id: int = Field(..., gt=0, description="ID de quien validó (vigilante)")
    observations: Optional[str] = Field(None, max_length=2000,
                                       description="Notas de inspección visual")


class OutLogCreate(OutLogBase):
    """Schema para crear un out_log"""
    pass


class OutLogResponse(BaseModel):
    """Schema de respuesta para OutLog"""
    id: int
    voucher_id: int
    validation_status: ValidationStatusEnum
    scanned_by_id: int
    scanned_by_name: Optional[str] = None  # Nombre del individual
    observations: Optional[str]
    created_at: datetime
    created_by: int
    creator_name: Optional[str] = None  # Nombre del usuario creador

    model_config = {
        "from_attributes": True
    }


# -------- Schemas para Validacion Linea por Linea --------

class LineValidation(BaseModel):
    """Schema para validacion de una linea individual"""
    detail_id: int = Field(..., gt=0, description="ID del voucher_detail")
    ok: bool = Field(..., description="Validacion visual (true=OK, false=problema)")
    notes: Optional[str] = Field(None, max_length=500, description="Observaciones si ok=false")


class ValidateExitRequest(BaseModel):
    """
    Schema para validar salida con validacion linea por linea

    Logica FLEXIBLE: Material SIEMPRE sale, incluso con observaciones
    """
    scanned_by_id: int = Field(..., gt=0, description="ID del vigilante que valida")
    line_validations: List[LineValidation] = Field(..., min_length=1, description="Validaciones por linea")
    general_observations: Optional[str] = Field(None, max_length=2000, description="Observaciones generales")


class ConfirmEntryRequest(BaseModel):
    """
    Schema para confirmar entrada con validacion linea por linea

    Logica ESTRICTA: Vale solo cierra si TODAS las lineas tienen ok=true
    """
    received_by_id: int = Field(..., gt=0, description="ID de quien recibe")
    line_validations: List[LineValidation] = Field(..., min_length=1, description="Validaciones por linea")
    general_observations: Optional[str] = Field(None, max_length=2000, description="Observaciones generales")


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
    outer_destination: Optional[str]

    # Firmas digitales
    approved_by_id: Optional[int]
    delivered_by_id: int
    received_by_id: Optional[int]

    # Control
    with_return: bool
    is_intercompany: bool
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
    Incluye logs de auditoría si existen.
    """
    company_name: Optional[str] = None
    origin_branch_name: Optional[str] = None
    destination_branch_name: Optional[str] = None

    # Nombres de firmas digitales
    approved_by_name: Optional[str] = None
    delivered_by_name: Optional[str] = None
    received_by_name: Optional[str] = None

    creator_name: Optional[str] = None

    # Logs de auditoría (uno a uno)
    entry_log: Optional[EntryLogResponse] = None
    out_log: Optional[OutLogResponse] = None


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


# ==================== SCHEMAS PARA PDF/QR (Phase 4) ====================

class TaskInitiatedResponse(BaseModel):
    """
    Schema de respuesta cuando se inicia una tarea asíncrona de Celery

    Usado cuando se solicita generar PDF o QR.
    """
    task_id: str = Field(..., description="ID de la tarea de Celery")
    status: str = Field(..., description="Estado inicial (siempre PENDING)")
    message: str = Field(..., description="Mensaje descriptivo de la operación")
    voucher_folio: Optional[str] = Field(None, description="Folio del voucher")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "PENDING",
                "message": "Generación de PDF iniciada para voucher ACM-SAL-2025-0001",
                "voucher_folio": "ACM-SAL-2025-0001"
            }
        }
    }


class TaskStatusResponse(BaseModel):
    """
    Schema de respuesta para consultar el estado de una tarea de Celery

    Estados posibles:
    - PENDING: En cola o ejecutándose
    - SUCCESS: Completada exitosamente
    - FAILURE: Falló durante la ejecución
    - RETRY: Reintentando después de un error
    """
    task_id: str = Field(..., description="ID de la tarea")
    status: str = Field(..., description="PENDING, SUCCESS, FAILURE, RETRY")
    message: str = Field(..., description="Descripción del estado actual")
    result: Optional[dict] = Field(None, description="Resultado si SUCCESS (ruta del archivo, etc)")
    error: Optional[str] = Field(None, description="Mensaje de error si FAILURE")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "SUCCESS",
                "message": "Tarea completada exitosamente",
                "result": {
                    "pdf_path": "temp_files/pdfs/voucher_1_20251129_143022.pdf",
                    "file_size": 245678,
                    "generated_at": "2025-11-29T14:30:22"
                }
            }
        }
    }


class VoucherWithGenerationInfo(VoucherResponse):
    """
    Schema de respuesta extendido con información de generación de PDF/QR

    Incluye timestamps de última generación para tracking.
    """
    pdf_last_generated_at: Optional[datetime] = Field(None, description="Última generación de PDF")
    qr_image_last_generated_at: Optional[datetime] = Field(None, description="Última generación de imagen QR")

    # Flags calculados (no están en BD)
    pdf_available: bool = Field(default=False, description="¿PDF generado al menos una vez?")
    qr_available: bool = Field(default=False, description="¿QR generado al menos una vez?")
    qr_token_expired: bool = Field(default=False, description="¿Token QR expirado? (>24h)")

    model_config = {
        "from_attributes": True
    }


class PDFDownloadMetadata(BaseModel):
    """
    Metadata sobre un archivo PDF generado

    Usado para respuestas de endpoints que devuelven información del PDF
    sin devolver el archivo directamente.
    """
    voucher_id: int = Field(..., description="ID del voucher")
    voucher_folio: str = Field(..., description="Folio del voucher")
    file_path: str = Field(..., description="Ruta del archivo PDF generado")
    file_size_bytes: int = Field(..., gt=0, description="Tamaño del archivo en bytes")
    generated_at: datetime = Field(..., description="Timestamp de generación")
    expires_at: Optional[datetime] = Field(None, description="Timestamp de expiración (si es temporal)")
    download_url: Optional[str] = Field(None, description="URL de descarga si está disponible")

    model_config = {
        "json_schema_extra": {
            "example": {
                "voucher_id": 1,
                "voucher_folio": "ACM-SAL-2025-0001",
                "file_path": "temp_files/pdfs/voucher_1_20251129_143022.pdf",
                "file_size_bytes": 245678,
                "generated_at": "2025-11-29T14:30:22",
                "expires_at": "2025-11-29T15:30:22",
                "download_url": "/api/vouchers/1/download-pdf"
            }
        }
    }


# Resolver forward references después de que todos los modelos estén definidos
# Este import se coloca al final para evitar importes circulares
try:
    from app.entities.voucher_details.schemas.voucher_detail_schemas import VoucherDetailWithProduct
    # Reconstruir el modelo para resolver la referencia forward 'VoucherDetailWithProduct'
    VoucherWithDetailsResponse.model_rebuild()
except ImportError:
    # Si voucher_details aún no está implementado, continuar sin error
    pass
