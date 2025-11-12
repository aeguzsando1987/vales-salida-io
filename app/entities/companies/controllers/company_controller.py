"""
Controller para la entidad Company

Orquesta las operaciones y transforma entre modelos Pydantic y SQLAlchemy.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.entities.companies.services.company_service import CompanyService
from app.entities.companies.schemas.company_schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    CompanyWithRelations,
    CompanySearch,
    CompanyStatistics
)
from database import User


class CompanyController:
    """
    Controller para Company

    Transforma requests a objetos de dominio y responses a schemas Pydantic.
    """

    def __init__(self, db: Session):
        """
        Constructor del controller

        Args:
            db: Sesión de base de datos
        """
        self.db = db
        self.service = CompanyService(db)

    # ==================== OPERACIONES CRUD ====================

    def create_company(
        self,
        company_data: CompanyCreate,
        current_user: User
    ) -> CompanyResponse:
        """
        Crea una nueva empresa

        Args:
            company_data: Datos de la empresa
            current_user: Usuario autenticado

        Returns:
            CompanyResponse con la empresa creada
        """
        # Convertir Pydantic a dict
        data_dict = company_data.model_dump()

        # Crear empresa
        new_company = self.service.create_company(
            company_data=data_dict,
            created_by_user_id=current_user.id
        )

        return CompanyResponse.model_validate(new_company)

    def get_company(self, company_id: int) -> CompanyResponse:
        """
        Obtiene una empresa por ID

        Args:
            company_id: ID de la empresa

        Returns:
            CompanyResponse
        """
        company = self.service.get_company_by_id(company_id)
        return CompanyResponse.model_validate(company)

    def get_company_with_relations(self, company_id: int) -> CompanyWithRelations:
        """
        Obtiene una empresa con relaciones

        Args:
            company_id: ID de la empresa

        Returns:
            CompanyWithRelations
        """
        company = self.service.get_company_with_relations(company_id)

        # Construir respuesta con relaciones
        response_data = CompanyResponse.model_validate(company).model_dump()

        # Agregar nombres de relaciones
        if company.country:
            response_data["country_name"] = company.country.name

        if company.state:
            response_data["state_name"] = company.state.name

        if company.creator:
            response_data["creator_name"] = company.creator.name

        if company.updater:
            response_data["updater_name"] = company.updater.name

        return CompanyWithRelations(**response_data)

    def get_all_companies(
        self,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True
    ) -> CompanyListResponse:
        """
        Obtiene lista de empresas con paginación

        Args:
            page: Número de página
            per_page: Registros por página
            active_only: Solo activas

        Returns:
            CompanyListResponse con lista paginada
        """
        skip = (page - 1) * per_page
        companies = self.service.get_all_companies(skip, per_page, active_only)
        total = self.service.count_companies(active_only)

        total_pages = (total + per_page - 1) // per_page

        return CompanyListResponse(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            data=[CompanyResponse.model_validate(c) for c in companies]
        )

    def update_company(
        self,
        company_id: int,
        company_data: CompanyUpdate,
        current_user: User
    ) -> CompanyResponse:
        """
        Actualiza una empresa

        Args:
            company_id: ID de la empresa
            company_data: Datos a actualizar
            current_user: Usuario autenticado

        Returns:
            CompanyResponse actualizada
        """
        # Convertir a dict excluyendo campos no seteados
        data_dict = company_data.model_dump(exclude_unset=True)

        # Actualizar
        updated_company = self.service.update_company(
            company_id=company_id,
            company_data=data_dict,
            updated_by_user_id=current_user.id
        )

        return CompanyResponse.model_validate(updated_company)

    def delete_company(
        self,
        company_id: int,
        current_user: User,
        hard_delete: bool = False
    ) -> dict:
        """
        Elimina una empresa

        Args:
            company_id: ID de la empresa
            current_user: Usuario autenticado
            hard_delete: Si es True, elimina físicamente

        Returns:
            Mensaje de confirmación
        """
        self.service.delete_company(
            company_id=company_id,
            deleted_by_user_id=current_user.id,
            soft_delete=not hard_delete
        )

        return {
            "message": "Empresa eliminada exitosamente",
            "company_id": company_id,
            "deleted_by": current_user.id
        }

    # ==================== BÚSQUEDAS ====================

    def get_company_by_tin(self, tin: str) -> CompanyResponse:
        """
        Busca empresa por TIN

        Args:
            tin: Tax Identification Number

        Returns:
            CompanyResponse
        """
        company = self.service.get_company_by_tin(tin)
        return CompanyResponse.model_validate(company)

    def get_companies_by_country(
        self,
        country_id: int,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True
    ) -> CompanyListResponse:
        """
        Obtiene empresas de un país

        Args:
            country_id: ID del país
            page: Número de página
            per_page: Registros por página
            active_only: Solo activas

        Returns:
            CompanyListResponse
        """
        skip = (page - 1) * per_page
        companies = self.service.get_companies_by_country(
            country_id, skip, per_page, active_only
        )

        # Contar total en ese país
        total = len(self.service.get_companies_by_country(
            country_id, 0, 999999, active_only
        ))

        total_pages = (total + per_page - 1) // per_page

        return CompanyListResponse(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            data=[CompanyResponse.model_validate(c) for c in companies]
        )

    def get_companies_by_state(
        self,
        state_id: int,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True
    ) -> CompanyListResponse:
        """
        Obtiene empresas de un estado

        Args:
            state_id: ID del estado
            page: Número de página
            per_page: Registros por página
            active_only: Solo activas

        Returns:
            CompanyListResponse
        """
        skip = (page - 1) * per_page
        companies = self.service.get_companies_by_state(
            state_id, skip, per_page, active_only
        )

        # Contar total en ese estado
        total = len(self.service.get_companies_by_state(
            state_id, 0, 999999, active_only
        ))

        total_pages = (total + per_page - 1) // per_page

        return CompanyListResponse(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            data=[CompanyResponse.model_validate(c) for c in companies]
        )

    def search_companies(
        self,
        search_data: CompanySearch,
        page: int = 1,
        per_page: int = 20
    ) -> CompanyListResponse:
        """
        Búsqueda avanzada de empresas

        Args:
            search_data: Criterios de búsqueda
            page: Número de página
            per_page: Registros por página

        Returns:
            CompanyListResponse
        """
        skip = (page - 1) * per_page

        companies = self.service.search_companies(
            search_term=search_data.search_term,
            country_id=search_data.country_id,
            state_id=search_data.state_id,
            status=search_data.status.value if search_data.status else None,
            tax_system=search_data.tax_system.value if search_data.tax_system else None,
            skip=skip,
            limit=per_page
        )

        # Contar total con mismos filtros
        all_results = self.service.search_companies(
            search_term=search_data.search_term,
            country_id=search_data.country_id,
            state_id=search_data.state_id,
            status=search_data.status.value if search_data.status else None,
            tax_system=search_data.tax_system.value if search_data.tax_system else None,
            skip=0,
            limit=999999
        )
        total = len(all_results)

        total_pages = (total + per_page - 1) // per_page

        return CompanyListResponse(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            data=[CompanyResponse.model_validate(c) for c in companies]
        )

    def get_statistics(self) -> CompanyStatistics:
        """
        Obtiene estadísticas de empresas

        Returns:
            CompanyStatistics
        """
        stats = self.service.get_statistics()
        return CompanyStatistics(**stats)

    # ==================== OPERACIONES DE ESTADO ====================

    def activate_company(self, company_id: int, current_user: User) -> CompanyResponse:
        """
        Activa una empresa

        Args:
            company_id: ID de la empresa
            current_user: Usuario autenticado

        Returns:
            CompanyResponse activada
        """
        company = self.service.activate_company(company_id, current_user.id)
        return CompanyResponse.model_validate(company)

    def suspend_company(self, company_id: int, current_user: User) -> CompanyResponse:
        """
        Suspende una empresa

        Args:
            company_id: ID de la empresa
            current_user: Usuario autenticado

        Returns:
            CompanyResponse suspendida
        """
        company = self.service.suspend_company(company_id, current_user.id)
        return CompanyResponse.model_validate(company)

    def deactivate_company(self, company_id: int, current_user: User) -> CompanyResponse:
        """
        Desactiva una empresa

        Args:
            company_id: ID de la empresa
            current_user: Usuario autenticado

        Returns:
            CompanyResponse desactivada
        """
        company = self.service.deactivate_company(company_id, current_user.id)
        return CompanyResponse.model_validate(company)
