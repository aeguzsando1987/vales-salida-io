"""
Repositorio: State
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.shared.base_repository import BaseRepository
from app.entities.states.models.state import State


class StateRepository(BaseRepository[State]):
    """Repositorio para operaciones de datos de State."""

    def __init__(self, db: Session):
        super().__init__(State, db)

    def get_by_country(self, country_id: int) -> List[State]:
        """Obtiene todos los estados de un pais."""
        return self.db.query(State).filter(
            State.country_id == country_id,
            State.is_deleted == False
        ).all()

    def get_by_code_and_country(self, code: str, country_id: int) -> Optional[State]:
        """Obtiene un estado por codigo y pais."""
        return self.db.query(State).filter(
            State.code == code.upper(),
            State.country_id == country_id,
            State.is_deleted == False
        ).first()

    def get_active_only(self, skip: int = 0, limit: int = 100) -> List[State]:
        """Obtiene solo estados activos."""
        return self.db.query(State).filter(
            State.is_active == True,
            State.is_deleted == False
        ).offset(skip).limit(limit).all()

    def search_by_name(self, name: str) -> List[State]:
        """Busca estados por nombre (busqueda parcial)."""
        return self.db.query(State).filter(
            State.name.ilike(f"%{name}%"),
            State.is_deleted == False
        ).all()