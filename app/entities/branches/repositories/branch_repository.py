"""
Repository para la entidad Branch.

Maneja todas las operaciones de base de datos para sucursales/ubicaciones,
incluyendo búsquedas avanzadas, validaciones y carga de relaciones.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.shared.base_repository import BaseRepository
from app.entities.branches.models.branch import Branch


class BranchRepository(BaseRepository[Branch]):
    """
    Repository para Branch.

    Extiende BaseRepository con métodos específicos para gestión de sucursales.
    """

    def __init__(self, db: Session):
        """
        Inicializa el repositorio.

        IMPORTANTE: El orden es (Model, db), NO (db, Model)
        """
        super().__init__(Branch, db)

    # ==================== BÚSQUEDA POR CAMPO ÚNICO ====================

    def get_by_code(self, code: str, active_only: bool = True) -> Optional[Branch]:
        """
        Busca una sucursal por su código único.

        Args:
            code: Código de la sucursal (se normaliza a mayúsculas)
            active_only: Si solo buscar activas y no eliminadas

        Returns:
            Branch si existe, None si no
        """
        normalized_code = code.strip().upper()

        query = self.db.query(Branch).filter(
            Branch.branch_code == normalized_code
        )

        if active_only:
            query = query.filter(
                Branch.is_active == True,
                Branch.is_deleted == False
            )

        return query.first()

    # ==================== BÚSQUEDAS CON FILTROS ====================

    def get_by_company(
        self,
        company_id: int,
        active_only: bool = True
    ) -> List[Branch]:
        """
        Obtiene todas las sucursales de una empresa.

        Args:
            company_id: ID de la empresa
            active_only: Si solo retornar activas

        Returns:
            Lista de sucursales de la empresa
        """
        query = self.db.query(Branch).filter(
            Branch.company_id == company_id
        )

        if active_only:
            query = query.filter(
                Branch.is_active == True,
                Branch.is_deleted == False
            )

        return query.order_by(Branch.branch_name).all()

    def get_by_type(
        self,
        branch_type: str,
        active_only: bool = True
    ) -> List[Branch]:
        """
        Obtiene sucursales por tipo.

        Args:
            branch_type: Tipo de sucursal (warehouse, project, plant, etc.)
            active_only: Si solo retornar activas

        Returns:
            Lista de sucursales del tipo especificado
        """
        query = self.db.query(Branch).filter(
            Branch.branch_type == branch_type
        )

        if active_only:
            query = query.filter(
                Branch.is_active == True,
                Branch.is_deleted == False
            )

        return query.order_by(Branch.branch_name).all()

    # ==================== CARGA CON RELACIONES ====================

    def get_with_relations(self, branch_id: int) -> Optional[Branch]:
        """
        Obtiene una sucursal con todas sus relaciones cargadas.

        Útil para mostrar información completa en detalles.

        Args:
            branch_id: ID de la sucursal

        Returns:
            Branch con relaciones cargadas o None
        """
        return self.db.query(Branch).options(
            joinedload(Branch.company),
            joinedload(Branch.country),
            joinedload(Branch.state),
            joinedload(Branch.manager),
            joinedload(Branch.creator),
            joinedload(Branch.updater)
        ).filter(Branch.id == branch_id).first()

    # ==================== BÚSQUEDA AVANZADA ====================

    def search_branches(
        self,
        search_term: Optional[str] = None,
        branch_type: Optional[str] = None,
        company_id: Optional[int] = None,
        country_id: Optional[int] = None,
        state_id: Optional[int] = None,
        operational_status: Optional[str] = None,
        active_only: bool = True,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Búsqueda avanzada de sucursales con múltiples filtros.

        Args:
            search_term: Búsqueda en código o nombre
            branch_type: Filtrar por tipo
            company_id: Filtrar por empresa
            country_id: Filtrar por país
            state_id: Filtrar por estado
            operational_status: Filtrar por estado operativo
            active_only: Solo registros activos
            page: Número de página
            per_page: Registros por página

        Returns:
            Diccionario con datos paginados y totales
        """
        query = self.db.query(Branch)

        # Filtro de búsqueda por texto
        if search_term:
            search_pattern = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    Branch.branch_code.ilike(search_pattern),
                    Branch.branch_name.ilike(search_pattern),
                    Branch.city.ilike(search_pattern)
                )
            )

        # Filtro por tipo
        if branch_type:
            query = query.filter(Branch.branch_type == branch_type)

        # Filtro por empresa
        if company_id:
            query = query.filter(Branch.company_id == company_id)

        # Filtro por país
        if country_id:
            query = query.filter(Branch.country_id == country_id)

        # Filtro por estado
        if state_id:
            query = query.filter(Branch.state_id == state_id)

        # Filtro por estado operativo
        if operational_status:
            query = query.filter(Branch.operational_status == operational_status)

        # Filtro de activos
        if active_only:
            query = query.filter(
                Branch.is_active == True,
                Branch.is_deleted == False
            )

        # Contar total de resultados
        total = query.count()

        # Paginación
        skip = (page - 1) * per_page
        branches = query.order_by(Branch.branch_name).offset(skip).limit(per_page).all()

        # Calcular total de páginas
        total_pages = (total + per_page - 1) // per_page

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": branches
        }

    # ==================== VALIDACIONES ====================

    def verify_code_unique(
        self,
        code: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si un código de sucursal ya existe.

        Args:
            code: Código a verificar
            exclude_id: ID a excluir (para updates)

        Returns:
            True si el código está disponible, False si ya existe
        """
        normalized_code = code.strip().upper()

        query = self.db.query(Branch).filter(
            Branch.branch_code == normalized_code,
            Branch.is_deleted == False
        )

        if exclude_id:
            query = query.filter(Branch.id != exclude_id)

        return query.first() is None

    def count_by_company(self, company_id: int, active_only: bool = True) -> int:
        """
        Cuenta cuántas sucursales tiene una empresa.

        Args:
            company_id: ID de la empresa
            active_only: Solo contar activas

        Returns:
            Número de sucursales
        """
        query = self.db.query(func.count(Branch.id)).filter(
            Branch.company_id == company_id
        )

        if active_only:
            query = query.filter(
                Branch.is_active == True,
                Branch.is_deleted == False
            )

        return query.scalar()

    # ==================== OPERACIONES ESPECIALES ====================

    def get_by_location(
        self,
        country_id: int,
        state_id: Optional[int] = None,
        city: Optional[str] = None,
        active_only: bool = True
    ) -> List[Branch]:
        """
        Busca sucursales por ubicación geográfica.

        Args:
            country_id: ID del país (obligatorio)
            state_id: ID del estado (opcional)
            city: Nombre de ciudad (opcional)
            active_only: Solo activas

        Returns:
            Lista de sucursales en esa ubicación
        """
        query = self.db.query(Branch).filter(
            Branch.country_id == country_id
        )

        if state_id:
            query = query.filter(Branch.state_id == state_id)

        if city:
            query = query.filter(Branch.city.ilike(f"%{city.strip()}%"))

        if active_only:
            query = query.filter(
                Branch.is_active == True,
                Branch.is_deleted == False
            )

        return query.order_by(Branch.branch_name).all()

    def update_operational_status(
        self,
        branch_id: int,
        new_status: str,
        updated_by: int
    ) -> bool:
        """
        Actualiza solo el estado operativo de una sucursal.

        Args:
            branch_id: ID de la sucursal
            new_status: Nuevo estado (active, inactive, maintenance, closed)
            updated_by: Usuario que realiza el cambio

        Returns:
            True si se actualizó, False si no existe
        """
        branch = self.get_by_id(branch_id)
        if not branch:
            return False

        branch.operational_status = new_status
        branch.updated_by = updated_by

        self.db.commit()
        self.db.refresh(branch)

        return True
