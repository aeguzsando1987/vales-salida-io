"""
Router: State
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from app.shared.dependencies import get_current_user
from app.entities.states.controllers.state_controller import StateController
from app.entities.states.schemas.state_schemas import StateResponse


router = APIRouter(
    prefix="/states",
    tags=["States"]
)


@router.get(
    "/",
    response_model=List[StateResponse],
    summary="Listar estados",
    description="Obtiene lista de estados/provincias/departamentos con paginacion"
)
def list_states(
    skip: int = Query(0, ge=0, description="Numero de registros a saltar"),
    limit: int = Query(1000, ge=1, le=1000, description="Cantidad de registros a retornar"),
    active_only: bool = Query(False, description="Solo registros activos"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista estados con paginacion."""
    controller = StateController(db)
    return controller.get_all(skip, limit, active_only)


@router.get(
    "/{id}",
    response_model=StateResponse,
    summary="Obtener estado por ID",
    description="Obtiene los detalles de un estado especifico"
)
def get_state(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un estado por ID."""
    controller = StateController(db)
    return controller.get_by_id(id)


@router.get(
    "/by-country/{country_id}",
    response_model=List[StateResponse],
    summary="Obtener estados por pais",
    description="Obtiene todos los estados de un pais especifico"
)
def get_states_by_country(
    country_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene todos los estados de un pais."""
    controller = StateController(db)
    return controller.get_by_country(country_id)


@router.get(
    "/search/",
    response_model=List[StateResponse],
    summary="Buscar estados",
    description="Busca estados por nombre"
)
def search_states(
    q: str = Query(..., min_length=1, description="Termino de busqueda"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Busca estados por nombre."""
    controller = StateController(db)
    return controller.search(q)