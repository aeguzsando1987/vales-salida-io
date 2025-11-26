"""
VoucherDetail Controller
Orquestación de requests/responses HTTP
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from app.entities.voucher_details.services.voucher_detail_service import VoucherDetailService
from app.entities.voucher_details.schemas.voucher_detail_schemas import (
    VoucherDetailCreate,
    VoucherDetailUpdate,
    VoucherDetailResponse,
    VoucherDetailWithProduct,
    ProductMatchResponse,
    ProductMatchesFound
)


class VoucherDetailController:
    """
    Controlador de VoucherDetail.
    Maneja requests HTTP y delega lógica al Service.
    """

    def __init__(self, db: Session):
        self.service = VoucherDetailService(db)

    def create(
        self,
        detail_data: VoucherDetailCreate,
        current_user_id: Optional[int] = None,
        skip_similarity_search: bool = False
    ) -> Union[VoucherDetailWithProduct, ProductMatchesFound]:
        """
        Crea un detalle de vale.

        Puede devolver:
        - VoucherDetailWithProduct: Si se creó exitosamente
        - ProductMatchesFound: Si se encontraron productos similares para selección

        Args:
            detail_data: Datos del detalle
            current_user_id: ID del usuario actual
            skip_similarity_search: Si True, salta búsqueda y auto-crea directo

        Returns:
            VoucherDetailWithProduct O ProductMatchesFound
        """
        return self.service.create(
            detail_data,
            created_by_id=current_user_id,
            skip_similarity_search=skip_similarity_search
        )

    def get_by_id(self, detail_id: int) -> VoucherDetailResponse:
        """Obtiene un detalle por ID"""
        detail = self.service.get_by_id(detail_id)
        return VoucherDetailResponse.model_validate(detail)

    def get_by_voucher(self, voucher_id: int) -> List[VoucherDetailWithProduct]:
        """Obtiene todas las líneas de un vale"""
        return self.service.get_by_voucher(voucher_id)

    def update(
        self,
        detail_id: int,
        detail_data: VoucherDetailUpdate,
        current_user_id: Optional[int] = None
    ) -> VoucherDetailWithProduct:
        """Actualiza un detalle"""
        return self.service.update(
            detail_id,
            detail_data,
            updated_by_id=current_user_id
        )

    def delete(self, detail_id: int, current_user_id: Optional[int] = None):
        """Elimina (soft delete) un detalle"""
        self.service.delete(detail_id, deleted_by_id=current_user_id)
        return {"message": "Detalle eliminado exitosamente"}

    def search_products(self, search_term: str, limit: int = 10) -> List[ProductMatchResponse]:
        """
        Busca productos por similitud.
        Útil para autocomplete en frontend.

        Args:
            search_term: Término de búsqueda
            limit: Máximo de resultados

        Returns:
            Lista de productos similares
        """
        return self.service.search_products(search_term, limit)
