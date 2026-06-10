"""
Repository para IOManager (Contralor).
Solo queries a BD. Filtra siempre is_deleted == False.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.shared.base_repository import BaseRepository
from app.entities.io_managers.models.io_manager import IOManager


class IOManagerRepository(BaseRepository[IOManager]):
    """Repositorio para IOManager."""

    def __init__(self, db: Session):
        super().__init__(IOManager, db)  # (Model, db)

    def get_by_individual_id(self, individual_id: int) -> Optional[IOManager]:
        """Busca el registro (no borrado) de un individual."""
        return self.db.query(IOManager).filter(
            IOManager.individual_id == individual_id,
            IOManager.is_deleted == False
        ).first()

    def exists_active_for_individual(self, individual_id: int) -> bool:
        """True si el individual es contralor ACTIVO (gate de la 2ª aprobación)."""
        return self.db.query(IOManager).filter(
            IOManager.individual_id == individual_id,
            IOManager.is_active == True,
            IOManager.is_deleted == False
        ).first() is not None

    def list_active(self) -> List[IOManager]:
        """Todos los contralores activos (para notificar nivel 2)."""
        return self.db.query(IOManager).filter(
            IOManager.is_active == True,
            IOManager.is_deleted == False
        ).all()

    def list_all(self) -> List[IOManager]:
        """Todos los contralores no borrados (para la sección de gestión)."""
        return self.db.query(IOManager).filter(
            IOManager.is_deleted == False
        ).all()
