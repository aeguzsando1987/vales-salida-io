"""
Product Service
Lógica de negocio para productos
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.entities.products.repositories.product_repository import ProductRepository
from app.entities.products.schemas.product_schemas import ProductCreate, ProductUpdate
from app.entities.products.models.product import Product
from app.shared.exceptions import EntityNotFoundError, EntityValidationError


class ProductService:
    """Service para lógica de negocio de Product"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProductRepository(db)

    def create_product(self, product_data: ProductCreate, user_id: int) -> Product:
        """
        Crea un nuevo producto

        Args:
            product_data: Datos del producto
            user_id: ID del usuario creador

        Returns:
            Product creado

        Raises:
            EntityValidationError: Si el código ya existe
        """
        # Validar código único
        if product_data.code:
            if self.repository.code_exists(product_data.code):
                raise EntityValidationError(
                    "Product",
                    {"code": f"El código '{product_data.code}' ya existe"}
                )

        # Validar nombre duplicado (opcional - puede haber nombres iguales)
        # existing = self.repository.find_by_name_exact(product_data.name)
        # if existing:
        #     raise EntityValidationError(
        #         "Product",
        #         {"name": f"Ya existe un producto con el nombre '{product_data.name}'"}
        #     )

        # Crear producto
        product_dict = product_data.model_dump()
        product_dict['created_by'] = user_id
        product_dict['usage_count'] = 0
        product_dict['is_active'] = True

        new_product = self.repository.create(product_dict)

        return new_product

    def get_product_by_id(self, product_id: int) -> Product:
        """
        Obtiene un producto por ID

        Args:
            product_id: ID del producto

        Returns:
            Product encontrado

        Raises:
            EntityNotFoundError: Si no existe
        """
        product = self.repository.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError("Product", product_id)
        return product

    def get_all_products(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """
        Obtiene todos los productos

        Args:
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo productos activos

        Returns:
            Lista de productos
        """
        return self.repository.get_all(skip=skip, limit=limit, active_only=active_only)

    def update_product(
        self,
        product_id: int,
        product_data: ProductUpdate,
        user_id: int
    ) -> Product:
        """
        Actualiza un producto

        Args:
            product_id: ID del producto
            product_data: Datos a actualizar
            user_id: ID del usuario que actualiza

        Returns:
            Product actualizado

        Raises:
            EntityNotFoundError: Si no existe
            EntityValidationError: Si el código ya existe
        """
        product = self.get_product_by_id(product_id)

        # Validar código único
        if product_data.code:
            if self.repository.code_exists(product_data.code, exclude_id=product_id):
                raise EntityValidationError(
                    "Product",
                    {"code": f"El código '{product_data.code}' ya existe"}
                )

        # Actualizar
        update_dict = product_data.model_dump(exclude_unset=True)
        update_dict['updated_by'] = user_id

        updated_product = self.repository.update(product_id, update_dict)

        return updated_product

    def delete_product(self, product_id: int, user_id: int, soft_delete: bool = True) -> bool:
        """
        Elimina un producto

        Args:
            product_id: ID del producto
            user_id: ID del usuario que elimina
            soft_delete: Si True, marca como eliminado. Si False, borra físicamente

        Returns:
            True si se eliminó

        Raises:
            EntityNotFoundError: Si no existe
        """
        product = self.get_product_by_id(product_id)

        if soft_delete:
            # Soft delete
            self.repository.update(product_id, {
                'is_deleted': True,
                'is_active': False,
                'deleted_at': datetime.utcnow(),
                'deleted_by': user_id
            })
        else:
            # Hard delete
            self.repository.delete(product_id, soft_delete=False)

        return True

    def search_products(
        self,
        search_term: str,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Product]:
        """
        Búsqueda de productos (autocomplete)

        Args:
            search_term: Término de búsqueda
            limit: Máximo de resultados
            active_only: Solo productos activos

        Returns:
            Lista de productos ordenados por uso
        """
        return self.repository.search_by_code_or_name(
            search_term=search_term,
            limit=limit,
            active_only=active_only
        )

    def get_top_used_products(self, limit: int = 20, active_only: bool = True) -> List[Product]:
        """
        Obtiene los productos más usados

        Args:
            limit: Número de productos
            active_only: Solo activos

        Returns:
            Lista de productos más usados
        """
        return self.repository.get_top_used(limit=limit, active_only=active_only)

    def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """
        Obtiene productos por categoría

        Args:
            category: Categoría
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos

        Returns:
            Lista de productos
        """
        return self.repository.get_by_category(
            category=category,
            skip=skip,
            limit=limit,
            active_only=active_only
        )

    def increment_usage(self, product_id: int) -> bool:
        """
        Incrementa el contador de uso (llamado desde VoucherDetailService)

        Args:
            product_id: ID del producto

        Returns:
            True si se incrementó
        """
        return self.repository.increment_usage_count(product_id)

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "usage_count",
        order_direction: str = "desc"
    ) -> Dict[str, Any]:
        """
        Paginación de productos

        Args:
            page: Número de página
            per_page: Registros por página
            filters: Filtros opcionales
            order_by: Campo para ordenar
            order_direction: Dirección (asc/desc)

        Returns:
            Dict con productos y metadata de paginación
        """
        result = self.repository.paginate(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction
        )

        return {
            "products": result["items"],
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "total_pages": result["pages"]
        }
