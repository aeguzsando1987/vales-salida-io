"""
Repositorio: Country
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.shared.base_repository import BaseRepository
from app.entities.countries.models.country import Country


class CountryRepository(BaseRepository[Country]):
    """Repositorio para operaciones de datos de Country."""

    def __init__(self, db: Session):
        super().__init__(Country, db)

    def get_by_iso_code_2(self, iso_code: str) -> Optional[Country]:
        """Obtiene un pais por su codigo ISO 3166-1 alpha-2."""
        return self.db.query(Country).filter(
            Country.iso_code_2 == iso_code.upper(),
            Country.is_deleted == False
        ).first()

    def get_by_iso_code_3(self, iso_code: str) -> Optional[Country]:
        """Obtiene un pais por su codigo ISO 3166-1 alpha-3."""
        return self.db.query(Country).filter(
            Country.iso_code_3 == iso_code.upper(),
            Country.is_deleted == False
        ).first()

    def get_active_only(self, skip: int = 0, limit: int = 100) -> List[Country]:
        """Obtiene solo paises activos."""
        return self.db.query(Country).filter(
            Country.is_active == True,
            Country.is_deleted == False
        ).offset(skip).limit(limit).all()

    def search_by_name(self, name: str) -> List[Country]:
        """Busca paises por nombre (busqueda parcial)."""
        return self.db.query(Country).filter(
            Country.name.ilike(f"%{name}%"),
            Country.is_deleted == False
        ).all()