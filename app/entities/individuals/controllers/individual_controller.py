"""
Controller para Individual

Maneja la lógica de presentación y coordina entre
Service layer y Router layer. Mantiene compatibilidad
total con los endpoints existentes.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.entities.individuals.services.individual_service import IndividualService
from app.entities.individuals.models.individual import Individual
from app.entities.individuals.schemas.enums import IndividualStatusEnum
from app.shared.exceptions import (
    BaseAppException,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    EntityValidationError,
    BusinessRuleError
)


class IndividualController:
    """
    Controller para manejar requests HTTP de individuals.

    Coordina entre Router y Service layer, manejando:
    - Validación de input HTTP
    - Transformación de datos
    - Manejo de errores
    - Formateo de respuestas
    """

    def __init__(self, db: Session):
        self.db = db
        self.service = IndividualService(db)

    # ==================== ENDPOINTS DE COMPATIBILIDAD ====================

    def create_individual(self, individual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear individuo - Compatibilidad con POST /individuals/

        Args:
            individual_data: Datos en formato legacy

        Returns:
            Respuesta con ID, name, last_name, email
        """
        try:
            individual = self.service.create_individual_legacy(individual_data)
            return {
                "id": individual.id,
                "name": individual.first_name,
                "last_name": individual.last_name,
                "email": individual.email
            }
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individuals(self) -> List[Dict[str, Any]]:
        """
        Listar individuos activos - Compatibilidad con GET /individuals/

        Returns:
            Lista de individuos en formato IndividualResponse
        """
        try:
            individuals = self.service.get_all_active_individuals()
            return [self._to_individual_response(individual) for individual in individuals]
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def search_individuals(
        self,
        request: Request,
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
        order_desc: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda avanzada - Compatibilidad con GET /individuals/search

        Mantiene exactamente la misma funcionalidad que el endpoint original
        incluyendo filtros dinámicos desde query parameters.
        """
        try:
            # Extraer filtros dinámicos adicionales del request
            additional_filters = {}
            excluded_params = {
                'name', 'last_name', 'email', 'phone', 'status', 'user_id',
                'search', 'page', 'limit', 'order_by', 'order_desc'
            }

            for key, value in request.query_params.items():
                if key not in excluded_params and value:
                    additional_filters[key] = value

            individuals = self.service.search_individuals(
                name=name,
                last_name=last_name,
                email=email,
                phone=phone,
                status=status,
                user_id=user_id,
                search=search,
                page=page,
                limit=limit,
                order_by=order_by,
                order_desc=order_desc,
                additional_filters=additional_filters
            )

            return [self._to_individual_response(individual) for individual in individuals]

        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individual(self, individual_id: int) -> Dict[str, Any]:
        """
        Obtener individuo específico - Compatibilidad con GET /individuals/{individual_id}
        """
        try:
            individual = self.service.get_individual_by_id(individual_id)
            return self._to_individual_response(individual)
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def update_individual(
        self,
        individual_id: int,
        update_data: Dict[str, Any],
        current_user_id: int
    ) -> Dict[str, Any]:
        """
        Actualizar individuo - Compatibilidad con PUT /individuals/{individual_id}
        """
        try:
            individual = self.service.update_individual_legacy(
                individual_id, update_data, current_user_id
            )
            return {
                "id": individual.id,
                "name": individual.first_name,
                "last_name": individual.last_name,
                "email": individual.email
            }
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except EntityAlreadyExistsError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def delete_individual(self, individual_id: int, current_user_id: int) -> Dict[str, str]:
        """
        Eliminar individuo (soft delete) - Compatibilidad con DELETE /individuals/{individual_id}
        """
        try:
            self.service.delete_individual(individual_id, current_user_id)
            return {"message": "Individuo eliminado correctamente"}
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def create_individual_with_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear individuo con usuario - Compatibilidad con POST /individuals/with-user
        """
        try:
            # Separar datos de usuario y individuo
            user_data = {
                'user_email': data.get('user_email'),
                'user_name': data.get('user_name'),
                'user_password': data.get('user_password'),
                'user_role': data.get('user_role', 4)
            }

            individual_data = {
                'name': data.get('name'),  # Formato legacy
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'address': data.get('address'),
                'status': data.get('status', 'active')
            }

            user_result, individual_result = self.service.create_individual_with_user(
                user_data, individual_data
            )

            return {
                "user": user_result,
                "individual": individual_result
            }

        except EntityAlreadyExistsError as e:
            if "User" in e.message:
                raise HTTPException(status_code=400, detail="Email de usuario ya existe")
            else:
                raise HTTPException(status_code=400, detail="Email de individuo ya existe")
        except EntityValidationError as e:
            # Incluir los detalles de validación en la respuesta
            raise HTTPException(
                status_code=e.status_code,
                detail={
                    "message": e.message,
                    "errors": e.details.get('validation_errors', {})
                }
            )
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creando usuario y individuo: {str(e)}")

    # ==================== NUEVOS ENDPOINTS EXTENDIDOS ====================

    def create_individual_extended(self, individual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear individuo con funcionalidades extendidas del nuevo modelo.
        """
        try:
            individual = self.service.create_individual_extended(individual_data)
            return self._to_extended_response(individual)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def find_by_document(self, document_number: str) -> Dict[str, Any]:
        """
        Buscar individuo por número de documento.
        """
        try:
            individual = self.service.find_by_document(document_number)
            if not individual:
                raise HTTPException(status_code=404, detail="Individuo no encontrado")
            return self._to_extended_response(individual)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def find_by_phone(self, phone: str) -> List[Dict[str, Any]]:
        """
        Buscar individuos por número de teléfono.
        """
        try:
            individuals = self.service.find_by_phone_number(phone)
            return [self._to_extended_response(individual) for individual in individuals]
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Obtener individuos por status usando enum.
        """
        try:
            status_enum = IndividualStatusEnum(status)
            individuals = self.service.get_individuals_by_status(status_enum)
            return [self._to_extended_response(individual) for individual in individuals]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_verified_individuals(self) -> List[Dict[str, Any]]:
        """
        Obtener individuos verificados.
        """
        try:
            individuals = self.service.get_verified_individuals()
            return [self._to_extended_response(individual) for individual in individuals]
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def verify_individual(self, individual_id: int, current_user_id: int) -> Dict[str, Any]:
        """
        Verificar individuo.
        """
        try:
            individual = self.service.verify_individual(individual_id, current_user_id)
            return {
                "message": "Individuo verificado exitosamente",
                "individual": self._to_extended_response(individual)
            }
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def search_by_skills(self, skill: str) -> List[Dict[str, Any]]:
        """
        Buscar individuos por habilidad.
        """
        try:
            individuals = self.service.search_by_skills(skill)
            return [self._to_extended_response(individual) for individual in individuals]
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    # ==================== CONTROLADORES AVANZADOS DE SKILLS ====================

    def add_skill_to_individual(
        self,
        individual_id: int,
        skill_data: Dict[str, Any],
        current_user_id: int
    ) -> Dict[str, Any]:
        """
        Añadir skill detallada a individuo.
        """
        try:
            self._validate_request_data(skill_data, ["name", "category", "level"])

            individual = self.service.add_skill_to_individual(
                individual_id=individual_id,
                skill_name=skill_data["name"],
                category=skill_data["category"],
                level=skill_data["level"],
                years_experience=skill_data.get("years_experience", 0),
                notes=skill_data.get("notes"),
                updated_by=current_user_id
            )

            return {
                "message": "Skill añadida exitosamente",
                "individual_id": individual_id,
                "skill_added": {
                    "name": skill_data["name"],
                    "category": skill_data["category"],
                    "level": skill_data["level"]
                },
                "skills_summary": individual.get_skills_summary()
            }

        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def remove_skill_from_individual(
        self,
        individual_id: int,
        skill_name: str,
        current_user_id: int
    ) -> Dict[str, Any]:
        """
        Eliminar skill de individuo.
        """
        try:
            individual = self.service.remove_skill_from_individual(
                individual_id=individual_id,
                skill_name=skill_name,
                updated_by=current_user_id
            )

            return {
                "message": "Skill eliminada exitosamente",
                "individual_id": individual_id,
                "skill_removed": skill_name,
                "skills_summary": individual.get_skills_summary()
            }

        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def search_by_skill_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Buscar individuos por categoría de skill.
        """
        try:
            individuals = self.service.search_by_skill_category(category)
            return [self._to_extended_response(individual) for individual in individuals]
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def search_by_skill_level(self, skill_name: str, level: str) -> List[Dict[str, Any]]:
        """
        Buscar individuos con skill específica en nivel mínimo.
        """
        try:
            individuals = self.service.search_by_skill_level(skill_name, level)
            return [self._to_extended_response(individual) for individual in individuals]
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individuals_with_expert_skills(self) -> List[Dict[str, Any]]:
        """
        Obtener individuos con skills de nivel experto.
        """
        try:
            individuals = self.service.get_individuals_with_expert_skills()
            return [self._to_extended_response(individual) for individual in individuals]
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def search_by_skill_and_experience(self, skill_name: str, min_years: int) -> List[Dict[str, Any]]:
        """
        Buscar individuos con skill y años mínimos de experiencia.
        """
        try:
            individuals = self.service.search_by_skill_and_experience(skill_name, min_years)
            return [self._to_extended_response(individual) for individual in individuals]
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individual_skills_summary(self, individual_id: int) -> Dict[str, Any]:
        """
        Obtener resumen de skills de individuo.
        """
        try:
            summary = self.service.get_individual_skills_summary(individual_id)
            return {
                "individual_id": individual_id,
                "skills_summary": summary
            }
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individual_skills_by_category(self, individual_id: int, category: str) -> Dict[str, Any]:
        """
        Obtener skills de individuo por categoría.
        """
        try:
            skills = self.service.get_individual_skills_by_category(individual_id, category)
            return {
                "individual_id": individual_id,
                "category": category,
                "skills": skills
            }
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individual_expert_skills(self, individual_id: int) -> Dict[str, Any]:
        """
        Obtener skills de nivel experto de individuo.
        """
        try:
            expert_skills = self.service.get_individual_expert_skills(individual_id)
            return {
                "individual_id": individual_id,
                "expert_skills": expert_skills
            }
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def validate_individual_skill_requirements(
        self,
        individual_id: int,
        requirements: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Validar si individuo cumple requisitos de skills.
        """
        try:
            # Validar formato de requisitos
            for req in requirements:
                if not req.get("name") or not req.get("level"):
                    raise HTTPException(
                        status_code=422,
                        detail="Cada requisito debe tener 'name' y 'level'"
                    )

            validation_result = self.service.validate_individual_skill_requirements(
                individual_id, requirements
            )
            return validation_result

        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def update_skill_level(
        self,
        individual_id: int,
        skill_name: str,
        update_data: Dict[str, Any],
        current_user_id: int
    ) -> Dict[str, Any]:
        """
        Actualizar nivel de skill existente.
        """
        try:
            self._validate_request_data(update_data, ["level"])

            individual = self.service.update_skill_level(
                individual_id=individual_id,
                skill_name=skill_name,
                new_level=update_data["level"],
                years_experience=update_data.get("years_experience"),
                notes=update_data.get("notes"),
                updated_by=current_user_id
            )

            return {
                "message": "Nivel de skill actualizado exitosamente",
                "individual_id": individual_id,
                "skill_name": skill_name,
                "new_level": update_data["level"],
                "skill_detail": individual.get_skill_detail(skill_name)
            }

        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrada")
        except BusinessRuleError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_skills_global_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas globales de skills.
        """
        try:
            return self.service.get_skills_global_statistics()
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de individuos.
        """
        try:
            return self.service.get_individual_statistics()
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individual_age(self, individual_id: int) -> Dict[str, Any]:
        """
        Calcular edad de individuo.
        """
        try:
            age = self.service.calculate_individual_age(individual_id)
            return {"individual_id": individual_id, "age": age}
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def get_individual_bmi(self, individual_id: int) -> Dict[str, Any]:
        """
        Calcular BMI de individuo.
        """
        try:
            bmi = self.service.get_individual_bmi(individual_id)
            return {"individual_id": individual_id, "bmi": bmi}
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    def validate_individual_consistency(self, individual_id: int) -> Dict[str, Any]:
        """
        Validar consistencia de datos de individuo.
        """
        try:
            errors = self.service.validate_individual_consistency(individual_id)
            return {
                "individual_id": individual_id,
                "is_consistent": len(errors) == 0,
                "validation_errors": errors
            }
        except EntityNotFoundError:
            raise HTTPException(status_code=404, detail="Individuo no encontrado")
        except BaseAppException as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    # ==================== MÉTODOS PRIVADOS DE TRANSFORMACIÓN ====================

    def _to_individual_response(self, individual: Individual) -> Dict[str, Any]:
        """
        Convierte Individual a formato IndividualResponse para compatibilidad.
        """
        return {
            "id": individual.id,
            "user_id": individual.user_id,
            "name": individual.first_name,  # Mapeo para compatibilidad
            "last_name": individual.last_name,
            "email": individual.email,
            "phone": individual.primary_phone,  # Primer teléfono del array
            "address": individual.address_street,  # Dirección principal
            "status": individual.status.value if individual.status else "active",
            "is_active": individual.is_active,
            "created_at": individual.created_at,
            "updated_at": individual.updated_at,
            "country": {
                "id": individual.country.id,
                "name": individual.country.name,
                "code": individual.country.iso_code_3
            } if individual.country else None,
            "state": {
                "id": individual.state.id,
                "name": individual.state.name,
                "code": individual.state.code
            } if individual.state else None
        }

    def _to_extended_response(self, individual: Individual) -> Dict[str, Any]:
        """
        Convierte Individual a formato extendido con todas las propiedades.
        """
        return {
            "id": individual.id,
            "user_id": individual.user_id,
            "first_name": individual.first_name,
            "last_name": individual.last_name,
            "full_name": individual.full_name,
            "email": individual.email,
            "document_type": individual.document_type.value if individual.document_type else None,
            "document_number": individual.document_number,
            "phone_numbers": individual.phone_numbers,
            "primary_phone": individual.primary_phone,
            "address": {
                "street": individual.address_street,
                "city": individual.address_city,
                "state": individual.address_state
            },
            "birth_info": {
                "birth_date": individual.birth_date,
                "age": individual.calculated_age,
                "birth_city": individual.birth_city,
                "birth_state": individual.birth_state,
                "birth_country": individual.birth_country
            },
            "physical_info": {
                "height": float(individual.height) if individual.height else None,
                "weight": float(individual.weight) if individual.weight else None,
                "bmi": individual.bmi
            },
            "status_info": {
                "status": individual.status.value if individual.status else None,
                "is_active": individual.is_active,
                "is_verified": individual.is_verified,
                "is_deleted": individual.is_deleted
            },
            "individuol_info": {
                "gender": individual.gender.value if individual.gender else None,
                "marital_status": individual.marital_status.value if individual.marital_status else None,
                "education_level": individual.education_level.value if individual.education_level else None,
                "employment_status": individual.employment_status.value if individual.employment_status else None
            },
            "skills": individual.skills,
            "languages": individual.languages,
            "preferences": individual.preferences,
            "additional_data": individual.additional_data,
            "audit_info": {
                "created_at": individual.created_at,
                "updated_at": individual.updated_at,
                "deleted_at": individual.deleted_at,
                "created_by": individual.created_by,
                "updated_by": individual.updated_by,
                "deleted_by": individual.deleted_by
            }
        }

    def _validate_request_data(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Valida que los campos requeridos estén presentes en el request.
        """
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Campos requeridos faltantes: {', '.join(missing_fields)}"
            )