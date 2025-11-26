"""
VoucherDetail Router
Endpoints REST API para VoucherDetails
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Union

from database import get_db, User
from app.shared.dependencies import require_permission
from app.entities.voucher_details.controllers.voucher_detail_controller import VoucherDetailController
from app.entities.voucher_details.schemas.voucher_detail_schemas import (
    VoucherDetailCreate,
    VoucherDetailUpdate,
    VoucherDetailResponse,
    VoucherDetailWithProduct,
    ProductMatchResponse,
    ProductMatchesFound
)


router = APIRouter(
    prefix="/voucher-details",
    tags=["Voucher Details"]
)


@router.post(
    "/",
    response_model=Union[VoucherDetailWithProduct, ProductMatchesFound],
    status_code=status.HTTP_201_CREATED,
    summary="Create voucher detail line",
    description="""
    Crea una línea de detalle en un vale (máximo 20 líneas).

    **Flujo Inteligente:**
    1. Si `product_id` se proporciona → usa ese producto
    2. Si no, busca automáticamente productos similares por `item_name`
    3. Si encuentra coincidencias → devuelve lista para selección (ProductMatchesFound)
    4. Si no encuentra → auto-crea producto en cache

    **Query Params:**
    - `skip_similarity_search=true`: Salta búsqueda y crea producto directo (útil cuando usuario ya revisó y no encontró)

    **Respuestas:**
    - `201 Created`: Detalle creado exitosamente (VoucherDetailWithProduct)
    - `200 OK`: Productos similares encontrados, seleccione uno (ProductMatchesFound)
    - `400 Bad Request`: Validación fallida (máximo 20 líneas)
    - `404 Not Found`: Voucher no existe
    """
)
def create_detail(
    detail_data: VoucherDetailCreate,
    skip_similarity_search: bool = Query(
        default=False,
        description="Si True, salta búsqueda por similitud y auto-crea producto"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("voucher_details", "create", min_level=3))
):
    """Crea línea de detalle con auto-cache de productos"""
    controller = VoucherDetailController(db)
    return controller.create(
        detail_data,
        current_user_id=current_user.id,
        skip_similarity_search=skip_similarity_search
    )


@router.get(
    "/{detail_id}",
    response_model=VoucherDetailResponse,
    summary="Get voucher detail by ID",
    description="Obtiene una línea de detalle específica por su ID"
)
def get_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("voucher_details", "get", min_level=1))
):
    """Obtiene detalle por ID"""
    controller = VoucherDetailController(db)
    return controller.get_by_id(detail_id)


@router.get(
    "/voucher/{voucher_id}",
    response_model=List[VoucherDetailWithProduct],
    summary="Get all details of a voucher",
    description="Obtiene todas las líneas de detalle de un vale específico, ordenadas por line_number"
)
def get_details_by_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("voucher_details", "list", min_level=1))
):
    """Obtiene todas las líneas de un vale"""
    controller = VoucherDetailController(db)
    return controller.get_by_voucher(voucher_id)


@router.put(
    "/{detail_id}",
    response_model=VoucherDetailWithProduct,
    summary="Update voucher detail",
    description="Actualiza una línea de detalle existente"
)
def update_detail(
    detail_id: int,
    detail_data: VoucherDetailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("voucher_details", "update", min_level=2))
):
    """Actualiza detalle"""
    controller = VoucherDetailController(db)
    return controller.update(detail_id, detail_data, current_user_id=current_user.id)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete voucher detail",
    description="Elimina (soft delete) una línea de detalle"
)
def delete_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("voucher_details", "delete", min_level=4))
):
    """Elimina detalle (soft delete)"""
    controller = VoucherDetailController(db)
    return controller.delete(detail_id, current_user_id=current_user.id)


@router.get(
    "/search/products",
    response_model=List[ProductMatchResponse],
    summary="Search products by similarity",
    description="""
    Busca productos en cache por similitud de nombre.
    Útil para autocomplete en frontend.

    Ordena por `usage_count DESC` (más usados primero).
    """
)
def search_products(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    limit: int = Query(default=10, ge=1, le=50, description="Límite de resultados"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("voucher_details", "search", min_level=1))
):
    """Busca productos por similitud (autocomplete)"""
    controller = VoucherDetailController(db)
    return controller.search_products(q, limit)
