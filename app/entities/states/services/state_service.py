"""
Servicio: State
"""
from typing import List
from sqlalchemy.orm import Session

from app.entities.states.repositories.state_repository import StateRepository
from app.entities.states.models.state import State
from app.shared.exceptions import EntityNotFoundError


class StateService:
    """Servicio de logica de negocio para State."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = StateRepository(db)

    def get_state(self, state_id: int) -> State:
        """Obtiene un estado por ID."""
        state = self.repository.get_by_id(state_id)
        if not state or state.is_deleted:
            raise EntityNotFoundError("State", state_id)
        return state

    def list_states(self, skip: int = 0, limit: int = 1000, active_only: bool = False) -> List[State]:
        """Lista estados con paginacion."""
        if active_only:
            return self.repository.get_active_only(skip, limit)
        return self.repository.get_all(skip, limit)

    def get_by_country(self, country_id: int) -> List[State]:
        """Obtiene todos los estados de un pais."""
        return self.repository.get_by_country(country_id)

    def search_states(self, query: str) -> List[State]:
        """Busca estados por nombre."""
        return self.repository.search_by_name(query)