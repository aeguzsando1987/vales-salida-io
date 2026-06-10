"""
Service para IOManager (Contralor). Lógica de negocio y validaciones.
"""
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.entities.io_managers.repositories.io_manager_repository import IOManagerRepository
from app.entities.io_managers.models.io_manager import IOManager
from app.entities.io_managers.schemas.io_manager_schemas import IOManagerCreate
from app.entities.individuals.models.individual import Individual
from app.shared.exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleError,
)


class IOManagerService:
    """Lógica de negocio para contralores (io managers)."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = IOManagerRepository(db)

    def _get_individual(self, individual_id: int) -> Individual:
        individual = self.db.query(Individual).filter(
            Individual.id == individual_id,
            Individual.is_deleted == False
        ).first()
        if not individual:
            raise EntityNotFoundError("Individual", individual_id)
        return individual

    def create(self, data: IOManagerCreate, current_user_id: int) -> IOManager:
        """Registra un contralor. Reactiva si existía dado de baja."""
        # El individual debe existir
        self._get_individual(data.individual_id)

        existing = self.repository.get_by_individual_id(data.individual_id)
        if existing:
            if existing.is_active:
                raise EntityAlreadyExistsError("Contralor", "individual_id", data.individual_id)
            # Reactivar registro existente
            existing.is_active = True
            existing.updated_by = current_user_id
            existing.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        return self.repository.create({
            "individual_id": data.individual_id,
            "is_active": True,
            "created_by": current_user_id,
        })

    def list_all(self) -> List[IOManager]:
        """Lista contralores activos (no borrados)."""
        return self.repository.list_active()

    def remove(self, io_manager_id: int, current_user_id: int) -> bool:
        """Da de baja (soft delete) a un contralor."""
        io_manager = self.repository.get_by_id(io_manager_id)
        if not io_manager or io_manager.is_deleted:
            raise EntityNotFoundError("Contralor", io_manager_id)

        io_manager.is_active = False
        io_manager.is_deleted = True
        io_manager.deleted_by = current_user_id
        io_manager.deleted_at = datetime.now()
        self.db.commit()
        return True
