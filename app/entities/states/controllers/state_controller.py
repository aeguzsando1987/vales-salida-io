"""
Controlador: State
"""
from typing import List
from sqlalchemy.orm import Session

from app.entities.states.services.state_service import StateService
from app.entities.states.schemas.state_schemas import StateResponse


class StateController:
    """Controlador para coordinar operaciones de State."""

    def __init__(self, db: Session):
        self.service = StateService(db)

    def get_by_id(self, state_id: int) -> StateResponse:
        """Obtiene un estado por ID."""
        state = self.service.get_state(state_id)
        return StateResponse.model_validate(state)

    def get_all(self, skip: int = 0, limit: int = 1000, active_only: bool = False) -> List[StateResponse]:
        """Lista todos los estados."""
        states = self.service.list_states(skip, limit, active_only)
        return [StateResponse.model_validate(s) for s in states]

    def get_by_country(self, country_id: int) -> List[StateResponse]:
        """Obtiene todos los estados de un pais."""
        states = self.service.get_by_country(country_id)
        return [StateResponse.model_validate(s) for s in states]

    def search(self, query: str) -> List[StateResponse]:
        """Busca estados por nombre."""
        states = self.service.search_states(query)
        return [StateResponse.model_validate(s) for s in states]