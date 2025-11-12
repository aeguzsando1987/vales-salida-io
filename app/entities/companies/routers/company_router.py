"""
Router para la entidad Company

Define todos los endpoints HTTP de la API para empresas.
Implementa sistema de permisos granulares.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, User
from app.shared.dependencies import require_permission
from app.entities.companies.controllers.company_controller import CompanyController
from app.entities.companies.schemas.company_schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    CompanyWithRelations,
    CompanySearch,
    CompanyStatistics,
    CompanyStatus,
    TaxSystem
)

# ==================== CONFIGURACIÓN DEL ROUTER ====================

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    responses={404: {"description": "Not found"}}
)


# ==================== ENDPOINTS CRUD ====================

@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa",
    description="Crea una nueva empresa. Requiere permisos de creación."
)
def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "create", min_level=3))
):
    """
    Crea una nueva empresa.

    Validaciones:
    - TIN único
    - País existe
    - Estado existe y pertenece al país
    """
    controller = CompanyController(db)
    return controller.create_company(company_data, current_user)


@router.get(
    "/",
    response_model=CompanyListResponse,
    summary="Listar empresas",
    description="Obtiene lista paginada de empresas"
)
def list_companies(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Registros por página"),
    active_only: bool = Query(True, description="Solo empresas activas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "list", min_level=1))
):
    """
    Lista todas las empresas con paginación.

    Parámetros:
    - page: Número de página
    - per_page: Registros por página (máx 100)
    - active_only: Filtrar solo activas
    """
    controller = CompanyController(db)
    return controller.get_all_companies(page, per_page, active_only)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Obtener empresa por ID",
    description="Obtiene los detalles de una empresa específica"
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "get", min_level=1))
):
    """
    Obtiene una empresa por su ID.

    Args:
        company_id: ID de la empresa

    Returns:
        Empresa encontrada

    Raises:
        404: Si la empresa no existe
    """
    controller = CompanyController(db)
    return controller.get_company(company_id)


@router.get(
    "/{company_id}/details",
    response_model=CompanyWithRelations,
    summary="Obtener empresa con relaciones",
    description="Obtiene empresa con datos de país, estado y usuarios"
)
def get_company_details(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "get", min_level=1))
):
    """
    Obtiene una empresa con sus relaciones cargadas.

    Incluye:
    - Nombre del país
    - Nombre del estado
    - Usuario creador
    - Usuario actualizador
    """
    controller = CompanyController(db)
    return controller.get_company_with_relations(company_id)


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Actualizar empresa",
    description="Actualiza los datos de una empresa"
)
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "update", min_level=2))
):
    """
    Actualiza una empresa existente.

    Todos los campos son opcionales. Solo se actualizan los campos enviados.

    Validaciones:
    - TIN único (si se actualiza)
    - País existe (si se actualiza)
    - Estado pertenece al país (si se actualiza)
    """
    controller = CompanyController(db)
    return controller.update_company(company_id, company_data, current_user)


@router.delete(
    "/{company_id}",
    summary="Eliminar empresa",
    description="Elimina una empresa (soft delete por defecto)"
)
def delete_company(
    company_id: int,
    hard_delete: bool = Query(False, description="Eliminación física si es True"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "delete", min_level=4))
):
    """
    Elimina una empresa.

    Por defecto hace soft delete (marca como eliminada).
    Si hard_delete=True, elimina físicamente del registro.
    """
    controller = CompanyController(db)
    return controller.delete_company(company_id, current_user, hard_delete)


# ==================== ENDPOINTS DE BÚSQUEDA ====================

@router.get(
    "/search/by-tin/{tin}",
    response_model=CompanyResponse,
    summary="Buscar empresa por TIN",
    description="Busca una empresa por su número de identificación fiscal"
)
def get_company_by_tin(
    tin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "search", min_level=1))
):
    """
    Busca una empresa por su TIN (Tax Identification Number).

    Args:
        tin: Número de identificación fiscal (RFC, EIN, NIF, etc.)

    Returns:
        Empresa encontrada

    Raises:
        404: Si no existe empresa con ese TIN
    """
    controller = CompanyController(db)
    return controller.get_company_by_tin(tin)


@router.get(
    "/by-country/{country_id}",
    response_model=CompanyListResponse,
    summary="Empresas por país",
    description="Obtiene empresas de un país específico"
)
def get_companies_by_country(
    country_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "list", min_level=1))
):
    """
    Obtiene empresas de un país específico.

    Args:
        country_id: ID del país
        page: Número de página
        per_page: Registros por página
        active_only: Solo empresas activas
    """
    controller = CompanyController(db)
    return controller.get_companies_by_country(country_id, page, per_page, active_only)


@router.get(
    "/by-state/{state_id}",
    response_model=CompanyListResponse,
    summary="Empresas por estado",
    description="Obtiene empresas de un estado específico"
)
def get_companies_by_state(
    state_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "list", min_level=1))
):
    """
    Obtiene empresas de un estado específico.

    Args:
        state_id: ID del estado
        page: Número de página
        per_page: Registros por página
        active_only: Solo empresas activas
    """
    controller = CompanyController(db)
    return controller.get_companies_by_state(state_id, page, per_page, active_only)


@router.post(
    "/search/advanced",
    response_model=CompanyListResponse,
    summary="Búsqueda avanzada",
    description="Búsqueda con múltiples filtros"
)
def search_companies(
    search_data: CompanySearch,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "search", min_level=1))
):
    """
    Búsqueda avanzada de empresas.

    Permite filtrar por:
    - Término de búsqueda (nombre, TIN, email)
    - País
    - Estado
    - Estado administrativo
    - Sistema fiscal
    """
    controller = CompanyController(db)
    return controller.search_companies(search_data, page, per_page)


# ==================== ENDPOINTS DE ESTADÍSTICAS ====================

@router.get(
    "/statistics/overview",
    response_model=CompanyStatistics,
    summary="Estadísticas generales",
    description="Obtiene estadísticas de empresas"
)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "view_statistics", min_level=1))
):
    """
    Obtiene estadísticas generales de empresas.

    Incluye:
    - Total de empresas
    - Empresas por estado (active, inactive, suspended)
    - Empresas por país
    - Empresas por sistema fiscal
    """
    controller = CompanyController(db)
    return controller.get_statistics()


# ==================== ENDPOINTS DE OPERACIONES DE ESTADO ====================

@router.patch(
    "/{company_id}/activate",
    response_model=CompanyResponse,
    summary="Activar empresa",
    description="Cambia el estado de la empresa a activo"
)
def activate_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "update", min_level=2))
):
    """
    Activa una empresa.

    Cambia:
    - status = "active"
    - is_active = True
    """
    controller = CompanyController(db)
    return controller.activate_company(company_id, current_user)


@router.patch(
    "/{company_id}/suspend",
    response_model=CompanyResponse,
    summary="Suspender empresa",
    description="Cambia el estado de la empresa a suspendido"
)
def suspend_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "update", min_level=2))
):
    """
    Suspende una empresa.

    Cambia status = "suspended"
    """
    controller = CompanyController(db)
    return controller.suspend_company(company_id, current_user)


@router.patch(
    "/{company_id}/deactivate",
    response_model=CompanyResponse,
    summary="Desactivar empresa",
    description="Cambia el estado de la empresa a inactivo"
)
def deactivate_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "update", min_level=2))
):
    """
    Desactiva una empresa.

    Cambia:
    - status = "inactive"
    - is_active = False
    """
    controller = CompanyController(db)
    return controller.deactivate_company(company_id, current_user)


# ==================== ENDPOINTS DE ENUMS ====================

@router.get(
    "/enums/statuses",
    summary="Obtener estados disponibles",
    description="Lista los estados posibles de una empresa"
)
def get_company_statuses(
    current_user: User = Depends(require_permission("companies", "list", min_level=1))
):
    """
    Retorna lista de estados disponibles para empresas.

    Returns:
        Lista de valores válidos para el campo status
    """
    return {
        "statuses": [status.value for status in CompanyStatus],
        "description": {
            "active": "Empresa activa y operando",
            "inactive": "Empresa inactiva temporalmente",
            "suspended": "Empresa suspendida por razones administrativas"
        }
    }


@router.get(
    "/enums/tax-systems",
    summary="Obtener sistemas fiscales",
    description="Lista los sistemas fiscales disponibles"
)
def get_tax_systems(
    current_user: User = Depends(require_permission("companies", "list", min_level=1))
):
    """
    Retorna lista de sistemas fiscales disponibles.

    Returns:
        Lista de valores válidos para el campo tax_system
    """
    return {
        "tax_systems": [tax.value for tax in TaxSystem],
        "description": {
            "RFC": "Registro Federal de Contribuyentes (México)",
            "EIN": "Employer Identification Number (USA)",
            "NIF": "Número de Identificación Fiscal (España)",
            "CUIT": "Clave Única de Identificación Tributaria (Argentina)",
            "RUC": "Registro Único de Contribuyentes (Perú, Ecuador)",
            "RUT": "Rol Único Tributario (Chile)",
            "CNPJ": "Cadastro Nacional da Pessoa Jurídica (Brasil)",
            "OTHER": "Otro sistema fiscal"
        }
    }