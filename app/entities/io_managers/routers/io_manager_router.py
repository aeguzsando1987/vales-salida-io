"""
Router para la entidad IOManager (Contralor).

Gestión transversal de contralores (io managers): alta, listado y baja.
La pertenencia activa a esta tabla es el gate de la 2ª aprobación de vales.
Gestión reservada a Admin (ver PERMISSION_MATRIX en init_db.py).
"""
from typing import List
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from database import get_db, User
from app.shared.dependencies import require_permission

from app.entities.io_managers.controllers.io_manager_controller import IOManagerController
from app.entities.io_managers.schemas.io_manager_schemas import (
    IOManagerCreate,
    IOManagerResponse,
)


router = APIRouter(
    prefix="/io-managers",
    tags=["IO Managers (Contralores)"],
    responses={
        404: {"description": "Contralor no encontrado"},
        409: {"description": "El individual ya es contralor"},
        403: {"description": "Permisos insuficientes"},
    }
)


@router.post(
    "/",
    response_model=IOManagerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar contralor",
    description="Da de alta a un individual como contralor (io manager)."
)
def create_io_manager(
    data: IOManagerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("io-managers", "create", min_level=3))
):
    controller = IOManagerController(db)
    return controller.create(data, current_user.id)


@router.get(
    "/",
    response_model=List[IOManagerResponse],
    summary="Listar contralores",
    description="Lista los contralores (io managers) activos."
)
def list_io_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("io-managers", "list", min_level=1))
):
    controller = IOManagerController(db)
    return controller.list_all()


@router.delete(
    "/{io_manager_id}",
    response_model=dict,
    summary="Dar de baja contralor",
    description="Da de baja (soft delete) a un contralor."
)
def delete_io_manager(
    io_manager_id: int = Path(..., gt=0, description="ID del registro de contralor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("io-managers", "delete", min_level=4))
):
    controller = IOManagerController(db)
    return controller.remove(io_manager_id, current_user.id)
