"""
Service para la entidad Company

Contiene toda la lógica de negocio para operaciones con empresas.
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from app.entities.companies.models.company import Company
from app.entities.companies.repositories.company_repository import CompanyRepository
from app.entities.countries.models.country import Country
from app.entities.states.models.state import State
from app.shared.exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    EntityValidationError,
    BusinessRuleError,
    DataIntegrityError
)


class CompanyService:
    """
    Service para Company

    Maneja validaciones de negocio, transacciones y lógica compleja.
    """

    def __init__(self, db: Session):
        """
        Constructor del service

        Args:
            db: Sesión de base de datos
        """
        self.db = db
        self.repository = CompanyRepository(db)

    # ==================== OPERACIONES CRUD ====================

    def create_company(
        self,
        company_data: Dict,
        created_by_user_id: Optional[int] = None
    ) -> Company:
        """
        Crea una nueva empresa

        Args:
            company_data: Datos de la empresa
            created_by_user_id: ID del usuario que crea

        Returns:
            Company creada

        Raises:
            EntityAlreadyExistsError: Si el TIN ya existe
            EntityValidationError: Si hay errores de validación
            DataIntegrityError: Si hay problemas de integridad
        """
        # Validar que el TIN sea único
        tin = company_data.get("tin", "").upper()
        if not self.repository.verify_tin_unique(tin):
            raise EntityAlreadyExistsError(
                entity_name="Company",
                field="tin",
                value=tin
            )

        # Validar que el país exista
        country_id = company_data.get("country_id")
        country = self.db.query(Country).filter(
            Country.id == country_id,
            Country.is_deleted == False
        ).first()

        if not country:
            raise EntityValidationError(
                entity_name="Company",
                errors={"country_id": f"País con ID {country_id} no existe"}
            )

        # Validar que el estado exista y pertenezca al país
        state_id = company_data.get("state_id")
        if state_id:
            state = self.db.query(State).filter(
                State.id == state_id,
                State.is_deleted == False
            ).first()

            if not state:
                raise EntityValidationError(
                    entity_name="Company",
                    errors={"state_id": f"Estado con ID {state_id} no existe"}
                )

            if state.country_id != country_id:
                raise BusinessRuleError(
                    message="El estado no pertenece al país seleccionado",
                    details={
                        "state_id": state_id,
                        "state_country_id": state.country_id,
                        "selected_country_id": country_id
                    }
                )

        # Agregar campos de auditoría
        company_data["created_by"] = created_by_user_id
        company_data["created_at"] = datetime.utcnow()

        # Crear empresa
        try:
            new_company = self.repository.create(company_data)
            self.db.commit()
            self.db.refresh(new_company)
            return new_company
        except Exception as e:
            self.db.rollback()
            raise DataIntegrityError(
                message="Error al crear empresa",
                details={"error": str(e)}
            )

    def get_company_by_id(self, company_id: int) -> Company:
        """
        Obtiene una empresa por ID

        Args:
            company_id: ID de la empresa

        Returns:
            Company encontrada

        Raises:
            EntityNotFoundError: Si no existe la empresa
        """
        company = self.repository.get_by_id(company_id)
        if not company:
            raise EntityNotFoundError("Company", company_id)
        return company

    def get_company_with_relations(self, company_id: int) -> Company:
        """
        Obtiene una empresa con relaciones cargadas

        Args:
            company_id: ID de la empresa

        Returns:
            Company con relaciones

        Raises:
            EntityNotFoundError: Si no existe
        """
        company = self.repository.get_with_relations(company_id)
        if not company:
            raise EntityNotFoundError("Company", company_id)
        return company

    def get_all_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Company]:
        """
        Obtiene lista de empresas con paginación

        Args:
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activas

        Returns:
            Lista de empresas
        """
        return self.repository.get_all(skip, limit, active_only)

    def update_company(
        self,
        company_id: int,
        company_data: Dict,
        updated_by_user_id: Optional[int] = None
    ) -> Company:
        """
        Actualiza una empresa

        Args:
            company_id: ID de la empresa
            company_data: Datos a actualizar
            updated_by_user_id: ID del usuario que actualiza

        Returns:
            Company actualizada

        Raises:
            EntityNotFoundError: Si no existe
            EntityAlreadyExistsError: Si el nuevo TIN ya existe
            EntityValidationError: Si hay errores de validación
        """
        # Verificar que exista
        company = self.get_company_by_id(company_id)

        # Si se actualiza TIN, validar que sea único
        if "tin" in company_data:
            tin = company_data["tin"].upper()
            if tin != company.tin:
                if not self.repository.verify_tin_unique(tin, exclude_id=company_id):
                    raise EntityAlreadyExistsError(
                        entity_name="Company",
                        field="tin",
                        value=tin
                    )

        # Si se actualiza país, validar
        if "country_id" in company_data:
            country_id = company_data["country_id"]
            country = self.db.query(Country).filter(
                Country.id == country_id,
                Country.is_deleted == False
            ).first()

            if not country:
                raise EntityValidationError(
                    entity_name="Company",
                    errors={"country_id": f"País con ID {country_id} no existe"}
                )

        # Si se actualiza estado, validar
        if "state_id" in company_data:
            state_id = company_data["state_id"]
            if state_id:
                state = self.db.query(State).filter(
                    State.id == state_id,
                    State.is_deleted == False
                ).first()

                if not state:
                    raise EntityValidationError(
                        entity_name="Company",
                        errors={"state_id": f"Estado con ID {state_id} no existe"}
                    )

                # Validar coherencia con país
                country_id = company_data.get("country_id", company.country_id)
                if state.country_id != country_id:
                    raise BusinessRuleError(
                        message="El estado no pertenece al país seleccionado",
                        details={
                            "state_id": state_id,
                            "state_country_id": state.country_id,
                            "selected_country_id": country_id
                        }
                    )

        # Agregar campos de auditoría
        company_data["updated_by"] = updated_by_user_id
        company_data["updated_at"] = datetime.utcnow()

        # Actualizar
        try:
            updated_company = self.repository.update(company_id, company_data)
            self.db.commit()
            self.db.refresh(updated_company)
            return updated_company
        except Exception as e:
            self.db.rollback()
            raise DataIntegrityError(
                message="Error al actualizar empresa",
                details={"error": str(e)}
            )

    def delete_company(
        self,
        company_id: int,
        deleted_by_user_id: Optional[int] = None,
        soft_delete: bool = True
    ) -> bool:
        """
        Elimina una empresa (soft delete por defecto)

        Args:
            company_id: ID de la empresa
            deleted_by_user_id: ID del usuario que elimina
            soft_delete: Si es True, solo marca como eliminado

        Returns:
            True si se eliminó

        Raises:
            EntityNotFoundError: Si no existe
        """
        # Verificar que exista
        company = self.get_company_by_id(company_id)

        if soft_delete:
            # Soft delete
            update_data = {
                "is_deleted": True,
                "is_active": False,
                "deleted_at": datetime.utcnow(),
                "deleted_by": deleted_by_user_id
            }
            self.repository.update(company_id, update_data)
            self.db.commit()
        else:
            # Hard delete
            self.repository.delete(company_id, soft_delete=False)
            self.db.commit()

        return True

    # ==================== BÚSQUEDAS ESPECÍFICAS ====================

    def get_company_by_tin(self, tin: str) -> Company:
        """
        Busca empresa por TIN

        Args:
            tin: Tax Identification Number

        Returns:
            Company encontrada

        Raises:
            EntityNotFoundError: Si no existe
        """
        company = self.repository.get_by_tin(tin)
        if not company:
            raise EntityNotFoundError("Company", f"TIN={tin}")
        return company

    def get_companies_by_country(
        self,
        country_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Company]:
        """
        Obtiene empresas de un país

        Args:
            country_id: ID del país
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activas

        Returns:
            Lista de empresas
        """
        return self.repository.get_by_country(country_id, skip, limit, active_only)

    def get_companies_by_state(
        self,
        state_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Company]:
        """
        Obtiene empresas de un estado

        Args:
            state_id: ID del estado
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activas

        Returns:
            Lista de empresas
        """
        return self.repository.get_by_state(state_id, skip, limit, active_only)

    def search_companies(
        self,
        search_term: Optional[str] = None,
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
            search_term: Término de búsqueda
            country_id: Filtro por país
            state_id: Filtro por estado
            status: Filtro por estado
            tax_system: Filtro por sistema fiscal
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de empresas que coinciden
        """
        return self.repository.search_companies(
            search_term=search_term,
            country_id=country_id,
            state_id=state_id,
            status=status,
            tax_system=tax_system,
            skip=skip,
            limit=limit
        )

    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas de empresas

        Returns:
            Diccionario con estadísticas
        """
        return self.repository.get_statistics()

    def count_companies(self, active_only: bool = True) -> int:
        """
        Cuenta el total de empresas

        Args:
            active_only: Solo activas

        Returns:
            Número de empresas
        """
        return self.repository.count(active_only)

    # ==================== OPERACIONES DE ESTADO ====================

    def activate_company(self, company_id: int, user_id: Optional[int] = None) -> Company:
        """
        Activa una empresa

        Args:
            company_id: ID de la empresa
            user_id: ID del usuario que activa

        Returns:
            Company activada
        """
        return self.update_company(
            company_id,
            {"status": "active", "is_active": True},
            user_id
        )

    def suspend_company(self, company_id: int, user_id: Optional[int] = None) -> Company:
        """
        Suspende una empresa

        Args:
            company_id: ID de la empresa
            user_id: ID del usuario que suspende

        Returns:
            Company suspendida
        """
        return self.update_company(
            company_id,
            {"status": "suspended"},
            user_id
        )

    def deactivate_company(self, company_id: int, user_id: Optional[int] = None) -> Company:
        """
        Desactiva una empresa

        Args:
            company_id: ID de la empresa
            user_id: ID del usuario que desactiva

        Returns:
            Company desactivada
        """
        return self.update_company(
            company_id,
            {"status": "inactive", "is_active": False},
            user_id
        )
