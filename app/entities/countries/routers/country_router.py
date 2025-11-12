"""
Router: Country
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from app.shared.dependencies import get_current_user
from app.entities.countries.controllers.country_controller import CountryController
from app.entities.countries.schemas.country_schemas import CountryResponse


router = APIRouter(
    prefix="/countries",
    tags=["Countries"]
)


@router.get(
    "/",
    response_model=List[CountryResponse],
    summary="Listar paises",
    description="Obtiene lista de paises con paginacion"
)
def list_countries(
    skip: int = Query(0, ge=0, description="Numero de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Cantidad de registros a retornar"),
    active_only: bool = Query(False, description="Solo registros activos"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista paises con paginacion."""
    controller = CountryController(db)
    return controller.get_all(skip, limit, active_only)


@router.get(
    "/{id}",
    response_model=CountryResponse,
    summary="Obtener pais por ID",
    description="Obtiene los detalles de un pais especifico"
)
def get_country(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un pais por ID."""
    controller = CountryController(db)
    return controller.get_by_id(id)


@router.get(
    "/iso/{iso_code}",
    response_model=CountryResponse,
    summary="Obtener pais por codigo ISO",
    description="Obtiene un pais por su codigo ISO 3166-1 (alpha-2 o alpha-3)"
)
def get_country_by_iso(
    iso_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un pais por codigo ISO (2 o 3 letras)."""
    controller = CountryController(db)
    return controller.get_by_iso(iso_code)


@router.get(
    "/search/",
    response_model=List[CountryResponse],
    summary="Buscar paises",
    description="Busca paises por nombre"
)
def search_countries(
    q: str = Query(..., min_length=1, description="Termino de busqueda"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Busca paises por nombre."""
    controller = CountryController(db)
    return controller.search(q)