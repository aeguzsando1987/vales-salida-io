"""
VoucherDetail Repository
Acceso a datos con queries especializadas
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional

from app.shared.base_repository import BaseRepository
from app.entities.voucher_details.models.voucher_detail import VoucherDetail
from app.entities.products.models.product import Product


class VoucherDetailRepository(BaseRepository[VoucherDetail]):
    """
    Repositorio para VoucherDetail con queries especializadas.

    Métodos adicionales:
    - count_by_voucher: Cuenta líneas de un vale
    - get_by_voucher: Obtiene todas las líneas de un vale
    - get_next_line_number: Obtiene siguiente número de línea disponible
    - search_similar_products: Busca productos por similitud
    - exists_line_number: Verifica si línea ya existe en vale
    """

    def __init__(self, db: Session):
        super().__init__(VoucherDetail, db)

    def count_by_voucher(self, voucher_id: int, active_only: bool = True) -> int:
        """
        Cuenta las líneas de detalle de un vale.

        Args:
            voucher_id: ID del vale
            active_only: Solo contar activas (no eliminadas)

        Returns:
            Número de líneas
        """
        query = self.db.query(func.count(VoucherDetail.id)).filter(
            VoucherDetail.voucher_id == voucher_id
        )

        if active_only:
            query = query.filter(
                VoucherDetail.is_active == True,
                VoucherDetail.is_deleted == False
            )

        return query.scalar() or 0

    def get_by_voucher(
        self,
        voucher_id: int,
        active_only: bool = True,
        order_by_line: bool = True
    ) -> List[VoucherDetail]:
        """
        Obtiene todas las líneas de detalle de un vale.

        Args:
            voucher_id: ID del vale
            active_only: Solo líneas activas
            order_by_line: Ordenar por line_number

        Returns:
            Lista de VoucherDetail
        """
        query = self.db.query(VoucherDetail).filter(
            VoucherDetail.voucher_id == voucher_id
        )

        if active_only:
            query = query.filter(
                VoucherDetail.is_active == True,
                VoucherDetail.is_deleted == False
            )

        if order_by_line:
            query = query.order_by(VoucherDetail.line_number)

        return query.all()

    def get_next_line_number(self, voucher_id: int) -> int:
        """
        Obtiene el siguiente número de línea disponible para un vale.

        Args:
            voucher_id: ID del vale

        Returns:
            Siguiente número de línea (1-20)
        """
        last_line = self.db.query(func.max(VoucherDetail.line_number)).filter(
            VoucherDetail.voucher_id == voucher_id,
            VoucherDetail.is_deleted == False
        ).scalar()

        return (last_line or 0) + 1

    def exists_line_number(self, voucher_id: int, line_number: int, exclude_id: Optional[int] = None) -> bool:
        """
        Verifica si un número de línea ya existe en un vale.

        Args:
            voucher_id: ID del vale
            line_number: Número de línea a verificar
            exclude_id: ID de detalle a excluir (para updates)

        Returns:
            True si existe, False si no
        """
        query = self.db.query(VoucherDetail).filter(
            VoucherDetail.voucher_id == voucher_id,
            VoucherDetail.line_number == line_number,
            VoucherDetail.is_deleted == False
        )

        if exclude_id:
            query = query.filter(VoucherDetail.id != exclude_id)

        return query.first() is not None

    def search_similar_products(
        self,
        search_term: str,
        limit: int = 10,
        active_only: bool = True
    ) -> List[Product]:
        """
        Busca productos por similitud en nombre.

        Usa PostgreSQL ILIKE para búsqueda case-insensitive.
        Ordena por usage_count DESC para mostrar más usados primero.

        Args:
            search_term: Término de búsqueda
            limit: Número máximo de resultados
            active_only: Solo productos activos

        Returns:
            Lista de productos similares
        """
        # Normalizar término de búsqueda
        search_term = search_term.strip()
        if not search_term:
            return []

        # Construir patrón ILIKE
        pattern = f"%{search_term}%"

        query = self.db.query(Product).filter(
            or_(
                func.lower(Product.name).like(func.lower(pattern)),
                func.lower(Product.description).like(func.lower(pattern)),
                func.lower(Product.code).like(func.lower(pattern))
            )
        )

        if active_only:
            query = query.filter(
                Product.is_active == True,
                Product.is_deleted == False
            )

        # Ordenar por usage_count (más usados primero)
        query = query.order_by(Product.usage_count.desc(), Product.name)

        return query.limit(limit).all()

    def get_by_voucher_with_products(self, voucher_id: int) -> List[VoucherDetail]:
        """
        Obtiene líneas de detalle con información de productos (JOIN).

        Args:
            voucher_id: ID del vale

        Returns:
            Lista de VoucherDetail con productos cargados
        """
        return self.db.query(VoucherDetail).filter(
            VoucherDetail.voucher_id == voucher_id,
            VoucherDetail.is_active == True,
            VoucherDetail.is_deleted == False
        ).order_by(VoucherDetail.line_number).all()

    def delete_all_by_voucher(self, voucher_id: int, soft_delete: bool = True) -> int:
        """
        Elimina todas las líneas de un vale (usado para cascada manual si es necesario).

        Args:
            voucher_id: ID del vale
            soft_delete: Soft delete o hard delete

        Returns:
            Número de líneas eliminadas
        """
        details = self.get_by_voucher(voucher_id, active_only=True)

        for detail in details:
            if soft_delete:
                self.delete(detail.id, soft_delete=True)
            else:
                self.db.delete(detail)

        self.db.commit()
        return len(details)
