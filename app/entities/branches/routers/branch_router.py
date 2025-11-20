"""
Router para la entidad Branch.

Define todos los endpoints HTTP con documentación Swagger,
validación de permisos y manejo de responses.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from database import get_db, User
from app.shared.dependencies import require_permission

from app.entities.branches.controllers.branch_controller import BranchController
from app.entities.branches.schemas.branch_schemas import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchWithRelations,
    BranchListResponse,
    BranchSearch,
    BranchStatusUpdate,
    BranchType,
    OperationalStatus
)


# ==================== ROUTER CONFIGURATION ====================

router = APIRouter(
    prefix="/branches",
    tags=["Branches"],
    responses={
        404: {"description": "Sucursal no encontrada"},
        400: {"description": "Datos inválidos"},
        403: {"description": "Permisos insuficientes"}
    }
)


# ==================== CRUD ENDPOINTS ====================

@router.post(
    "/",
    response_model=BranchResponse,
    status_code=201,
    summary="Crear sucursal",
    description="Crea una nueva sucursal/ubicación con validaciones completas"
)
def create_branch(
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "create", min_level=3))
):
    """
    Crea una nueva sucursal.

    Validaciones:
    - Código único
    - Empresa existe
    - País existe
    - Estado existe (si se proporciona)
    - Manager existe (si se proporciona)

    Permisos requeridos: branches:create (nivel 3+)
    """
    controller = BranchController(db)
    return controller.create(branch_data, current_user.id)


@router.get(
    "/{branch_id}",
    response_model=BranchResponse,
    summary="Obtener sucursal por ID",
    description="Retorna una sucursal específica por su ID"
)
def get_branch(
    branch_id: int = Path(..., gt=0, description="ID de la sucursal"),
    with_relations: bool = Query(False, description="Incluir nombres de relaciones"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "get", min_level=1))
):
    """
    Obtiene una sucursal por ID.

    Parámetros:
    - branch_id: ID de la sucursal
    - with_relations: Si es True, incluye company_name, country_name, etc.

    Permisos requeridos: branches:get (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_by_id(branch_id, with_relations)


@router.get(
    "/code/{code}",
    response_model=BranchResponse,
    summary="Obtener sucursal por código",
    description="Busca una sucursal por su código único"
)
def get_branch_by_code(
    code: str = Path(..., min_length=2, max_length=50, description="Código de la sucursal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "get", min_level=1))
):
    """
    Obtiene una sucursal por código.

    Parámetros:
    - code: Código de la sucursal (se normaliza a mayúsculas)

    Permisos requeridos: branches:get (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_by_code(code)


@router.put(
    "/{branch_id}",
    response_model=BranchResponse,
    summary="Actualizar sucursal",
    description="Actualiza los datos de una sucursal existente"
)
def update_branch(
    branch_id: int = Path(..., gt=0, description="ID de la sucursal"),
    branch_data: BranchUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "update", min_level=2))
):
    """
    Actualiza una sucursal.

    Validaciones:
    - Sucursal existe
    - Código único (si se cambia)
    - Referencias válidas (si se cambian)

    Permisos requeridos: branches:update (nivel 2+)
    """
    controller = BranchController(db)
    return controller.update(branch_id, branch_data, current_user.id)


@router.delete(
    "/{branch_id}",
    response_model=dict,
    summary="Eliminar sucursal",
    description="Elimina una sucursal (soft delete por defecto)"
)
def delete_branch(
    branch_id: int = Path(..., gt=0, description="ID de la sucursal"),
    soft_delete: bool = Query(True, description="Si es True, soft delete; si es False, hard delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "delete", min_level=4))
):
    """
    Elimina una sucursal.

    Parámetros:
    - branch_id: ID de la sucursal
    - soft_delete: True para soft delete (por defecto), False para hard delete

    Permisos requeridos: branches:delete (nivel 4)
    """
    controller = BranchController(db)
    return controller.delete(branch_id, current_user.id, soft_delete)


# ==================== SEARCH & LIST ENDPOINTS ====================

@router.get(
    "/",
    response_model=BranchListResponse,
    summary="Búsqueda avanzada de sucursales",
    description="Lista y filtra sucursales con paginación"
)
def search_branches(
    search_term: Optional[str] = Query(None, description="Buscar en código, nombre o ciudad"),
    branch_type: Optional[BranchType] = Query(None, description="Filtrar por tipo"),
    company_id: Optional[int] = Query(None, gt=0, description="Filtrar por empresa"),
    country_id: Optional[int] = Query(None, gt=0, description="Filtrar por país"),
    state_id: Optional[int] = Query(None, gt=0, description="Filtrar por estado"),
    operational_status: Optional[OperationalStatus] = Query(None, description="Filtrar por estado operativo"),
    active_only: bool = Query(True, description="Solo registros activos"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Registros por página"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "list", min_level=1))
):
    """
    Búsqueda avanzada de sucursales con múltiples filtros.

    Filtros disponibles:
    - search_term: Busca en código, nombre o ciudad
    - branch_type: warehouse, project, plant, office, site
    - company_id: ID de la empresa
    - country_id: ID del país
    - state_id: ID del estado
    - operational_status: active, inactive, maintenance, closed
    - active_only: Solo registros activos

    Permisos requeridos: branches:list (nivel 1+)
    """
    controller = BranchController(db)

    search_params = BranchSearch(
        search_term=search_term,
        branch_type=branch_type,
        company_id=company_id,
        country_id=country_id,
        state_id=state_id,
        operational_status=operational_status,
        active_only=active_only
    )

    return controller.search(search_params, page, per_page)


@router.get(
    "/by-company/{company_id}",
    response_model=list[BranchResponse],
    summary="Listar sucursales por empresa",
    description="Retorna todas las sucursales de una empresa específica"
)
def get_branches_by_company(
    company_id: int = Path(..., gt=0, description="ID de la empresa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "list", min_level=1))
):
    """
    Lista sucursales de una empresa.

    Permisos requeridos: branches:list (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_by_company(company_id)


@router.get(
    "/by-type/{branch_type}",
    response_model=list[BranchResponse],
    summary="Listar sucursales por tipo",
    description="Retorna todas las sucursales de un tipo específico"
)
def get_branches_by_type(
    branch_type: BranchType = Path(..., description="Tipo de sucursal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "list", min_level=1))
):
    """
    Lista sucursales por tipo.

    Tipos disponibles:
    - warehouse: Almacén
    - project: Proyecto/Obra
    - plant: Planta industrial
    - office: Oficina
    - site: Sitio temporal

    Permisos requeridos: branches:list (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_by_type(branch_type)


@router.get(
    "/by-location/",
    response_model=list[BranchResponse],
    summary="Listar sucursales por ubicación",
    description="Busca sucursales por país, estado y/o ciudad"
)
def get_branches_by_location(
    country_id: int = Query(..., gt=0, description="ID del país"),
    state_id: Optional[int] = Query(None, gt=0, description="ID del estado (opcional)"),
    city: Optional[str] = Query(None, max_length=100, description="Ciudad (opcional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "list", min_level=1))
):
    """
    Lista sucursales por ubicación geográfica.

    Parámetros:
    - country_id: ID del país (obligatorio)
    - state_id: ID del estado (opcional)
    - city: Nombre de ciudad (opcional, búsqueda parcial)

    Permisos requeridos: branches:list (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_by_location(country_id, state_id, city)


# ==================== SPECIAL OPERATIONS ====================

@router.patch(
    "/{branch_id}/status",
    response_model=BranchResponse,
    summary="Actualizar estado operativo",
    description="Cambia solo el estado operativo de una sucursal"
)
def update_branch_status(
    branch_id: int = Path(..., gt=0, description="ID de la sucursal"),
    status_data: BranchStatusUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "update", min_level=2))
):
    """
    Actualiza el estado operativo de una sucursal.

    Estados disponibles:
    - active: Activa y operando
    - inactive: Inactiva temporalmente
    - maintenance: En mantenimiento
    - closed: Cerrada permanentemente

    Permisos requeridos: branches:update (nivel 2+)
    """
    controller = BranchController(db)
    return controller.update_status(branch_id, status_data, current_user.id)


@router.get(
    "/statistics/overview",
    response_model=dict,
    summary="Estadísticas de sucursales",
    description="Retorna estadísticas generales de sucursales"
)
def get_branch_statistics(
    company_id: Optional[int] = Query(None, gt=0, description="Filtrar por empresa (opcional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "list", min_level=1))
):
    """
    Obtiene estadísticas de sucursales.

    Retorna:
    - Total de sucursales
    - Distribución por tipo
    - Distribución por estado operativo

    Permisos requeridos: branches:list (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_statistics(company_id)


@router.get(
    "/enums/values",
    response_model=dict,
    summary="Obtener valores de ENUMs",
    description="Retorna los valores disponibles para branch_type y operational_status"
)
def get_branch_enums(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("branches", "list", min_level=1))
):
    """
    Retorna los ENUMs disponibles para Branch.

    Útil para construir formularios dinámicos en frontend.

    Retorna:
    - branch_types: Lista de tipos de sucursal
    - operational_statuses: Lista de estados operativos

    Permisos requeridos: branches:list (nivel 1+)
    """
    controller = BranchController(db)
    return controller.get_enums()