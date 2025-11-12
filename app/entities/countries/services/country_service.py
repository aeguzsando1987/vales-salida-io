"""
Servicio: Country
"""
from typing import List
from sqlalchemy.orm import Session

from app.entities.countries.repositories.country_repository import CountryRepository
from app.entities.countries.models.country import Country
from app.shared.exceptions import EntityNotFoundError


class CountryService:
    """Servicio de logica de negocio para Country."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = CountryRepository(db)

    def get_country(self, country_id: int) -> Country:
        """Obtiene un pais por ID."""
        country = self.repository.get_by_id(country_id)
        if not country or country.is_deleted:
            raise EntityNotFoundError("Country", country_id)
        return country

    def get_by_iso_code(self, iso_code: str) -> Country:
        """Obtiene un pais por codigo ISO (2 o 3 letras)."""
        if len(iso_code) == 2:
            country = self.repository.get_by_iso_code_2(iso_code)
        elif len(iso_code) == 3:
            country = self.repository.get_by_iso_code_3(iso_code)
        else:
            raise ValueError("ISO code debe ser de 2 o 3 caracteres")

        if not country:
            raise EntityNotFoundError("Country", iso_code)
        return country

    def list_countries(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Country]:
        """Lista paises con paginacion."""
        if active_only:
            return self.repository.get_active_only(skip, limit)
        return self.repository.get_all(skip, limit)

    def search_countries(self, query: str) -> List[Country]:
        """Busca paises por nombre."""
        return self.repository.search_by_name(query)