"""
Repository para la entidad Company

Maneja todas las operaciones de base de datos para empresas.
Extiende BaseRepository para reutilizar operaciones CRUD comunes.
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from app.shared.base_repository import BaseRepository
from app.entities.companies.models.company import Company
from app.entities.countries.models.country import Country
from app.entities.states.models.state import State


class CompanyRepository(BaseRepository[Company]):
    """
    Repository para Company

    Hereda todos los métodos CRUD básicos de BaseRepository:
    - create, get_by_id, get_all, update, delete, exists, count, etc.

    Agrega métodos específicos para búsquedas y queries complejas de empresas.
    """

    def __init__(self, db: Session):
        """
        Constructor del repository

        IMPORTANTE: El orden de argumentos es (Model, db)
        """
        super().__init__(Company, db)

    # ==================== MÉTODOS ESPECÍFICOS DE COMPANY ====================

    def get_by_tin(self, tin: str) -> Optional[Company]:
        """
        Busca una empresa por su Tax Identification Number (TIN)

        Args:
            tin: Número de identificación fiscal

        Returns:
            Company si existe, None si no
        """
        return self.db.query(Company).filter(
            Company.tin == tin.upper(),
            Company.is_deleted == False
        ).first()

    def get_by_email(self, email: str) -> Optional[Company]:
        """
        Busca una empresa por email

        Args:
            email: Correo electrónico de la empresa

        Returns:
            Company si existe, None si no
        """
        return self.db.query(Company).filter(
            Company.email == email.lower(),
            Company.is_deleted == False
        ).first()

    def get_with_relations(self, company_id: int) -> Optional[Company]:
        """
        Obtiene una empresa con sus relaciones cargadas (country, state)

        Args:
            company_id: ID de la empresa

        Returns:
            Company con relaciones o None
        """
        return self.db.query(Company).options(
            joinedload(Company.country),
            joinedload(Company.state),
            joinedload(Company.creator),
            joinedload(Company.updater)
        ).filter(
            Company.id == company_id,
            Company.is_deleted == False
        ).first()

    def get_by_country(
        self,
        country_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Company]:
        """
        Obtiene empresas de un país específico

        Args:
            country_id: ID del país
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo empresas activas

        Returns:
            Lista de empresas
        """
        query = self.db.query(Company).filter(
            Company.country_id == country_id,
            Company.is_deleted == False
        )

        if active_only:
            query = query.filter(Company.is_active == True)

        return query.offset(skip).limit(limit).all()

    def get_by_state(
        self,
        state_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Company]:
        """
        Obtiene empresas de un estado específico

        Args:
            state_id: ID del estado
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo empresas activas

        Returns:
            Lista de empresas
        """
        query = self.db.query(Company).filter(
            Company.state_id == state_id,
            Company.is_deleted == False
        )

        if active_only:
            query = query.filter(Company.is_active == True)

        return query.offset(skip).limit(limit).all()

    def get_by_tax_system(
        self,
        tax_system: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Company]:
        """
        Obtiene empresas por sistema fiscal

        Args:
            tax_system: Tipo de sistema fiscal (RFC, EIN, NIF, etc.)
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo empresas activas

        Returns:
            Lista de empresas
        """
        query = self.db.query(Company).filter(
            Company.tax_system == tax_system.upper(),
            Company.is_deleted == False
        )

        if active_only:
            query = query.filter(Company.is_active == True)

        return query.offset(skip).limit(limit).all()

    def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Company]:
        """
        Obtiene empresas por estado (active, inactive, suspended)

        Args:
            status: Estado de la empresa
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de empresas
        """
        return self.db.query(Company).filter(
            Company.status == status.lower(),
            Company.is_deleted == False
        ).offset(skip).limit(limit).all()

    def search_companies(
        self,
        search_term: str,
        country_id: Optional[int] = None,
        state_id: Optional[int] = None,
        status: Optional[str] = None,
        tax_system: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Company]:
        """
        Búsqueda avanzada de empresas

        Args:
            search_term: Término a buscar en nombre, TIN, email
            country_id: Filtrar por país (opcional)
            state_id: Filtrar por estado (opcional)
            status: Filtrar por estado (opcional)
            tax_system: Filtrar por sistema fiscal (opcional)
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de empresas que coinciden
        """
        query = self.db.query(Company).filter(Company.is_deleted == False)

        # Búsqueda por término
        if search_term:
            search_filter = or_(
                Company.company_name.ilike(f"%{search_term}%"),
                Company.legal_name.ilike(f"%{search_term}%"),
                Company.tin.ilike(f"%{search_term}%"),
                Company.email.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        # Filtros adicionales
        if country_id:
            query = query.filter(Company.country_id == country_id)

        if state_id:
            query = query.filter(Company.state_id == state_id)

        if status:
            query = query.filter(Company.status == status.lower())

        if tax_system:
            query = query.filter(Company.tax_system == tax_system.upper())

        return query.offset(skip).limit(limit).all()

    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas de empresas

        Returns:
            Diccionario con estadísticas
        """
        # Total de empresas
        total = self.count(active_only=False)
        active = self.db.query(Company).filter(
            Company.is_deleted == False,
            Company.status == "active"
        ).count()
        inactive = self.db.query(Company).filter(
            Company.is_deleted == False,
            Company.status == "inactive"
        ).count()
        suspended = self.db.query(Company).filter(
            Company.is_deleted == False,
            Company.status == "suspended"
        ).count()

        # Empresas por país
        companies_by_country = {}
        country_stats = self.db.query(
            Country.name,
            func.count(Company.id).label('count')
        ).join(
            Company, Company.country_id == Country.id
        ).filter(
            Company.is_deleted == False
        ).group_by(Country.name).all()

        for country_name, count in country_stats:
            companies_by_country[country_name] = count

        # Empresas por sistema fiscal
        companies_by_tax_system = {}
        tax_stats = self.db.query(
            Company.tax_system,
            func.count(Company.id).label('count')
        ).filter(
            Company.is_deleted == False
        ).group_by(Company.tax_system).all()

        for tax_system, count in tax_stats:
            companies_by_tax_system[tax_system] = count

        return {
            "total_companies": total,
            "active_companies": active,
            "inactive_companies": inactive,
            "suspended_companies": suspended,
            "companies_by_country": companies_by_country,
            "companies_by_tax_system": companies_by_tax_system
        }

    def verify_tin_unique(self, tin: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verifica si un TIN ya existe en la base de datos

        Args:
            tin: Tax Identification Number a verificar
            exclude_id: ID de empresa a excluir (útil en updates)

        Returns:
            True si el TIN está disponible, False si ya existe
        """
        query = self.db.query(Company).filter(
            Company.tin == tin.upper(),
            Company.is_deleted == False
        )

        if exclude_id:
            query = query.filter(Company.id != exclude_id)

        return query.first() is None
