"""
Repository para Voucher

Hereda de BaseRepository y agrega métodos específicos para vales.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import extract, func, and_, or_
from datetime import date, datetime

from app.shared.base_repository import BaseRepository
from app.entities.vouchers.models.voucher import Voucher, VoucherStatusEnum, VoucherTypeEnum


class VoucherRepository(BaseRepository[Voucher]):
    """
    Repository para Voucher

    Hereda CRUD básico de BaseRepository y agrega queries específicas.
    """

    def __init__(self, db: Session):
        super().__init__(Voucher, db)

    # ==================== BÚSQUEDAS ESPECÍFICAS ====================

    def find_by_folio(self, folio: str) -> Optional[Voucher]:
        """
        Busca un voucher por su folio único

        Args:
            folio: Folio del voucher

        Returns:
            Voucher si existe, None si no
        """
        return self.db.query(Voucher).filter(
            Voucher.folio == folio,
            Voucher.is_deleted == False
        ).first()

    def find_by_company(
        self,
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Voucher]:
        """
        Busca vouchers por empresa

        Args:
            company_id: ID de la empresa
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos

        Returns:
            Lista de vouchers
        """
        query = self.db.query(Voucher).filter(
            Voucher.company_id == company_id,
            Voucher.is_deleted == False
        )

        if active_only:
            query = query.filter(Voucher.is_active == True)

        return query.order_by(Voucher.created_at.desc()).offset(skip).limit(limit).all()

    def find_by_status(
        self,
        status: VoucherStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Voucher]:
        """
        Busca vouchers por estado

        Args:
            status: Estado del voucher
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de vouchers
        """
        return self.db.query(Voucher).filter(
            Voucher.status == status,
            Voucher.is_deleted == False
        ).order_by(Voucher.created_at.desc()).offset(skip).limit(limit).all()

    def find_by_type(
        self,
        voucher_type: VoucherTypeEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Voucher]:
        """
        Busca vouchers por tipo (ENTRY/EXIT)

        Args:
            voucher_type: Tipo de voucher
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de vouchers
        """
        return self.db.query(Voucher).filter(
            Voucher.voucher_type == voucher_type,
            Voucher.is_deleted == False
        ).order_by(Voucher.created_at.desc()).offset(skip).limit(limit).all()

    # ==================== GENERACIÓN DE FOLIOS ====================

    def get_last_sequence_for_folio(
        self,
        company_id: int,
        voucher_type: VoucherTypeEnum,
        year: int
    ) -> int:
        """
        Obtiene la última secuencia usada para generar folios

        Args:
            company_id: ID de la empresa
            voucher_type: Tipo de voucher
            year: Año

        Returns:
            Última secuencia (0 si no existe ninguna)
        """
        count = self.db.query(func.count(Voucher.id)).filter(
            Voucher.company_id == company_id,
            Voucher.voucher_type == voucher_type,
            extract('year', Voucher.created_at) == year
        ).scalar()

        return count or 0

    # ==================== VALES VENCIDOS ====================

    def find_overdue_vouchers(self) -> List[Voucher]:
        """
        Encuentra vales que deberían estar vencidos

        Busca vales con:
        - status = IN_TRANSIT
        - with_return = True
        - estimated_return_date < hoy

        Returns:
            Lista de vouchers vencidos
        """
        today = date.today()

        return self.db.query(Voucher).filter(
            Voucher.status == VoucherStatusEnum.IN_TRANSIT,
            Voucher.with_return == True,
            Voucher.estimated_return_date < today,
            Voucher.is_deleted == False
        ).all()

    # ==================== ESTADÍSTICAS ====================

    def get_statistics(self, company_id: Optional[int] = None) -> dict:
        """
        Obtiene estadísticas de vouchers

        Args:
            company_id: Filtrar por empresa (opcional)

        Returns:
            Dict con estadísticas
        """
        base_query = self.db.query(Voucher).filter(
            Voucher.is_deleted == False
        )

        if company_id:
            base_query = base_query.filter(Voucher.company_id == company_id)

        # Total
        total = base_query.count()

        # Por estado
        by_status = {}
        for status in VoucherStatusEnum:
            count = base_query.filter(Voucher.status == status).count()
            by_status[status.value] = count

        # Por tipo
        by_type = {}
        for vtype in VoucherTypeEnum:
            count = base_query.filter(Voucher.voucher_type == vtype).count()
            by_type[vtype.value] = count

        return {
            "total_vouchers": total,
            "by_status": by_status,
            "by_type": by_type,
            "pending_approval": by_status.get(VoucherStatusEnum.PENDING.value, 0),
            "overdue": by_status.get(VoucherStatusEnum.OVERDUE.value, 0),
            "in_transit": by_status.get(VoucherStatusEnum.IN_TRANSIT.value, 0)
        }

    # ==================== BÚSQUEDA AVANZADA ====================

    def search_vouchers(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[int] = None,
        status: Optional[VoucherStatusEnum] = None,
        voucher_type: Optional[VoucherTypeEnum] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50
    ) -> List[Voucher]:
        """
        Búsqueda avanzada de vouchers

        Args:
            search_term: Término de búsqueda (en folio o notas)
            company_id: Filtrar por empresa
            status: Filtrar por estado
            voucher_type: Filtrar por tipo
            from_date: Fecha desde
            to_date: Fecha hasta
            limit: Máximo de resultados

        Returns:
            Lista de vouchers
        """
        query = self.db.query(Voucher).filter(
            Voucher.is_deleted == False
        )

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Voucher.folio.ilike(search_pattern),
                    Voucher.notes.ilike(search_pattern)
                )
            )

        if company_id:
            query = query.filter(Voucher.company_id == company_id)

        if status:
            query = query.filter(Voucher.status == status)

        if voucher_type:
            query = query.filter(Voucher.voucher_type == voucher_type)

        if from_date:
            query = query.filter(Voucher.created_at >= from_date)

        if to_date:
            query = query.filter(Voucher.created_at <= to_date)

        return query.order_by(Voucher.created_at.desc()).limit(limit).all()
