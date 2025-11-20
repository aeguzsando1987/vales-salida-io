"""
Product Router
Endpoints FastAPI para productos
"""
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, User
from app.shared.dependencies import require_permission
from app.entities.products.controllers.product_controller import ProductController
from app.entities.products.schemas.product_schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductSearchResponse,
    ProductCategoryEnum
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new product"
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "create", min_level=3))
):
    """
    Crea un nuevo producto en el cache

    - **code**: Código único (opcional)
    - **name**: Nombre del producto (requerido)
    - **description**: Descripción detallada
    - **part_number**: Número de parte
    - **category**: Categoría del producto
    - **unit_of_measure**: Unidad de medida (PZA, KG, LT, M, etc.)
    - **is_serialized**: ¿Requiere número de serie?
    """
    controller = ProductController(db)
    return controller.create_product(product_data, current_user.id)


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List all products"
)
def list_products(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    active_only: bool = Query(True, description="Solo productos activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "list", min_level=1))
):
    """
    Lista todos los productos con paginación
    """
    controller = ProductController(db)
    return controller.list_products(skip=skip, limit=limit, active_only=active_only)


@router.get(
    "/paginated",
    response_model=ProductListResponse,
    summary="List products with pagination metadata"
)
def paginate_products(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Registros por página"),
    order_by: str = Query("usage_count", description="Campo para ordenar"),
    order_direction: str = Query("desc", regex="^(asc|desc)$", description="Dirección"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "list", min_level=1))
):
    """
    Lista productos con metadata de paginación completa
    """
    controller = ProductController(db)
    return controller.paginate_products(
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_direction=order_direction
    )


@router.get(
    "/search",
    response_model=List[ProductSearchResponse],
    summary="Search products (autocomplete)"
)
def search_products(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    limit: int = Query(10, ge=1, le=50, description="Máximo de resultados"),
    active_only: bool = Query(True, description="Solo productos activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "search", min_level=1))
):
    """
    Búsqueda de productos por código o nombre (autocomplete)

    Retorna productos ordenados por uso (usage_count DESC)
    """
    controller = ProductController(db)
    return controller.search_products(search_term=q, limit=limit, active_only=active_only)


@router.get(
    "/top-used",
    response_model=List[ProductResponse],
    summary="Get most used products"
)
def get_top_used_products(
    limit: int = Query(20, ge=1, le=100, description="Número de productos"),
    active_only: bool = Query(True, description="Solo productos activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "list", min_level=1))
):
    """
    Obtiene los productos más usados

    Ordenados por usage_count DESC
    """
    controller = ProductController(db)
    return controller.get_top_used(limit=limit, active_only=active_only)


@router.get(
    "/category/{category}",
    response_model=List[ProductResponse],
    summary="Get products by category"
)
def get_products_by_category(
    category: ProductCategoryEnum = Path(..., description="Categoría del producto"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    active_only: bool = Query(True, description="Solo productos activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "list", min_level=1))
):
    """
    Obtiene productos filtrados por categoría
    """
    controller = ProductController(db)
    return controller.get_by_category(
        category=category.value,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID"
)
def get_product(
    product_id: int = Path(..., gt=0, description="ID del producto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "get", min_level=1))
):
    """
    Obtiene un producto por su ID
    """
    controller = ProductController(db)
    return controller.get_product(product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product"
)
def update_product(
    product_id: int = Path(..., gt=0, description="ID del producto"),
    product_data: ProductUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "update", min_level=2))
):
    """
    Actualiza un producto existente

    Todos los campos son opcionales
    """
    controller = ProductController(db)
    return controller.update_product(product_id, product_data, current_user.id)


@router.delete(
    "/{product_id}",
    summary="Delete product (soft delete)"
)
def delete_product(
    product_id: int = Path(..., gt=0, description="ID del producto"),
    hard_delete: bool = Query(False, description="Si True, borra físicamente"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products", "delete", min_level=4))
):
    """
    Elimina un producto

    Por defecto usa soft delete (is_deleted=True)

    Usar hard_delete=true para borrado físico
    """
    controller = ProductController(db)
    return controller.delete_product(
        product_id,
        current_user.id,
        soft_delete=not hard_delete
    )