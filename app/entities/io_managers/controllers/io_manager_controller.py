"""
Controller para IOManager (Contralor).
Orquesta request/response y transforma a schemas Pydantic.
"""
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.entities.io_managers.services.io_manager_service import IOManagerService
from app.entities.io_managers.schemas.io_manager_schemas import (
    IOManagerCreate,
    IOManagerResponse,
)
from app.entities.io_managers.models.io_manager import IOManager
from app.shared.exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleError,
)


class IOManagerController:
    """Controller para contralores (io managers)."""

    def __init__(self, db: Session):
        self.service = IOManagerService(db)

    def _to_response(self, io_manager: IOManager) -> IOManagerResponse:
        individual = io_manager.individual
        return IOManagerResponse(
            id=io_manager.id,
            individual_id=io_manager.individual_id,
            is_active=io_manager.is_active,
            created_at=io_manager.created_at,
            created_by=io_manager.created_by,
            individual_name=individual.full_name if individual else None,
            individual_email=individual.email if individual else None,
        )

    def create(self, data: IOManagerCreate, current_user_id: int) -> IOManagerResponse:
        try:
            io_manager = self.service.create(data, current_user_id)
            return self._to_response(io_manager)
        except EntityNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except EntityAlreadyExistsError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        except BusinessRuleError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al registrar contralor: {str(e)}"
            )

    def list_all(self) -> List[IOManagerResponse]:
        try:
            return [self._to_response(m) for m in self.service.list_all()]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar contralores: {str(e)}"
            )

    def remove(self, io_manager_id: int, current_user_id: int) -> dict:
        try:
            self.service.remove(io_manager_id, current_user_id)
            return {"success": True, "message": "Contralor dado de baja correctamente"}
        except EntityNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al dar de baja contralor: {str(e)}"
            )
