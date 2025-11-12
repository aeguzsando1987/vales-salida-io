"""
Controlador: Country
"""
from typing import List
from sqlalchemy.orm import Session

from app.entities.countries.services.country_service import CountryService
from app.entities.countries.schemas.country_schemas import CountryResponse


class CountryController:
    """Controlador para coordinar operaciones de Country."""

    def __init__(self, db: Session):
        self.service = CountryService(db)

    def get_by_id(self, country_id: int) -> CountryResponse:
        """Obtiene un pais por ID."""
        country = self.service.get_country(country_id)
        return CountryResponse.model_validate(country)

    def get_by_iso(self, iso_code: str) -> CountryResponse:
        """Obtiene un pais por codigo ISO."""
        country = self.service.get_by_iso_code(iso_code)
        return CountryResponse.model_validate(country)

    def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[CountryResponse]:
        """Lista todos los paises."""
        countries = self.service.list_countries(skip, limit, active_only)
        return [CountryResponse.model_validate(c) for c in countries]

    def search(self, query: str) -> List[CountryResponse]:
        """Busca paises por nombre."""
        countries = self.service.search_countries(query)
        return [CountryResponse.model_validate(c) for c in countries]