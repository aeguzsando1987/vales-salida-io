"""
Product Repository
Acceso a datos de productos con queries especializadas
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from typing import List, Optional

from app.shared.base_repository import BaseRepository
from app.entities.products.models.product import Product


class ProductRepository(BaseRepository[Product]):
    """Repository para operaciones de base de datos de Product"""

    def __init__(self, db: Session):
        super().__init__(Product, db)

    def find_by_code(self, code: str) -> Optional[Product]:
        """
        Busca un producto por código

        Args:
            code: Código del producto

        Returns:
            Product o None si no existe
        """
        return self.db.query(Product).filter(
            Product.code == code.upper(),
            Product.is_deleted == False
        ).first()

    def find_by_name_exact(self, name: str) -> Optional[Product]:
        """
        Busca un producto por nombre exacto (case insensitive)

        Args:
            name: Nombre del producto

        Returns:
            Product o None si no existe
        """
        return self.db.query(Product).filter(
            func.lower(Product.name) == name.lower(),
            Product.is_deleted == False
        ).first()

    def search_by_name(
        self,
        search_term: str,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Product]:
        """
        Búsqueda de productos por nombre (autocomplete)

        Args:
            search_term: Término de búsqueda
            limit: Máximo de resultados
            active_only: Solo productos activos

        Returns:
            Lista de productos ordenados por usage_count DESC
        """
        query = self.db.query(Product).filter(
            Product.name.ilike(f"%{search_term}%"),
            Product.is_deleted == False
        )

        if active_only:
            query = query.filter(Product.is_active == True)

        return query.order_by(desc(Product.usage_count)).limit(limit).all()

    def search_by_code_or_name(
        self,
        search_term: str,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Product]:
        """
        Búsqueda combinada por código o nombre

        Args:
            search_term: Término de búsqueda
            limit: Máximo de resultados
            active_only: Solo productos activos

        Returns:
            Lista de productos ordenados por usage_count DESC
        """
        query = self.db.query(Product).filter(
            or_(
                Product.code.ilike(f"%{search_term}%"),
                Product.name.ilike(f"%{search_term}%")
            ),
            Product.is_deleted == False
        )

        if active_only:
            query = query.filter(Product.is_active == True)

        return query.order_by(desc(Product.usage_count)).limit(limit).all()

    def get_top_used(
        self,
        limit: int = 20,
        active_only: bool = True
    ) -> List[Product]:
        """
        Obtiene los productos más usados

        Args:
            limit: Número de productos a retornar
            active_only: Solo productos activos

        Returns:
            Lista de productos ordenados por usage_count DESC
        """
        query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.usage_count > 0
        )

        if active_only:
            query = query.filter(Product.is_active == True)

        return query.order_by(desc(Product.usage_count)).limit(limit).all()

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
            category: Categoría del producto
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo productos activos

        Returns:
            Lista de productos de la categoría
        """
        query = self.db.query(Product).filter(
            Product.category == category,
            Product.is_deleted == False
        )

        if active_only:
            query = query.filter(Product.is_active == True)

        return query.order_by(desc(Product.usage_count)).offset(skip).limit(limit).all()

    def increment_usage_count(self, product_id: int) -> bool:
        """
        Incrementa el contador de uso del producto

        Args:
            product_id: ID del producto

        Returns:
            True si se incrementó, False si no existe
        """
        product = self.get_by_id(product_id)
        if product:
            product.usage_count += 1
            self.db.commit()
            self.db.refresh(product)
            return True
        return False

    def code_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verifica si un código ya existe

        Args:
            code: Código a verificar
            exclude_id: ID a excluir de la búsqueda (para updates)

        Returns:
            True si existe, False si no
        """
        query = self.db.query(Product).filter(
            Product.code == code.upper(),
            Product.is_deleted == False
        )

        if exclude_id:
            query = query.filter(Product.id != exclude_id)

        return query.first() is not None
