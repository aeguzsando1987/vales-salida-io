"""
Router para la entidad Voucher.

Define todos los endpoints HTTP con documentación Swagger,
validación de permisos y manejo de responses.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from typing import Optional, Union
from datetime import date
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session

from database import get_db, User
from app.shared.dependencies import require_permission

from app.entities.vouchers.controllers.voucher_controller import VoucherController
from app.entities.vouchers.schemas.voucher_schemas import (
    VoucherCreate,
    VoucherUpdate,
    VoucherApprove,
    VoucherCancel,
    VoucherResponse,
    VoucherDetailedResponse,
    VoucherWithDetailsResponse,
    VoucherListResponse,
    VoucherSearchResponse,
    VoucherStatistics
)
from app.entities.vouchers.models.voucher import VoucherStatusEnum, VoucherTypeEnum


# ==================== ROUTER CONFIGURATION ====================

router = APIRouter(
    prefix="/vouchers",
    tags=["Vouchers"],
    responses={
        404: {"description": "Voucher no encontrado"},
        400: {"description": "Datos inválidos o transición de estado no permitida"},
        403: {"description": "Permisos insuficientes"}
    }
)


# ==================== CRUD ENDPOINTS ====================

@router.post(
    "/",
    response_model=VoucherResponse,
    status_code=201,
    summary="Crear voucher",
    description="Crea un nuevo voucher (ENTRY o EXIT) con folio y QR token auto-generados"
)
def create_voucher(
    voucher_data: VoucherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "create", min_level=3))
):
    """
    Crea un nuevo voucher.

    Estado inicial: PENDING
    Genera automáticamente:
    - Folio único: {company_code}-{type}-{year}-{seq}
    - Token QR para validación

    Validaciones:
    - Empresa existe
    - Sucursales existen (si se proporcionan)
    - delivered_by existe
    - Si with_return=True, estimated_return_date es requerido

    Permisos requeridos: vouchers:create (nivel 3+)
    """
    controller = VoucherController(db)
    return controller.create(voucher_data, current_user.id)


@router.get(
    "/{voucher_id}",
    response_model=Union[VoucherResponse, VoucherDetailedResponse, VoucherWithDetailsResponse],
    summary="Obtener voucher por ID",
    description="Retorna un voucher específico por su ID, opcionalmente con líneas de detalle"
)
def get_voucher(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    detailed: bool = Query(False, description="Incluir nombres de relaciones expandidos"),
    include_details: bool = Query(False, description="Incluir líneas de detalle del voucher"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "get", min_level=1))
):
    """
    Obtiene un voucher por ID.

    Parámetros:
    - voucher_id: ID del voucher
    - detailed: Si es True, incluye company_name, approved_by_name, etc.
    - include_details: Si es True, incluye todas las líneas de detalle (voucher_details)

    Combinaciones de respuesta:
    - detailed=False, include_details=False → VoucherResponse (básico)
    - detailed=True, include_details=False → VoucherDetailedResponse (con nombres)
    - include_details=True → VoucherWithDetailsResponse (con nombres y líneas de detalle)

    Permisos requeridos: vouchers:get (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.get_by_id(voucher_id, detailed, include_details)


@router.get(
    "/folio/{folio}",
    response_model=VoucherResponse,
    summary="Obtener voucher por folio",
    description="Busca un voucher por su folio único"
)
def get_voucher_by_folio(
    folio: str = Path(..., min_length=10, max_length=50, description="Folio del voucher"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "get", min_level=1))
):
    """
    Obtiene un voucher por folio.

    Parámetros:
    - folio: Folio del voucher (ej: GPA-SAL-2025-0001)

    Permisos requeridos: vouchers:get (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.get_by_folio(folio)


@router.put(
    "/{voucher_id}",
    response_model=VoucherResponse,
    summary="Actualizar voucher",
    description="Actualiza un voucher (solo permitido en estado PENDING)"
)
def update_voucher(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    voucher_data: VoucherUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "update", min_level=2))
):
    """
    Actualiza un voucher.

    Solo se permite actualizar vouchers en estado PENDING.

    Validaciones:
    - Voucher existe
    - Estado es PENDING
    - Referencias válidas (si se cambian)

    Permisos requeridos: vouchers:update (nivel 2+)
    """
    controller = VoucherController(db)
    return controller.update(voucher_id, voucher_data, current_user.id)


@router.get(
    "/",
    response_model=VoucherListResponse,
    summary="Listar vouchers",
    description="Lista todos los vouchers con paginación"
)
def list_vouchers(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros"),
    active_only: bool = Query(True, description="Solo registros activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "list", min_level=1))
):
    """
    Lista todos los vouchers con paginación.

    Parámetros:
    - skip: Registros a saltar
    - limit: Máximo de registros
    - active_only: Si es True, solo registros activos

    Permisos requeridos: vouchers:list (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.list_vouchers(skip, limit, active_only)


# ==================== STATE TRANSITION ENDPOINTS ====================

@router.post(
    "/{voucher_id}/approve",
    response_model=VoucherResponse,
    summary="Aprobar voucher",
    description="Transición: PENDING → APPROVED"
)
def approve_voucher(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    approve_data: VoucherApprove = Body(..., description="Datos de aprobación"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "approve", min_level=3))
):
    """
    Aprueba un voucher: PENDING → APPROVED

    Requerido para:
    - Vales EXIT antes de escanear QR
    - Vales ENTRY (opcional según flujo de negocio)

    Validaciones:
    - Estado actual es PENDING
    - approved_by existe

    Permisos requeridos: vouchers:approve (nivel 3+)
    """
    controller = VoucherController(db)
    return controller.approve(voucher_id, approve_data, current_user.id)


@router.post(
    "/{voucher_id}/start-transit",
    response_model=VoucherResponse,
    summary="Iniciar tránsito",
    description="Transición: APPROVED → IN_TRANSIT (solo EXIT con retorno)"
)
def start_transit(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "scan_qr", min_level=3))
):
    """
    Inicia tránsito: APPROVED → IN_TRANSIT

    Solo aplica para:
    - EXIT con retorno
    - EXIT intercompañía

    No aplica para:
    - EXIT sin retorno (va directo a CLOSED)

    Validaciones:
    - Estado actual es APPROVED
    - Voucher requiere tránsito (with_return=True)

    Permisos requeridos: vouchers:scan_qr (nivel 3+)
    """
    controller = VoucherController(db)
    return controller.start_transit(voucher_id, current_user.id)


@router.post(
    "/{voucher_id}/close",
    response_model=VoucherResponse,
    summary="Cerrar voucher",
    description="Transición: → CLOSED"
)
def close_voucher(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    received_by_id: Optional[int] = Query(None, gt=0, description="ID de quien recibe"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "close", min_level=3))
):
    """
    Cierra un voucher: → CLOSED

    Casos de uso:
    - EXIT sin retorno: APPROVED → CLOSED (al escanear QR)
    - EXIT con retorno: IN_TRANSIT → CLOSED (al registrar entry_log COMPLETE)
    - ENTRY: PENDING → CLOSED (al registrar entry_log COMPLETE)

    Validaciones:
    - Estado permite cierre
    - received_by existe (si se proporciona)

    Permisos requeridos: vouchers:close (nivel 3+)
    """
    controller = VoucherController(db)
    return controller.close(voucher_id, current_user.id, received_by_id)


@router.post(
    "/{voucher_id}/cancel",
    response_model=VoucherResponse,
    summary="Cancelar voucher",
    description="Transición: → CANCELLED (solo desde PENDING o APPROVED)"
)
def cancel_voucher(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    cancel_data: VoucherCancel = Body(..., description="Razón de cancelación"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "cancel", min_level=3))
):
    """
    Cancela un voucher: → CANCELLED

    Solo permitido desde:
    - PENDING
    - APPROVED

    No permitido desde:
    - IN_TRANSIT (ya está en tránsito)
    - CLOSED (ya completado)
    - OVERDUE (requiere resolución)

    Validaciones:
    - Estado actual permite cancelación
    - Razón de cancelación proporcionada

    Permisos requeridos: vouchers:cancel (nivel 3+)
    """
    controller = VoucherController(db)
    return controller.cancel(voucher_id, cancel_data, current_user.id)


# ==================== SEARCH & FILTER ENDPOINTS ====================

@router.get(
    "/search/advanced",
    response_model=VoucherSearchResponse,
    summary="Búsqueda avanzada de vouchers",
    description="Búsqueda con múltiples filtros"
)
def search_vouchers(
    search_term: Optional[str] = Query(None, description="Buscar en folio o notas"),
    company_id: Optional[int] = Query(None, gt=0, description="Filtrar por empresa"),
    status: Optional[VoucherStatusEnum] = Query(None, description="Filtrar por estado"),
    voucher_type: Optional[VoucherTypeEnum] = Query(None, description="Filtrar por tipo"),
    from_date: Optional[date] = Query(None, description="Fecha desde"),
    to_date: Optional[date] = Query(None, description="Fecha hasta"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "search", min_level=1))
):
    """
    Búsqueda avanzada de vouchers con múltiples filtros.

    Filtros disponibles:
    - search_term: Busca en folio y notas
    - company_id: Filtra por empresa específica
    - status: PENDING, APPROVED, IN_TRANSIT, OVERDUE, CLOSED, CANCELLED
    - voucher_type: ENTRY o EXIT
    - from_date: Fecha de creación desde
    - to_date: Fecha de creación hasta

    Permisos requeridos: vouchers:search (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.search(
        search_term=search_term,
        company_id=company_id,
        status=status,
        voucher_type=voucher_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )


@router.get(
    "/company/{company_id}",
    response_model=list[VoucherResponse],
    summary="Listar vouchers por empresa",
    description="Lista todos los vouchers de una empresa específica"
)
def get_vouchers_by_company(
    company_id: int = Path(..., gt=0, description="ID de la empresa"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "list", min_level=1))
):
    """
    Lista vouchers de una empresa.

    Parámetros:
    - company_id: ID de la empresa
    - skip: Registros a saltar
    - limit: Máximo de registros

    Permisos requeridos: vouchers:list (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.find_by_company(company_id, skip, limit)


@router.get(
    "/status/{status}",
    response_model=list[VoucherResponse],
    summary="Listar vouchers por estado",
    description="Lista todos los vouchers de un estado específico"
)
def get_vouchers_by_status(
    status: VoucherStatusEnum = Path(..., description="Estado del voucher"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "list", min_level=1))
):
    """
    Lista vouchers por estado.

    Estados disponibles:
    - PENDING: Pendiente de aprobación
    - APPROVED: Aprobado
    - IN_TRANSIT: En tránsito
    - OVERDUE: Vencido
    - CLOSED: Cerrado
    - CANCELLED: Cancelado

    Permisos requeridos: vouchers:list (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.find_by_status(status, skip, limit)


# ==================== QR VALIDATION ====================

@router.get(
    "/{voucher_id}/validate-qr",
    response_model=dict,
    summary="Validar token QR",
    description="Valida el token QR de un voucher (válido por 24h)"
)
def validate_qr_token(
    voucher_id: int = Path(..., gt=0, description="ID del voucher"),
    token: str = Query(..., min_length=64, max_length=64, description="Token QR a validar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "validate_qr", min_level=1))
):
    """
    Valida token QR de un voucher.

    El token QR es válido por 24 horas desde su generación.

    Retorna:
    - voucher_id: ID del voucher
    - folio: Folio del voucher
    - is_valid: True si token es válido
    - status: Estado actual del voucher
    - message: Mensaje de resultado

    Permisos requeridos: vouchers:validate_qr (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.validate_qr(voucher_id, token)


# ==================== STATISTICS ====================

@router.get(
    "/statistics/overview",
    response_model=VoucherStatistics,
    summary="Estadísticas de vouchers",
    description="Obtiene estadísticas completas de vouchers"
)
def get_statistics(
    company_id: Optional[int] = Query(None, gt=0, description="Filtrar por empresa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "view_statistics", min_level=1))
):
    """
    Obtiene estadísticas de vouchers.

    Incluye:
    - Total de vouchers
    - Por estado (PENDING, APPROVED, IN_TRANSIT, OVERDUE, CLOSED, CANCELLED)
    - Por tipo (ENTRY, EXIT)
    - Pendientes de aprobación
    - Vencidos
    - En tránsito

    Parámetros:
    - company_id: Si se proporciona, filtra por empresa

    Permisos requeridos: vouchers:view_statistics (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.get_statistics(company_id)


# ==================== UTILITY ENDPOINTS ====================

@router.get(
    "/utils/enums",
    response_model=dict,
    summary="Obtener ENUMs disponibles",
    description="Retorna los valores de ENUMs para formularios dinámicos"
)
def get_enums(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "list", min_level=1))
):
    """
    Retorna los ENUMs disponibles para Voucher.

    Útil para formularios dinámicos en frontend.

    Retorna:
    - voucher_types: [ENTRY, EXIT]
    - voucher_statuses: [PENDING, APPROVED, IN_TRANSIT, OVERDUE, CLOSED, CANCELLED]

    Permisos requeridos: vouchers:list (nivel 1+)
    """
    controller = VoucherController(db)
    return controller.get_enums()


# ==================== MAINTENANCE ENDPOINTS ====================

@router.post(
    "/maintenance/check-overdue",
    response_model=dict,
    summary="Proceso automático: revisar vencidos",
    description="Marca vouchers vencidos (proceso de mantenimiento)"
)
def check_overdue_vouchers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vouchers", "maintenance", min_level=4))
):
    """
    Proceso automático para marcar vouchers vencidos.

    Busca vouchers con:
    - status = IN_TRANSIT
    - with_return = True
    - estimated_return_date < hoy

    Y los marca como OVERDUE.

    Este endpoint está pensado para ser llamado por un scheduler diario.

    Permisos requeridos: vouchers:maintenance (nivel 4 - Admin)
    """
    controller = VoucherController(db)
    return controller.check_overdue_vouchers(current_user.id)
