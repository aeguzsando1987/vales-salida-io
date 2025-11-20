"""
Controller para la entidad Branch.

Orquesta las operaciones HTTP, maneja request/response y delega
la lógica de negocio al Service.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.entities.branches.services.branch_service import BranchService
from app.entities.branches.schemas.branch_schemas import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchWithRelations,
    BranchListResponse,
    BranchSearch,
    BranchStatusUpdate
)

from app.shared.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    BusinessRuleError
)


class BranchController:
    """
    Controller para Branch.

    Maneja request/response y orquesta llamadas al Service.
    """

    def __init__(self, db: Session):
        """
        Inicializa el controller con su service.

        Args:
            db: Sesión de base de datos
        """
        self.service = BranchService(db)

    # ==================== OPERACIONES CRUD ====================

    def create(
        self,
        branch_data: BranchCreate,
        current_user_id: int
    ) -> BranchResponse:
        """
        Crea una nueva sucursal.

        Args:
            branch_data: Datos de la sucursal
            current_user_id: ID del usuario autenticado

        Returns:
            Sucursal creada

        Raises:
            HTTPException 400: Si validaciones fallan
            HTTPException 500: Si error interno
        """
        try:
            return self.service.create(branch_data, current_user_id)

        except EntityValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear sucursal: {str(e)}"
            )

    def get_by_id(
        self,
        branch_id: int,
        with_relations: bool = False
    ) -> BranchResponse | BranchWithRelations:
        """
        Obtiene una sucursal por ID.

        Args:
            branch_id: ID de la sucursal
            with_relations: Si incluir nombres de relaciones

        Returns:
            Sucursal encontrada

        Raises:
            HTTPException 404: Si no existe
            HTTPException 500: Si error interno
        """
        try:
            return self.service.get_by_id(branch_id, with_relations)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener sucursal: {str(e)}"
            )

    def get_by_code(self, code: str) -> BranchResponse:
        """
        Obtiene una sucursal por código.

        Args:
            code: Código de la sucursal

        Returns:
            Sucursal encontrada

        Raises:
            HTTPException 404: Si no existe
            HTTPException 500: Si error interno
        """
        try:
            return self.service.get_by_code(code)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener sucursal por código: {str(e)}"
            )

    def update(
        self,
        branch_id: int,
        branch_data: BranchUpdate,
        current_user_id: int
    ) -> BranchResponse:
        """
        Actualiza una sucursal.

        Args:
            branch_id: ID de la sucursal
            branch_data: Datos a actualizar
            current_user_id: Usuario autenticado

        Returns:
            Sucursal actualizada

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si validaciones fallan
            HTTPException 500: Si error interno
        """
        try:
            return self.service.update(branch_id, branch_data, current_user_id)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except EntityValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar sucursal: {str(e)}"
            )

    def delete(
        self,
        branch_id: int,
        current_user_id: int,
        soft_delete: bool = True
    ) -> dict:
        """
        Elimina una sucursal.

        Args:
            branch_id: ID de la sucursal
            current_user_id: Usuario autenticado
            soft_delete: Si es eliminación suave

        Returns:
            Mensaje de confirmación

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si hay dependencias
            HTTPException 500: Si error interno
        """
        try:
            self.service.delete(branch_id, current_user_id, soft_delete)
            return {
                "message": "Sucursal eliminada exitosamente",
                "branch_id": branch_id
            }

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except BusinessRuleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar sucursal: {str(e)}"
            )

    # ==================== BÚSQUEDA Y LISTADO ====================

    def search(
        self,
        search_params: BranchSearch,
        page: int = 1,
        per_page: int = 20
    ) -> BranchListResponse:
        """
        Búsqueda avanzada de sucursales.

        Args:
            search_params: Parámetros de búsqueda
            page: Número de página
            per_page: Registros por página

        Returns:
            Resultados paginados

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            result = self.service.search(search_params, page, per_page)
            return BranchListResponse(**result)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en búsqueda: {str(e)}"
            )

    def get_by_company(self, company_id: int) -> list[BranchResponse]:
        """
        Lista sucursales de una empresa.

        Args:
            company_id: ID de la empresa

        Returns:
            Lista de sucursales

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            return self.service.get_by_company(company_id)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar sucursales: {str(e)}"
            )

    def get_by_type(self, branch_type: str) -> list[BranchResponse]:
        """
        Lista sucursales por tipo.

        Args:
            branch_type: Tipo de sucursal

        Returns:
            Lista de sucursales

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            return self.service.get_by_type(branch_type)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar sucursales por tipo: {str(e)}"
            )

    def get_by_location(
        self,
        country_id: int,
        state_id: Optional[int] = None,
        city: Optional[str] = None
    ) -> list[BranchResponse]:
        """
        Lista sucursales por ubicación.

        Args:
            country_id: ID del país
            state_id: ID del estado (opcional)
            city: Ciudad (opcional)

        Returns:
            Lista de sucursales

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            return self.service.get_by_location(country_id, state_id, city)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar sucursales por ubicación: {str(e)}"
            )

    # ==================== OPERACIONES ESPECIALES ====================

    def update_status(
        self,
        branch_id: int,
        status_data: BranchStatusUpdate,
        current_user_id: int
    ) -> BranchResponse:
        """
        Actualiza el estado operativo de una sucursal.

        Args:
            branch_id: ID de la sucursal
            status_data: Nuevo estado
            current_user_id: Usuario autenticado

        Returns:
            Sucursal actualizada

        Raises:
            HTTPException 404: Si no existe
            HTTPException 500: Si error interno
        """
        try:
            return self.service.update_status(
                branch_id,
                status_data.operational_status,
                current_user_id
            )

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar estado: {str(e)}"
            )

    def get_statistics(self, company_id: Optional[int] = None) -> dict:
        """
        Obtiene estadísticas de sucursales.

        Args:
            company_id: Filtrar por empresa (opcional)

        Returns:
            Diccionario con estadísticas

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            return self.service.get_statistics(company_id)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener estadísticas: {str(e)}"
            )

    def get_enums(self) -> dict:
        """
        Retorna los ENUMs disponibles para Branch.

        Útil para formularios dinámicos en frontend.

        Returns:
            Diccionario con valores de ENUMs
        """
        from app.entities.branches.schemas.branch_schemas import BranchType, OperationalStatus

        return {
            "branch_types": [t.value for t in BranchType],
            "operational_statuses": [s.value for s in OperationalStatus]
        }
