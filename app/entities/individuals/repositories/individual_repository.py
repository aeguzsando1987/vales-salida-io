"""
Repository para la entidad Individual

Este repository extiende BaseRepository con funcionalidades específicas
de Individual, manteniendo compatibilidad con el comportamiento existente
del módulo modules/individuals/.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.shared.base_repository import BaseRepository
from app.entities.individuals.models.individual import Individual
from app.entities.individuals.schemas.enums import IndividualStatusEnum
from app.shared.exceptions import EntityNotFoundError, EntityAlreadyExistsError


class IndividualRepository(BaseRepository[Individual]):
    """
    Repository específico para Individual con funcionalidades avanzadas.

    Mantiene compatibilidad total con el comportamiento existente
    en modules/individuals/routes.py mientras añade nuevas capacidades.
    """

    def __init__(self, db: Session):
        super().__init__(Individual, db)

    # ==================== MÉTODOS DE COMPATIBILIDAD ====================

    def get_active_individuals(self) -> List[Individual]:
        """
        Obtiene todos los individuos activos.

        Mantiene compatibilidad con GET /individuals/ existente.
        """
        return self.db.query(Individual).filter(Individual.is_active == True).all()

    def find_by_email(self, email: str) -> Optional[Individual]:
        """
        Busca individuo por email.

        Usado para validar unicidad de email.
        """
        return self.db.query(Individual).filter(Individual.email == email).first()

    def search_with_filters(
        self,
        name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False,
        additional_filters: Optional[Dict[str, Any]] = None
    ) -> List[Individual]:
        """
        Búsqueda avanzada con filtros dinámicos.

        Mantiene compatibilidad total con GET /individuals/search existente.
        Replica exactamente la lógica de modules/individuals/routes.py
        """
        # Query base - solo individuos activos
        query = self.db.query(Individual).filter(Individual.is_active == True)

        # Filtros específicos (compatibilidad con API existente)
        if name:
            query = query.filter(Individual.first_name.ilike(f"%{name}%"))
        if last_name:
            query = query.filter(Individual.last_name.ilike(f"%{last_name}%"))
        if email:
            query = query.filter(Individual.email.ilike(f"%{email}%"))
        if phone:
            # Búsqueda en array de teléfonos del nuevo modelo
            query = query.filter(
                or_(
                    Individual.phone_numbers.any(phone),  # Nuevo campo array
                    func.cast(Individual.phone_numbers, str).ilike(f"%{phone}%")  # Fallback
                )
            )
        if status:
            query = query.filter(Individual.status == status)
        if user_id:
            query = query.filter(Individual.user_id == user_id)

        # Búsqueda global (compatibilidad exacta)
        if search:
            search_filter = or_(
                Individual.first_name.ilike(f"%{search}%"),
                Individual.last_name.ilike(f"%{search}%"),
                Individual.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Filtros dinámicos adicionales (nueva funcionalidad)
        if additional_filters:
            for key, value in additional_filters.items():
                if hasattr(Individual, key) and value:
                    attr = getattr(Individual, key)
                    if key in ['id', 'user_id']:
                        query = query.filter(attr == int(value))
                    elif key in ['is_active', 'is_deleted']:
                        query = query.filter(attr == (str(value).lower() == 'true'))
                    else:
                        query = query.filter(attr.ilike(f"%{value}%"))

        # Ordenamiento
        if order_by and hasattr(Individual, order_by):
            order_attr = getattr(Individual, order_by)
            if order_desc:
                query = query.order_by(order_attr.desc())
            else:
                query = query.order_by(order_attr)

        # Paginación
        offset = (page - 1) * limit
        return query.offset(offset).limit(limit).all()

    def create_individual_compatible(self, individual_data: Dict[str, Any]) -> Individual:
        """
        Crea individuo manteniendo compatibilidad con estructura existente.

        Mapea campos del formato antiguo al nuevo modelo extendido.
        """
        # Validar email único
        if self.find_by_email(individual_data.get('email')):
            raise EntityAlreadyExistsError("Individual", "email", individual_data.get('email'))

        # Mapear campos del formato antiguo al nuevo
        mapped_data = self._map_legacy_to_new_format(individual_data)

        return self.create(mapped_data)

    def update_individual_compatible(
        self,
        individual_id: int,
        update_data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Individual:
        """
        Actualiza individuo manteniendo compatibilidad.
        """
        individual = self.get_by_id(individual_id)
        if not individual:
            raise EntityNotFoundError("Individual", individual_id)

        # Validar email único si se está cambiando
        if 'email' in update_data and update_data['email'] != individual.email:
            if self.find_by_email(update_data['email']):
                raise EntityAlreadyExistsError("Individual", "email", update_data['email'])

        # Mapear datos del formato antiguo
        mapped_data = self._map_legacy_to_new_format(update_data)

        # Agregar auditoría
        if updated_by:
            mapped_data['updated_by'] = updated_by

        return self.update(individual_id, mapped_data)

    def soft_delete_individual(self, individual_id: int, deleted_by: Optional[int] = None) -> bool:
        """
        Soft delete manteniendo compatibilidad exacta con auditoría completa.
        """
        from datetime import datetime

        individual = self.get_by_id(individual_id)
        if not individual:
            raise EntityNotFoundError("Individual", individual_id)

        # Soft delete con campos de auditoría completos
        update_data = {
            'is_active': False,
            'is_deleted': True,
            'deleted_at': datetime.utcnow(),
            'deleted_by': deleted_by,
            'updated_by': deleted_by  # También actualizar updated_by
        }

        self.update(individual_id, update_data)
        return True

    # ==================== NUEVAS FUNCIONALIDADES EXTENDIDAS ====================

    def find_by_document(self, document_number: str) -> Optional[Individual]:
        """Nueva funcionalidad: buscar por documento."""
        return self.db.query(Individual).filter(
            Individual.document_number == document_number
        ).first()

    def find_by_phone_array(self, phone: str) -> List[Individual]:
        """Nueva funcionalidad: buscar en array de teléfonos."""
        return self.db.query(Individual).filter(
            Individual.phone_numbers.any(phone)
        ).all()

    def get_by_status_enum(self, status: IndividualStatusEnum) -> List[Individual]:
        """Nueva funcionalidad: filtrar por enum de status."""
        return self.db.query(Individual).filter(
            Individual.status == status,
            Individual.is_active == True
        ).all()

    def get_individuals_with_user(self) -> List[Individual]:
        """Nueva funcionalidad: individuos que tienen usuario asociado."""
        return self.db.query(Individual).filter(
            Individual.user_id.isnot(None),
            Individual.is_active == True
        ).all()

    def get_verified_individuals(self) -> List[Individual]:
        """Nueva funcionalidad: individuos verificados."""
        return self.db.query(Individual).filter(
            Individual.is_verified == True,
            Individual.is_active == True
        ).all()

    def search_by_skills(self, skill: str) -> List[Individual]:
        """Nueva funcionalidad: buscar por habilidades en skill_details (JSONB)."""
        from sqlalchemy import cast, String
        return self.db.query(Individual).filter(
            cast(Individual.skill_details, String).ilike(f'%"name": "{skill}"%'),
            Individual.is_active == True
        ).all()

    # ==================== MÉTODOS AVANZADOS DE SKILLS ====================

    def search_by_skill_category(self, category: str) -> List[Individual]:
        """Buscar individuos por categoría de skill."""
        return self.db.query(Individual).filter(
            Individual.skill_details.op('?')([{"category": category}]),
            Individual.is_active == True
        ).all()

    def search_by_skill_level(self, skill_name: str, level: str) -> List[Individual]:
        """Buscar individuos con skill específica en nivel mínimo."""
        return self.db.query(Individual).filter(
            Individual.skill_details.op('@>')([{"name": skill_name, "level": level}]),
            Individual.is_active == True
        ).all()

    def get_individuals_with_expert_skills(self) -> List[Individual]:
        """Obtener individuos con al menos una skill de nivel EXPERT o MASTER."""
        return self.db.query(Individual).filter(
            or_(
                Individual.skill_details.op('@>')([{"level": "EXPERT"}]),
                Individual.skill_details.op('@>')([{"level": "MASTER"}])
            ),
            Individual.is_active == True
        ).all()

    def search_by_skill_and_experience(self, skill_name: str, min_years: int) -> List[Individual]:
        """Buscar individuos con skill y años mínimos de experiencia."""
        return self.db.query(Individual).filter(
            Individual.skill_details.op('@>')([{"name": skill_name}]),
            Individual.skill_details.op('?')([{"years_experience": min_years}]),
            Individual.is_active == True
        ).all()

    def get_skills_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas globales de skills."""
        total_individuals = self.db.query(Individual).filter(Individual.is_active == True).count()
        individuals_with_skills = self.db.query(Individual).filter(
            Individual.skills.isnot(None),
            func.array_length(Individual.skills, 1) > 0,
            Individual.is_active == True
        ).count()

        individuals_with_detailed_skills = self.db.query(Individual).filter(
            Individual.skill_details.isnot(None),
            Individual.is_active == True
        ).count()

        return {
            "total_individuals": total_individuals,
            "individuals_with_skills": individuals_with_skills,
            "individuals_with_detailed_skills": individuals_with_detailed_skills,
            "percentage_with_skills": round((individuals_with_skills / total_individuals * 100), 2) if total_individuals > 0 else 0
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Nueva funcionalidad: estadísticas de individuos."""
        total = self.db.query(Individual).count()
        active = self.db.query(Individual).filter(Individual.is_active == True).count()
        verified = self.db.query(Individual).filter(Individual.is_verified == True).count()
        with_user = self.db.query(Individual).filter(Individual.user_id.isnot(None)).count()

        return {
            "total_individuals": total,
            "active_individuals": active,
            "verified_individuals": verified,
            "individuals_with_user": with_user,
            "inactive_individuals": total - active
        }

    # ==================== MÉTODOS PRIVADOS ====================

    def _map_legacy_to_new_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapea datos del formato legacy al nuevo modelo extendido.

        Mantiene compatibilidad mapeando:
        - name -> first_name
        - Campos adicionales se mantienen igual
        """
        mapped = data.copy()

        # Mapear name del formato antiguo a first_name del nuevo
        if 'name' in mapped:
            mapped['first_name'] = mapped.pop('name')

        # Si viene phone como string, convertir a array
        if 'phone' in mapped and mapped['phone']:
            if not mapped.get('phone_numbers'):
                mapped['phone_numbers'] = [mapped['phone']]

        # Mapear status string a enum si es necesario
        if 'status' in mapped and isinstance(mapped['status'], str):
            try:
                # Convertir a mayúsculas para compatibilidad con enum
                mapped['status'] = IndividualStatusEnum(mapped['status'].upper())
            except ValueError:
                # Si no es un enum válido, usar ACTIVE por defecto
                mapped['status'] = IndividualStatusEnum.ACTIVE

        return mapped

    def _prepare_legacy_response(self, individual: Individual) -> Dict[str, Any]:
        """
        Prepara respuesta en formato legacy para mantener compatibilidad.
        """
        return {
            "id": individual.id,
            "user_id": individual.user_id,
            "name": individual.first_name,  # Mapear de vuelta
            "last_name": individual.last_name,
            "email": individual.email,
            "phone": individual.primary_phone,  # Primer teléfono del array
            "address": individual.address_street,  # Campo principal de dirección
            "status": individual.status.value if individual.status else "active",
            "is_active": individual.is_active,
            "created_at": individual.created_at,
            "updated_at": individual.updated_at
        }