"""
BaseRepository - Repositorio genérico para operaciones CRUD comunes

Este módulo implementa el patrón Repository con generics de Python,
permitiendo reutilizar operaciones CRUD estándar para cualquier entidad.

Características:
- Tipado fuerte con TypeVar
- Operaciones CRUD completas
- Paginación integrada
- Filtros dinámicos
- Manejo de transacciones
- Extensible para operaciones específicas
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.ext.declarative import DeclarativeMeta

# T representa cualquier modelo SQLAlchemy
T = TypeVar('T', bound=DeclarativeMeta)

class BaseRepository(Generic[T]):
    """
    Repositorio base genérico para operaciones CRUD estándar.

    Uso:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: Session):
                super().__init__(User, db)

    El parámetro T será reemplazado por el tipo específico (User, Person, etc.)
    """

    def __init__(self, model: Type[T], db: Session):
        """
        Inicializa el repositorio con el modelo y sesión de BD.

        Args:
            model: Clase del modelo SQLAlchemy (User, Person, etc.)
            db: Sesión de base de datos SQLAlchemy
        """
        self.model = model
        self.db = db

    # ==================== OPERACIONES BÁSICAS CRUD ====================

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Busca una entidad por su ID.

        Args:
            id: ID de la entidad a buscar

        Returns:
            La entidad encontrada o None si no existe

        Ejemplo:
            user = user_repository.get_by_id(123)
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[T]:
        """
        Obtiene todas las entidades con paginación.

        Args:
            skip: Número de registros a saltar (para paginación)
            limit: Máximo número de registros a retornar
            active_only: Si True, solo retorna registros activos

        Returns:
            Lista de entidades encontradas

        Ejemplo:
            users = user_repository.get_all(skip=0, limit=50)
        """
        query = self.db.query(self.model)

        # Filtrar solo activos si la entidad tiene campo is_active
        if active_only and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)

        return query.offset(skip).limit(limit).all()

    def create(self, obj_data: Dict[str, Any]) -> T:
        """
        Crea una nueva entidad en la base de datos.

        Args:
            obj_data: Diccionario con los datos de la entidad

        Returns:
            La entidad creada con ID asignado

        Ejemplo:
            user_data = {"email": "test@test.com", "name": "Test User"}
            new_user = user_repository.create(user_data)
        """
        db_obj = self.model()

        # Asignar campos usando setattr para compatibilidad con SQLAlchemy
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[T]:
        """
        Actualiza una entidad existente.

        Args:
            id: ID de la entidad a actualizar
            obj_data: Diccionario con los nuevos datos

        Returns:
            La entidad actualizada o None si no existe

        Ejemplo:
            updated_data = {"name": "New Name"}
            updated_user = user_repository.update(123, updated_data)
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None

        # Actualizar solo los campos proporcionados
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        # Actualizar timestamp si existe
        if hasattr(db_obj, 'updated_at'):
            from datetime import datetime
            db_obj.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int, soft_delete: bool = True) -> bool:
        """
        Elimina una entidad (soft delete por defecto).

        Args:
            id: ID de la entidad a eliminar
            soft_delete: Si True, marca como inactivo. Si False, elimina físicamente

        Returns:
            True si se eliminó correctamente, False si no existe

        Ejemplo:
            # Soft delete (recomendado)
            success = user_repository.delete(123)

            # Hard delete (permanente)
            success = user_repository.delete(123, soft_delete=False)
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False

        if soft_delete and hasattr(db_obj, 'is_active'):
            # Soft delete: marcar como inactivo
            db_obj.is_active = False
            if hasattr(db_obj, 'updated_at'):
                from datetime import datetime
                db_obj.updated_at = datetime.utcnow()
            self.db.commit()
        else:
            # Hard delete: eliminar físicamente
            self.db.delete(db_obj)
            self.db.commit()

        return True

    # ==================== OPERACIONES AVANZADAS ====================

    def exists(self, id: int) -> bool:
        """
        Verifica si existe una entidad con el ID dado.

        Args:
            id: ID a verificar

        Returns:
            True si existe, False si no

        Ejemplo:
            if user_repository.exists(123):
                print("Usuario existe")
        """
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

    def count(self, active_only: bool = True) -> int:
        """
        Cuenta el total de registros.

        Args:
            active_only: Si True, cuenta solo registros activos

        Returns:
            Número total de registros

        Ejemplo:
            total_users = user_repository.count()
        """
        query = self.db.query(self.model)

        if active_only and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)

        return query.count()

    def find_by_field(self, field_name: str, value: Any) -> List[T]:
        """
        Busca entidades por un campo específico.

        Args:
            field_name: Nombre del campo a buscar
            value: Valor a buscar

        Returns:
            Lista de entidades que coinciden

        Ejemplo:
            users = user_repository.find_by_field("email", "test@test.com")
            persons = person_repository.find_by_field("status", "active")
        """
        if not hasattr(self.model, field_name):
            return []

        field = getattr(self.model, field_name)
        return self.db.query(self.model).filter(field == value).all()

    def find_by_filters(self, filters: Dict[str, Any]) -> List[T]:
        """
        Busca entidades aplicando múltiples filtros.

        Args:
            filters: Diccionario con campo: valor a filtrar

        Returns:
            Lista de entidades que coinciden con TODOS los filtros

        Ejemplo:
            filters = {"status": "active", "role": 1}
            admins = user_repository.find_by_filters(filters)
        """
        query = self.db.query(self.model)

        for field_name, value in filters.items():
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                query = query.filter(field == value)

        return query.all()

    def search(
        self,
        search_term: str,
        search_fields: List[str],
        limit: int = 50
    ) -> List[T]:
        """
        Búsqueda de texto en múltiples campos.

        Args:
            search_term: Término a buscar
            search_fields: Lista de campos donde buscar
            limit: Máximo de resultados

        Returns:
            Lista de entidades que contienen el término

        Ejemplo:
            # Buscar "Juan" en nombre y apellido
            persons = person_repository.search(
                "Juan",
                ["first_name", "last_name"],
                limit=20
            )
        """
        if not search_term or not search_fields:
            return []

        query = self.db.query(self.model)

        # Crear condiciones OR para cada campo
        conditions = []
        for field_name in search_fields:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                # Búsqueda case-insensitive que contenga el término
                conditions.append(field.ilike(f"%{search_term}%"))

        if conditions:
            query = query.filter(or_(*conditions))

        return query.limit(limit).all()

    # ==================== OPERACIONES DE PAGINACIÓN ====================

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc"
    ) -> Dict[str, Any]:
        """
        Paginación avanzada con filtros y ordenamiento.

        Args:
            page: Número de página (empezando en 1)
            per_page: Registros por página
            filters: Filtros a aplicar
            order_by: Campo por el cual ordenar
            order_direction: "asc" o "desc"

        Returns:
            Diccionario con:
            - items: Lista de entidades
            - total: Total de registros
            - page: Página actual
            - per_page: Registros por página
            - pages: Total de páginas

        Ejemplo:
            result = user_repository.paginate(
                page=2,
                per_page=10,
                filters={"is_active": True},
                order_by="created_at",
                order_direction="desc"
            )
            users = result["items"]
            total_pages = result["pages"]
        """
        query = self.db.query(self.model)

        # Aplicar filtros
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    query = query.filter(field == value)

        # Aplicar ordenamiento
        if order_by and hasattr(self.model, order_by):
            field = getattr(self.model, order_by)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))

        # Calcular paginación
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        # Calcular número de páginas
        pages = (total + per_page - 1) // per_page

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }