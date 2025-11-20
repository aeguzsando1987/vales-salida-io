"""
Service para la entidad Branch.

Contiene toda la lógica de negocio, validaciones y orquestación
de operaciones para sucursales/ubicaciones.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.entities.branches.models.branch import Branch
from app.entities.branches.repositories.branch_repository import BranchRepository
from app.entities.branches.schemas.branch_schemas import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchWithRelations,
    BranchSearch
)

from app.shared.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    BusinessRuleError
)


class BranchService:
    """
    Service para Branch.

    Maneja lógica de negocio, validaciones complejas y transformaciones.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con su repositorio.

        Args:
            db: Sesión de base de datos
        """
        self.db = db
        self.repository = BranchRepository(db)

    # ==================== OPERACIONES CRUD ====================

    def create(
        self,
        branch_data: BranchCreate,
        current_user_id: int
    ) -> BranchResponse:
        """
        Crea una nueva sucursal con validaciones de negocio.

        Validaciones:
        - Código único
        - Empresa existe
        - País existe
        - Estado existe (si se proporciona)
        - Manager existe (si se proporciona)

        Args:
            branch_data: Datos de la sucursal a crear
            current_user_id: ID del usuario que crea

        Returns:
            Sucursal creada

        Raises:
            EntityValidationError: Si las validaciones fallan
        """
        # Validar código único
        if not self.repository.verify_code_unique(branch_data.branch_code):
            raise EntityValidationError(
                "Branch",
                {"branch_code": f"El código '{branch_data.branch_code}' ya existe"}
            )

        # Validar empresa existe
        self._validate_company_exists(branch_data.company_id)

        # Validar país existe
        self._validate_country_exists(branch_data.country_id)

        # Validar estado (si se proporciona)
        if branch_data.state_id:
            self._validate_state_exists(branch_data.state_id)

        # Validar manager (si se proporciona)
        if branch_data.manager_id:
            self._validate_individual_exists(branch_data.manager_id)

        # Crear objeto Branch
        branch_dict = branch_data.model_dump()
        branch_dict["created_by"] = current_user_id

        new_branch = self.repository.create(branch_dict)

        return BranchResponse.model_validate(new_branch)

    def get_by_id(
        self,
        branch_id: int,
        with_relations: bool = False
    ) -> BranchResponse | BranchWithRelations:
        """
        Obtiene una sucursal por ID.

        Args:
            branch_id: ID de la sucursal
            with_relations: Si cargar relaciones completas

        Returns:
            Sucursal encontrada

        Raises:
            EntityNotFoundError: Si no existe
        """
        if with_relations:
            branch = self.repository.get_with_relations(branch_id)
        else:
            branch = self.repository.get_by_id(branch_id)

        if not branch:
            raise EntityNotFoundError("Branch", branch_id)

        if with_relations:
            return self._build_with_relations(branch)
        else:
            return BranchResponse.model_validate(branch)

    def get_by_code(self, code: str) -> BranchResponse:
        """
        Obtiene una sucursal por código.

        Args:
            code: Código de la sucursal

        Returns:
            Sucursal encontrada

        Raises:
            EntityNotFoundError: Si no existe
        """
        branch = self.repository.get_by_code(code)

        if not branch:
            raise EntityNotFoundError("Branch", code)

        return BranchResponse.model_validate(branch)

    def update(
        self,
        branch_id: int,
        branch_data: BranchUpdate,
        current_user_id: int
    ) -> BranchResponse:
        """
        Actualiza una sucursal con validaciones.

        Validaciones:
        - Sucursal existe
        - Código único (si se cambia)
        - Referencias válidas (si se cambian)

        Args:
            branch_id: ID de la sucursal
            branch_data: Datos a actualizar
            current_user_id: Usuario que actualiza

        Returns:
            Sucursal actualizada

        Raises:
            EntityNotFoundError: Si no existe
            EntityValidationError: Si validaciones fallan
        """
        # Verificar existe
        branch = self.repository.get_by_id(branch_id)
        if not branch:
            raise EntityNotFoundError("Branch", branch_id)

        # Preparar datos de actualización (solo no-None)
        update_dict = branch_data.model_dump(exclude_unset=True)

        # Validar código único (si se está cambiando)
        if "branch_code" in update_dict:
            if not self.repository.verify_code_unique(
                update_dict["branch_code"],
                exclude_id=branch_id
            ):
                raise EntityValidationError(
                    "Branch",
                    {"branch_code": f"El código '{update_dict['branch_code']}' ya existe"}
                )

        # Validar referencias (si se están cambiando)
        if "company_id" in update_dict:
            self._validate_company_exists(update_dict["company_id"])

        if "country_id" in update_dict:
            self._validate_country_exists(update_dict["country_id"])

        if "state_id" in update_dict and update_dict["state_id"]:
            self._validate_state_exists(update_dict["state_id"])

        if "manager_id" in update_dict and update_dict["manager_id"]:
            self._validate_individual_exists(update_dict["manager_id"])

        # Agregar auditoría
        update_dict["updated_by"] = current_user_id

        # Actualizar
        updated_branch = self.repository.update(branch_id, update_dict)

        return BranchResponse.model_validate(updated_branch)

    def delete(
        self,
        branch_id: int,
        current_user_id: int,
        soft_delete: bool = True
    ) -> bool:
        """
        Elimina una sucursal.

        Args:
            branch_id: ID de la sucursal
            current_user_id: Usuario que elimina
            soft_delete: Si es soft delete (por defecto True)

        Returns:
            True si se eliminó

        Raises:
            EntityNotFoundError: Si no existe
            BusinessLogicException: Si hay dependencias
        """
        # Verificar existe
        branch = self.repository.get_by_id(branch_id)
        if not branch:
            raise EntityNotFoundError("Branch", branch_id)

        # TODO: Validar que no tenga vouchers asociados
        # Esta validación se agregará cuando se implemente Voucher
        # has_vouchers = self._check_vouchers(branch_id)
        # if has_vouchers:
        #     raise BusinessRuleError(
        #         "No se puede eliminar la sucursal porque tiene vales asociados"
        #     )

        # Eliminar
        if soft_delete:
            # Soft delete con auditoría
            self.repository.update(branch_id, {
                "is_deleted": True,
                "deleted_by": current_user_id
            })
        else:
            # Hard delete
            self.repository.delete(branch_id, soft_delete=False)

        return True

    # ==================== BÚSQUEDA Y LISTADO ====================

    def search(
        self,
        search_params: BranchSearch,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Búsqueda avanzada de sucursales.

        Args:
            search_params: Parámetros de búsqueda
            page: Número de página
            per_page: Registros por página

        Returns:
            Diccionario con resultados paginados
        """
        return self.repository.search_branches(
            search_term=search_params.search_term,
            branch_type=search_params.branch_type,
            company_id=search_params.company_id,
            country_id=search_params.country_id,
            state_id=search_params.state_id,
            operational_status=search_params.operational_status,
            active_only=search_params.active_only,
            page=page,
            per_page=per_page
        )

    def get_by_company(self, company_id: int) -> List[BranchResponse]:
        """
        Obtiene todas las sucursales de una empresa.

        Args:
            company_id: ID de la empresa

        Returns:
            Lista de sucursales
        """
        branches = self.repository.get_by_company(company_id)
        return [BranchResponse.model_validate(b) for b in branches]

    def get_by_type(self, branch_type: str) -> List[BranchResponse]:
        """
        Obtiene sucursales por tipo.

        Args:
            branch_type: Tipo de sucursal

        Returns:
            Lista de sucursales
        """
        branches = self.repository.get_by_type(branch_type)
        return [BranchResponse.model_validate(b) for b in branches]

    def get_by_location(
        self,
        country_id: int,
        state_id: Optional[int] = None,
        city: Optional[str] = None
    ) -> List[BranchResponse]:
        """
        Busca sucursales por ubicación geográfica.

        Args:
            country_id: ID del país
            state_id: ID del estado (opcional)
            city: Ciudad (opcional)

        Returns:
            Lista de sucursales
        """
        branches = self.repository.get_by_location(country_id, state_id, city)
        return [BranchResponse.model_validate(b) for b in branches]

    # ==================== OPERACIONES ESPECIALES ====================

    def update_status(
        self,
        branch_id: int,
        new_status: str,
        current_user_id: int
    ) -> BranchResponse:
        """
        Actualiza solo el estado operativo de una sucursal.

        Args:
            branch_id: ID de la sucursal
            new_status: Nuevo estado
            current_user_id: Usuario que actualiza

        Returns:
            Sucursal actualizada

        Raises:
            EntityNotFoundError: Si no existe
        """
        success = self.repository.update_operational_status(
            branch_id,
            new_status,
            current_user_id
        )

        if not success:
            raise EntityNotFoundError("Branch", branch_id)

        return self.get_by_id(branch_id)

    def get_statistics(self, company_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de sucursales.

        Args:
            company_id: Filtrar por empresa (opcional)

        Returns:
            Diccionario con estadísticas
        """
        from sqlalchemy import func

        query = self.db.query(Branch).filter(
            Branch.is_active == True,
            Branch.is_deleted == False
        )

        if company_id:
            query = query.filter(Branch.company_id == company_id)

        total = query.count()

        # Por tipo
        by_type = self.db.query(
            Branch.branch_type,
            func.count(Branch.id).label("count")
        ).filter(
            Branch.is_active == True,
            Branch.is_deleted == False
        )

        if company_id:
            by_type = by_type.filter(Branch.company_id == company_id)

        by_type = by_type.group_by(Branch.branch_type).all()

        # Por estado operativo
        by_status = self.db.query(
            Branch.operational_status,
            func.count(Branch.id).label("count")
        ).filter(
            Branch.is_active == True,
            Branch.is_deleted == False
        )

        if company_id:
            by_status = by_status.filter(Branch.company_id == company_id)

        by_status = by_status.group_by(Branch.operational_status).all()

        return {
            "total": total,
            "by_type": {item.branch_type: item.count for item in by_type},
            "by_status": {item.operational_status: item.count for item in by_status}
        }

    # ==================== MÉTODOS AUXILIARES PRIVADOS ====================

    def _build_with_relations(self, branch: Branch) -> BranchWithRelations:
        """
        Construye BranchWithRelations desde un objeto Branch.

        Args:
            branch: Branch con relaciones cargadas

        Returns:
            BranchWithRelations con nombres de relaciones
        """
        branch_dict = BranchResponse.model_validate(branch).model_dump()

        # Agregar nombres de relaciones
        branch_dict["company_name"] = branch.company.company_name if branch.company else None
        branch_dict["country_name"] = branch.country.country_name if branch.country else None
        branch_dict["state_name"] = branch.state.state_name if branch.state else None

        if branch.manager:
            branch_dict["manager_name"] = f"{branch.manager.first_name} {branch.manager.last_name}"
        else:
            branch_dict["manager_name"] = None

        if branch.creator:
            branch_dict["creator_name"] = branch.creator.name
        else:
            branch_dict["creator_name"] = None

        if branch.updater:
            branch_dict["updater_name"] = branch.updater.name
        else:
            branch_dict["updater_name"] = None

        return BranchWithRelations(**branch_dict)

    def _validate_company_exists(self, company_id: int):
        """
        Valida que una empresa existe.

        Args:
            company_id: ID de la empresa

        Raises:
            EntityValidationError: Si no existe
        """
        from app.entities.companies.models.company import Company

        company = self.db.query(Company).filter(
            Company.id == company_id,
            Company.is_active == True,
            Company.is_deleted == False
        ).first()

        if not company:
            raise EntityValidationError(
                "Branch",
                {"company_id": f"La empresa con ID {company_id} no existe"}
            )

    def _validate_country_exists(self, country_id: int):
        """
        Valida que un país existe.

        Args:
            country_id: ID del país

        Raises:
            EntityValidationError: Si no existe
        """
        from app.entities.countries.models.country import Country

        country = self.db.query(Country).filter(
            Country.id == country_id,
            Country.is_active == True,
            Country.is_deleted == False
        ).first()

        if not country:
            raise EntityValidationError(
                "Branch",
                {"country_id": f"El país con ID {country_id} no existe"}
            )

    def _validate_state_exists(self, state_id: int):
        """
        Valida que un estado existe.

        Args:
            state_id: ID del estado

        Raises:
            EntityValidationError: Si no existe
        """
        from app.entities.states.models.state import State

        state = self.db.query(State).filter(
            State.id == state_id,
            State.is_active == True,
            State.is_deleted == False
        ).first()

        if not state:
            raise EntityValidationError(
                "Branch",
                {"state_id": f"El estado con ID {state_id} no existe"}
            )

    def _validate_individual_exists(self, individual_id: int):
        """
        Valida que un individual (manager) existe.

        Args:
            individual_id: ID del individual

        Raises:
            EntityValidationError: Si no existe
        """
        from app.entities.individuals.models.individual import Individual

        individual = self.db.query(Individual).filter(
            Individual.id == individual_id,
            Individual.is_active == True,
            Individual.is_deleted == False
        ).first()

        if not individual:
            raise EntityValidationError(
                "Branch",
                {"manager_id": f"El individual con ID {individual_id} no existe"}
            )
