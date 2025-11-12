"""
Router para Individual con nueva arquitectura

Mantiene compatibilidad 100% con endpoints existentes en modules/individuals/routes.py
mientras permite funcionalidades extendidas del nuevo modelo.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

# Importaciones compatibles con estructura existente
from database import get_db
from auth import require_admin, require_manager_or_admin, require_collaborator_or_better, require_any_user

# Importaciones de la nueva arquitectura
from app.entities.individuals.controllers.individual_controller import IndividualController
from app.shared.dependencies import get_current_user, get_pagination_params, get_common_filters

# Router compatible con el existente
router = APIRouter(prefix="/individuals", tags=["Individuals"])


# ==================== DEPENDENCIAS ====================

def get_individual_controller(db: Session = Depends(get_db)) -> IndividualController:
    """Dependencia para obtener el controller de Individual."""
    return IndividualController(db)


# ==================== ENDPOINTS DE COMPATIBILIDAD TOTAL ====================
# Estos endpoints mantienen exactamente la misma firma y comportamiento
# que los existentes en modules/individuals/routes.py

@router.post("/", summary="Crear individuo")
def create_individual(
    individual_data: dict,  # Mantenemos dict para compatibilidad total
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_collaborator_or_better)
):
    """
    Crear individuo - COMPATIBILIDAD TOTAL con POST /individuals/

    Mantiene exactamente el mismo comportamiento que el endpoint original:
    - Validación de email único
    - Estructura de respuesta idéntica
    - Roles de autorización iguales
    """
    return controller.create_individual(individual_data)


@router.get("/", response_model=List[dict], summary="Listar individuos")
def get_individuals(
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Listar individuos activos - COMPATIBILIDAD TOTAL con GET /individuals/

    Mantiene exactamente el mismo comportamiento:
    - Solo individuos con is_active=True
    - Mismo formato de respuesta IndividualResponse
    - Mismos roles de autorización
    """
    return controller.get_individuals()


@router.get("/search", response_model=List[dict], summary="Buscar individuos con filtros dinámicos")
def search_individuals(
    request: Request,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user),
    # Filtros específicos comunes - EXACTAMENTE IGUALES AL ORIGINAL
    name: Optional[str] = Query(None, description="Filtrar por nombre"),
    last_name: Optional[str] = Query(None, description="Filtrar por apellido"),
    email: Optional[str] = Query(None, description="Filtrar por email"),
    phone: Optional[str] = Query(None, description="Filtrar por teléfono"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    user_id: Optional[int] = Query(None, description="Filtrar por user_id"),
    # Filtros de búsqueda
    search: Optional[str] = Query(None, description="Búsqueda global en name, last_name, email"),
    # Paginación
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(100, ge=1, le=1000, description="Registros por página"),
    # Ordenamiento
    order_by: Optional[str] = Query("id", description="Campo para ordenar"),
    order_desc: bool = Query(False, description="Orden descendente")
):
    """
    Búsqueda avanzada - COMPATIBILIDAD TOTAL con GET /persons/search

    Mantiene EXACTAMENTE la misma funcionalidad:
    - Todos los filtros específicos idénticos
    - Búsqueda global igual
    - Filtros dinámicos desde query params
    - Paginación idéntica
    - Ordenamiento igual
    """
    return controller.search_individuals(
        request=request,
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
        order_desc=order_desc
    )


@router.get("/{individual_id}", response_model=dict, summary="Obtener individuo específica")
def get_individual(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener individuo específica - COMPATIBILIDAD TOTAL con GET /persons/{individual_id}

    Mantiene exactamente el mismo comportamiento:
    - Solo individuos activas
    - Mismo formato de respuesta
    - Error 404 si no existe
    """
    return controller.get_individual(individual_id)


@router.put("/{individual_id}", summary="Actualizar individuo")
def update_individual(
    individual_id: int,
    individual_data: dict,  # Mantenemos dict para compatibilidad
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_collaborator_or_better)
):
    """
    Actualizar individuo - COMPATIBILIDAD TOTAL con PUT /persons/{individual_id}

    Mantiene exactamente el mismo comportamiento:
    - Validación de email único
    - Validación de user_id (0 -> None)
    - Auditoría con updated_by
    - Misma estructura de respuesta
    """
    return controller.update_individual(individual_id, individual_data, current_user.id)


@router.delete("/{individual_id}", summary="Eliminar individuo (soft delete)")
def delete_individual(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_admin)
):
    """
    Eliminar individuo - COMPATIBILIDAD TOTAL con DELETE /persons/{individual_id}

    Mantiene exactamente el mismo comportamiento:
    - Soft delete (is_active=False, is_deleted=True)
    - Solo admins pueden eliminar
    - Auditoría con updated_by
    - Misma respuesta
    """
    return controller.delete_individual(individual_id, current_user.id)


@router.post("/with-user", summary="Crear individuo con usuario asociado")
def create_individual_with_user(
    data: dict,  # Mantenemos dict para compatibilidad total
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_manager_or_admin)
):
    """
    Crear individuo con usuario - COMPATIBILIDAD TOTAL con POST /persons/with-user

    Mantiene exactamente el mismo comportamiento:
    - Transacción atómica usuario + individuo
    - Validaciones de emails únicos
    - Estructura de respuesta idéntica
    - Rollback en caso de error
    """
    return controller.create_individual_with_user(data)


# ==================== NUEVOS ENDPOINTS EXTENDIDOS ====================
# Estos endpoints aprovechan las nuevas funcionalidades del modelo extendido

@router.post("/extended", summary="Crear individuo con funcionalidades extendidas")
def create_individual_extended(
    individual_data: dict,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_collaborator_or_better)
):
    """
    Crear individuo usando todas las funcionalidades del nuevo modelo extendido.

    Permite usar todos los nuevos tipos de datos:
    - Enums (document_type, gender, marital_status, etc.)
    - Arrays (phone_numbers, skills, languages)
    - JSON/JSONB (preferences, additional_data)
    - Decimals (height, weight, salary)
    - Datos de ubicación detallados
    """
    return controller.create_individual_extended(individual_data)


@router.get("/search/by-document/{document_number}", summary="Buscar individuo por documento")
def find_by_document(
    document_number: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Buscar individuo por número de documento.

    Nueva funcionalidad que aprovecha el campo document_number
    del modelo extendido.
    """
    return controller.find_by_document(document_number)


@router.get("/search/by-phone/{phone}", summary="Buscar individuos por teléfono")
def find_by_phone(
    phone: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Buscar individuos por número de teléfono.

    Nueva funcionalidad que busca en el array phone_numbers
    del modelo extendido.
    """
    return controller.find_by_phone(phone)


@router.get("/filter/by-status/{status}", summary="Filtrar individuos por status enum")
def get_by_status(
    status: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener individuos por status usando enum.

    Nueva funcionalidad que aprovecha IndividualStatusEnum.
    Valores válidos: ACTIVE, INACTIVE, SUSPENDED, PENDING_VERIFICATION, ARCHIVED
    """
    return controller.get_by_status(status)


@router.get("/filter/verified", summary="Obtener individuos verificadas")
def get_verified_individuals(
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener todas las individuos verificadas.

    Nueva funcionalidad usando el campo is_verified del modelo extendido.
    """
    return controller.get_verified_individuals()


@router.patch("/{individual_id}/verify", summary="Verificar individuo")
def verify_individual(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_manager_or_admin)
):
    """
    Marcar individuo como verificada.

    Nueva funcionalidad que requiere:
    - Número de documento presente
    - Al menos email o teléfono
    - Permisos de manager o admin
    """
    return controller.verify_individual(individual_id, current_user.id)


@router.get("/search/by-skill/{skill}", summary="Buscar individuos por habilidad")
def search_by_skills(
    skill: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Buscar individuos que tengan una habilidad específica.

    Nueva funcionalidad que busca en el array skills del modelo extendido.
    """
    return controller.search_by_skills(skill)


@router.get("/statistics", summary="Obtener estadísticas de individuos")
def get_statistics(
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_manager_or_admin)
):
    """
    Obtener estadísticas generales de individuos.

    Nueva funcionalidad que retorna:
    - Total de individuos
    - Individuos activas
    - Individuos verificadas
    - Individuos con usuario asociado
    - Individuos inactivas
    """
    return controller.get_statistics()


@router.get("/{individual_id}/age", summary="Calcular edad de individuo")
def get_individual_age(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Calcular edad de individuo desde fecha de nacimiento.

    Nueva funcionalidad que usa la propiedad calculated_age
    del modelo extendido.
    """
    return controller.get_individual_age(individual_id)


@router.get("/{individual_id}/bmi", summary="Calcular BMI de individuo")
def get_individual_bmi(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Calcular Índice de Masa Corporal de individuo.

    Nueva funcionalidad que usa altura y peso del modelo extendido
    para calcular BMI automáticamente.
    """
    return controller.get_individual_bmi(individual_id)


@router.get("/{individual_id}/validate", summary="Validar consistencia de datos")
def validate_individual_consistency(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Validar consistencia de datos de individuo.

    Nueva funcionalidad que verifica:
    - Coherencia entre edad y fecha de nacimiento
    - Presencia de métodos de contacto
    - Validez de documento si está verificado
    """
    return controller.validate_individual_consistency(individual_id)


# ==================== ENDPOINTS DE UTILIDAD ====================

@router.get("/enums/document-types", summary="Obtener tipos de documento válidos")
def get_document_types(current_user=Depends(require_any_user)):
    """
    Obtener lista de tipos de documento válidos.

    Utilidad para formularios y validaciones frontend.
    """
    from app.entities.individuals.schemas.enums import DocumentTypeEnum, DOCUMENT_TYPE_DISPLAY_NAMES
    return {
        "values": [item.value for item in DocumentTypeEnum],
        "display_names": DOCUMENT_TYPE_DISPLAY_NAMES
    }


@router.get("/enums/genders", summary="Obtener géneros válidos")
def get_genders(current_user=Depends(require_any_user)):
    """
    Obtener lista de géneros válidos.

    Utilidad para formularios y validaciones frontend.
    """
    from app.entities.individuals.schemas.enums import GenderEnum, GENDER_DISPLAY_NAMES
    return {
        "values": [item.value for item in GenderEnum],
        "display_names": GENDER_DISPLAY_NAMES
    }


@router.get("/enums/marital-status", summary="Obtener estados civiles válidos")
def get_marital_status(current_user=Depends(require_any_user)):
    """
    Obtener lista de estados civiles válidos.

    Utilidad para formularios y validaciones frontend.
    """
    from app.entities.individuals.schemas.enums import MaritalStatusEnum, MARITAL_STATUS_DISPLAY_NAMES
    return {
        "values": [item.value for item in MaritalStatusEnum],
        "display_names": MARITAL_STATUS_DISPLAY_NAMES
    }


@router.get("/enums/individual-status", summary="Obtener estados de individuo válidos")
def get_individual_status(current_user=Depends(require_any_user)):
    """
    Obtener lista de estados de individuo válidos.

    Utilidad para formularios y validaciones frontend.
    """
    from app.entities.individuals.schemas.enums import IndividualStatusEnum
    return {
        "values": [item.value for item in IndividualStatusEnum]
    }


# ==================== ENDPOINTS AVANZADOS DE SKILLS ====================

@router.post("/{individual_id}/skills", summary="Añadir skill detallada a individuo")
def add_skill_to_individual(
    individual_id: int,
    skill_data: dict,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_collaborator_or_better)
):
    """
    Añadir skill detallada a una individuo.

    Body esperado:
    ```json
    {
        "name": "Python",
        "category": "TECHNICAL",
        "level": "ADVANCED",
        "years_experience": 4,
        "notes": "Frameworks Django y FastAPI"
    }
    ```

    Categorías válidas: TECHNICAL, LANGUAGE, SOFT_SKILL, TOOL, FRAMEWORK, PLATFORM, METHODOLOGY, CERTIFICATION, DOMAIN, OTHER
    Niveles válidos: BEGINNER, INTERMEDIATE, ADVANCED, EXPERT, MASTER
    """
    return controller.add_skill_to_individual(individual_id, skill_data, current_user.id)


@router.delete("/{individual_id}/skills/{skill_name}", summary="Eliminar skill de individuo")
def remove_skill_from_individual(
    individual_id: int,
    skill_name: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_collaborator_or_better)
):
    """
    Eliminar skill específica de una individuo.

    Elimina tanto del array simple como de los detalles JSONB.
    """
    return controller.remove_skill_from_individual(individual_id, skill_name, current_user.id)


@router.patch("/{individual_id}/skills/{skill_name}", summary="Actualizar nivel de skill")
def update_skill_level(
    individual_id: int,
    skill_name: str,
    update_data: dict,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_collaborator_or_better)
):
    """
    Actualizar nivel y detalles de una skill existente.

    Body esperado:
    ```json
    {
        "level": "EXPERT",
        "years_experience": 6,
        "notes": "Certificación avanzada obtenida"
    }
    ```
    """
    return controller.update_skill_level(individual_id, skill_name, update_data, current_user.id)


@router.get("/{individual_id}/skills/summary", summary="Resumen de skills de individuo")
def get_individual_skills_summary(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener resumen estadístico de skills de una individuo.

    Retorna:
    - Total de skills
    - Distribución por categoría
    - Distribución por nivel
    - Skills de nivel experto
    - Total años de experiencia
    """
    return controller.get_individual_skills_summary(individual_id)


@router.get("/{individual_id}/skills/category/{category}", summary="Skills por categoría")
def get_individual_skills_by_category(
    individual_id: int,
    category: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener skills de una individuo filtradas por categoría.

    Categorías válidas: TECHNICAL, LANGUAGE, SOFT_SKILL, TOOL, FRAMEWORK, PLATFORM, METHODOLOGY, CERTIFICATION, DOMAIN, OTHER
    """
    return controller.get_individual_skills_by_category(individual_id, category)


@router.get("/{individual_id}/skills/expert", summary="Skills de nivel experto")
def get_individual_expert_skills(
    individual_id: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener solo las skills de nivel EXPERT o MASTER de una individuo.
    """
    return controller.get_individual_expert_skills(individual_id)


@router.post("/{individual_id}/skills/validate", summary="Validar requisitos de skills")
def validate_individual_skill_requirements(
    individual_id: int,
    requirements: List[dict],
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Validar si una individuo cumple con requisitos específicos de skills.

    Body esperado:
    ```json
    [
        {"name": "Python", "level": "ADVANCED"},
        {"name": "SQL", "level": "INTERMEDIATE"},
        {"name": "Docker", "level": "BEGINNER"}
    ]
    ```

    Retorna análisis detallado de qué requisitos cumple y cuáles no.
    """
    return controller.validate_individual_skill_requirements(individual_id, requirements)


# ==================== BÚSQUEDAS AVANZADAS DE SKILLS ====================

@router.get("/search/skills/category/{category}", summary="Buscar individuos por categoría de skill")
def search_by_skill_category(
    category: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Buscar individuos que tengan skills en una categoría específica.

    Categorías válidas: TECHNICAL, LANGUAGE, SOFT_SKILL, TOOL, FRAMEWORK, PLATFORM, METHODOLOGY, CERTIFICATION, DOMAIN, OTHER
    """
    return controller.search_by_skill_category(category)


@router.get("/search/skills/{skill_name}/level/{level}", summary="Buscar por skill y nivel")
def search_by_skill_level(
    skill_name: str,
    level: str,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Buscar individuos con una skill específica en el nivel indicado o superior.

    Niveles válidos: BEGINNER, INTERMEDIATE, ADVANCED, EXPERT, MASTER
    """
    return controller.search_by_skill_level(skill_name, level)


@router.get("/search/skills/{skill_name}/experience/{min_years}", summary="Buscar por skill y experiencia")
def search_by_skill_and_experience(
    skill_name: str,
    min_years: int,
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Buscar individuos con una skill específica y años mínimos de experiencia.
    """
    return controller.search_by_skill_and_experience(skill_name, min_years)


@router.get("/search/skills/experts", summary="Buscar individuos con skills expertas")
def get_individuals_with_expert_skills(
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_any_user)
):
    """
    Obtener individuos que tengan al menos una skill de nivel EXPERT o MASTER.
    """
    return controller.get_individuals_with_expert_skills()


# ==================== ESTADÍSTICAS DE SKILLS ====================

@router.get("/statistics/skills", summary="Estadísticas globales de skills")
def get_skills_global_statistics(
    controller: IndividualController = Depends(get_individual_controller),
    current_user=Depends(require_manager_or_admin)
):
    """
    Obtener estadísticas globales de skills en el sistema.

    Solo accesible para managers y admins.
    """
    return controller.get_skills_global_statistics()


# ==================== ENDPOINTS DE UTILIDAD PARA SKILLS ====================

@router.get("/enums/skill-categories", summary="Obtener categorías de skills válidas")
def get_skill_categories(current_user=Depends(require_any_user)):
    """
    Obtener lista de categorías de skills válidas.

    Utilidad para formularios y validaciones frontend.
    """
    from app.entities.individuals.schemas.enums import SkillCategoryEnum, SKILL_CATEGORY_DISPLAY_NAMES
    return {
        "values": [item.value for item in SkillCategoryEnum],
        "display_names": SKILL_CATEGORY_DISPLAY_NAMES
    }


@router.get("/enums/skill-levels", summary="Obtener niveles de skills válidos")
def get_skill_levels(current_user=Depends(require_any_user)):
    """
    Obtener lista de niveles de skills válidos.

    Utilidad para formularios y validaciones frontend.
    """
    from app.entities.individuals.schemas.enums import SkillLevelEnum, SKILL_LEVEL_DISPLAY_NAMES
    return {
        "values": [item.value for item in SkillLevelEnum],
        "display_names": SKILL_LEVEL_DISPLAY_NAMES
    }