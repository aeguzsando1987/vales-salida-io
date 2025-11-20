"""
Product Controller
Orquestación de requests/responses para productos
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.entities.products.services.product_service import ProductService
from app.entities.products.schemas.product_schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductSearchResponse
)
from app.entities.products.models.product import Product
from app.shared.exceptions import EntityNotFoundError, EntityValidationError


class ProductController:
    """Controller para orquestar operaciones de Product"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ProductService(db)

    def create_product(self, product_data: ProductCreate, user_id: int) -> ProductResponse:
        """
        Crea un nuevo producto

        Args:
            product_data: Datos del producto
            user_id: ID del usuario creador

        Returns:
            ProductResponse

        Raises:
            EntityValidationError: Si hay errores de validación
        """
        product = self.service.create_product(product_data, user_id)
        return ProductResponse.model_validate(product)

    def get_product(self, product_id: int) -> ProductResponse:
        """
        Obtiene un producto por ID

        Args:
            product_id: ID del producto

        Returns:
            ProductResponse

        Raises:
            EntityNotFoundError: Si no existe
        """
        product = self.service.get_product_by_id(product_id)
        return ProductResponse.model_validate(product)

    def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ProductResponse]:
        """
        Lista todos los productos

        Args:
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos

        Returns:
            Lista de ProductResponse
        """
        products = self.service.get_all_products(skip=skip, limit=limit, active_only=active_only)
        return [ProductResponse.model_validate(p) for p in products]

    def update_product(
        self,
        product_id: int,
        product_data: ProductUpdate,
        user_id: int
    ) -> ProductResponse:
        """
        Actualiza un producto

        Args:
            product_id: ID del producto
            product_data: Datos a actualizar
            user_id: ID del usuario

        Returns:
            ProductResponse

        Raises:
            EntityNotFoundError: Si no existe
            EntityValidationError: Si hay errores
        """
        product = self.service.update_product(product_id, product_data, user_id)
        return ProductResponse.model_validate(product)

    def delete_product(
        self,
        product_id: int,
        user_id: int,
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Elimina un producto

        Args:
            product_id: ID del producto
            user_id: ID del usuario
            soft_delete: Soft delete por defecto

        Returns:
            Dict con mensaje de éxito

        Raises:
            EntityNotFoundError: Si no existe
        """
        self.service.delete_product(product_id, user_id, soft_delete)
        return {
            "message": "Product deleted successfully",
            "id": product_id,
            "soft_delete": soft_delete
        }

    def search_products(
        self,
        search_term: str,
        limit: int = 10,
        active_only: bool = True
    ) -> List[ProductSearchResponse]:
        """
        Búsqueda de productos (autocomplete)

        Args:
            search_term: Término de búsqueda
            limit: Máximo de resultados
            active_only: Solo activos

        Returns:
            Lista de ProductSearchResponse
        """
        products = self.service.search_products(
            search_term=search_term,
            limit=limit,
            active_only=active_only
        )
        return [ProductSearchResponse.model_validate(p) for p in products]

    def get_top_used(self, limit: int = 20, active_only: bool = True) -> List[ProductResponse]:
        """
        Obtiene los productos más usados

        Args:
            limit: Número de productos
            active_only: Solo activos

        Returns:
            Lista de ProductResponse
        """
        products = self.service.get_top_used_products(limit=limit, active_only=active_only)
        return [ProductResponse.model_validate(p) for p in products]

    def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ProductResponse]:
        """
        Obtiene productos por categoría

        Args:
            category: Categoría
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos

        Returns:
            Lista de ProductResponse
        """
        products = self.service.get_by_category(
            category=category,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        return [ProductResponse.model_validate(p) for p in products]

    def paginate_products(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "usage_count",
        order_direction: str = "desc"
    ) -> ProductListResponse:
        """
        Paginación de productos

        Args:
            page: Número de página
            per_page: Registros por página
            filters: Filtros opcionales
            order_by: Campo para ordenar
            order_direction: Dirección

        Returns:
            ProductListResponse con paginación
        """
        result = self.service.paginate(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction
        )

        return ProductListResponse(
            products=[ProductResponse.model_validate(p) for p in result["products"]],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            total_pages=result["total_pages"]
        )
