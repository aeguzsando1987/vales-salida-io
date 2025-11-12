"""
Enums para la entidad Individual

Este módulo define los valores permitidos para campos categóricos
de la entidad Individual, demostrando el uso de Enums en SQLAlchemy y Pydantic.

🔧 INSTRUCCIONES PARA AGREGAR NUEVOS VALORES:

1. Para agregar nuevos tipos de documento:
   - Agregar el valor en DocumentTypeEnum
   - Actualizar el validator en validators.py si necesita validación específica
   - Agregar display name en DOCUMENT_TYPE_DISPLAY_NAMES

2. Para agregar nuevos géneros:
   - Agregar el valor en GenderEnum
   - Agregar display name en GENDER_DISPLAY_NAMES

3. Para agregar nuevos estados civiles:
   - Agregar el valor en MaritalStatusEnum
   - Agregar display name en MARITAL_STATUS_DISPLAY_NAMES

4. Para crear nuevos enums:
   - Heredar de (str, Enum) para compatibilidad con JSON
   - Usar UPPER_CASE para los nombres de valores
   - Crear diccionario de display names correspondiente
   - Actualizar el modelo Individual si es necesario

⚠️ IMPORTANTE: Al agregar valores a enums existentes, asegúrate de:
- No cambiar valores existentes (puede romper datos)
- Ejecutar migraciones de base de datos si es necesario
- Actualizar tests correspondientes
"""

from enum import Enum


class DocumentTypeEnum(str, Enum):
    """
    Tipos de documentos de identificación válidos.

    Hereda de str para compatibilidad con JSON y bases de datos.

    Ejemplos de uso:
        # En Pydantic schema:
        document_type: DocumentTypeEnum = DocumentTypeEnum.RFC

        # En API endpoint:
        @app.get("/individuals/{doc_type}")
        def get_by_doc_type(doc_type: DocumentTypeEnum):
            return f"Buscando por {doc_type.value}"

        # En base de datos:
        individual.document_type = DocumentTypeEnum.CURP

        # Validar valor:
        if doc_type == DocumentTypeEnum.RFC:
            validate_rfc_format(document_number)
    """
    RFC = "RFC"                    # Registro Federal de Contribuyentes (México)
    CURP = "CURP"                  # Clave Única de Registro de Población (México)
    PASSPORT = "PASSPORT"          # Pasaporte internacional
    DRIVER_LICENSE = "DRIVER_LICENSE"  # Licencia de conducir
    OTHER = "OTHER"                # Otros documentos (carta antecedentes, NSS, etc.)


class GenderEnum(str, Enum):
    """
    Géneros reconocidos en el sistema.

    Seguimos estándares internacionales de inclusión.

    Ejemplos de uso:
        # En modelo Individual:
        individual.gender = GenderEnum.MALE

        # En Pydantic schema:
        gender: Optional[GenderEnum] = None

        # En query de base de datos:
        males = db.query(Individual).filter(Individual.gender == GenderEnum.MALE).all()

        # Obtener display name:
        display = get_display_name(GenderEnum.MALE, GENDER_DISPLAY_NAMES)
        # Resultado: "Masculino"
    """
    MALE = "M"                     # Masculino
    FEMALE = "F"                   # Femenino
    PREFER_NOT_TO_SAY = "N"        # Prefiere no decir


class MaritalStatusEnum(str, Enum):
    """
    Estados civiles reconocidos.

    Basado en los estados civiles más comunes en sistemas latinos.
    """
    SINGLE = "SINGLE"              # Soltero/a
    MARRIED = "MARRIED"            # Casado/a
    DIVORCED = "DIVORCED"          # Divorciado/a
    WIDOWED = "WIDOWED"            # Viudo/a
    SEPARATED = "SEPARATED"        # Separado/a
    DOMESTIC_PARTNERSHIP = "DOMESTIC_PARTNERSHIP"  # Unión libre
    OTHER = "OTHER"                # Otro


class IndividualStatusEnum(str, Enum):
    """
    Estados de un individuo en el sistema.

    Permite categorizar individuos según su situación actual.

    Ejemplos de uso:
        # Filtrar individuos activos:
        active_individuals = db.query(Individual).filter(
            Individual.status == IndividualStatusEnum.ACTIVE
        ).all()

        # Validar transición de estado:
        if current_status == IndividualStatusEnum.PENDING_VERIFICATION:
            individual.status = IndividualStatusEnum.ACTIVE

        # En endpoint con query parameter:
        @app.get("/individuals")
        def list_individuals(status: Optional[IndividualStatusEnum] = None):
            # Si status es None, muestra todos
            # Si es ACTIVE, solo muestra activos

        # Valores por defecto:
        individual.status = IndividualStatusEnum.ACTIVE  # Default para nuevos individuos
    """
    ACTIVE = "ACTIVE"              # Activo en el sistema
    INACTIVE = "INACTIVE"          # Inactivo temporalmente
    SUSPENDED = "SUSPENDED"        # Suspendido por alguna razón
    PENDING_VERIFICATION = "PENDING_VERIFICATION"  # Pendiente de verificación
    ARCHIVED = "ARCHIVED"          # Archivado (no eliminar por historial)


class ContactPreferenceEnum(str, Enum):
    """
    Preferencias de contacto para comunicaciones.

    Define cómo prefiere la persona ser contactada.
    """
    EMAIL = "EMAIL"                # Preferencia por email
    PHONE = "PHONE"                # Preferencia por teléfono
    SMS = "SMS"                    # Preferencia por SMS
    MAIL = "MAIL"                  # Preferencia por correo postal
    NO_CONTACT = "NO_CONTACT"      # No desea ser contactado


class EducationLevelEnum(str, Enum):
    """
    Niveles educativos estándar.

    Basado en el sistema educativo mexicano pero adaptable.
    """
    NONE = "NONE"                  # Sin educación formal
    PRIMARY = "PRIMARY"            # Primaria
    SECONDARY = "SECONDARY"        # Secundaria
    HIGH_SCHOOL = "HIGH_SCHOOL"    # Preparatoria/Bachillerato
    TECHNICAL = "TECHNICAL"        # Técnico/Tecnólogo
    BACHELOR = "BACHELOR"          # Licenciatura
    MASTER = "MASTER"              # Maestría
    DOCTORATE = "DOCTORATE"        # Doctorado
    OTHER = "OTHER"                # Otro


class EmploymentStatusEnum(str, Enum):
    """
    Estados de empleo para contexto laboral.

    Útil para sistemas de RRHH o CRM empresariales.
    """
    EMPLOYED = "EMPLOYED"          # Empleado
    UNEMPLOYED = "UNEMPLOYED"      # Desempleado
    SELF_EMPLOYED = "SELF_EMPLOYED"  # Trabajador independiente
    STUDENT = "STUDENT"            # Estudiante
    RETIRED = "RETIRED"            # Jubilado
    OTHER = "OTHER"                # Otro


class SkillCategoryEnum(str, Enum):
    """
    Categorías de habilidades para mejor organización.

    Permite clasificar skills por tipo para filtrado y análisis.

    Ejemplos de uso:
        # En skill detail:
        skill_detail = {
            "name": "Python",
            "category": SkillCategoryEnum.TECHNICAL,
            "level": "ADVANCED"
        }

        # En búsqueda por categoría:
        technical_persons = person_service.get_by_skill_category(SkillCategoryEnum.TECHNICAL)

        # En validación:
        if skill_category == SkillCategoryEnum.LANGUAGE:
            validate_language_skill(skill_name)
    """
    TECHNICAL = "TECHNICAL"        # Habilidades técnicas (Python, SQL, etc.)
    LANGUAGE = "LANGUAGE"          # Idiomas (Español, Inglés, etc.)
    SOFT_SKILL = "SOFT_SKILL"      # Habilidades blandas (Liderazgo, Comunicación)
    TOOL = "TOOL"                  # Herramientas (Excel, Photoshop, etc.)
    FRAMEWORK = "FRAMEWORK"        # Frameworks (React, Django, etc.)
    PLATFORM = "PLATFORM"         # Plataformas (AWS, Azure, etc.)
    METHODOLOGY = "METHODOLOGY"    # Metodologías (Agile, Scrum, etc.)
    CERTIFICATION = "CERTIFICATION"  # Certificaciones (PMP, AWS Certified, etc.)
    DOMAIN = "DOMAIN"              # Conocimiento de dominio (Finanzas, Salud, etc.)
    OTHER = "OTHER"                # Otras habilidades


class SkillLevelEnum(str, Enum):
    """
    Niveles de competencia en habilidades.

    Define el grado de dominio que tiene una persona sobre una habilidad específica.

    Ejemplos de uso:
        # En skill detail:
        skill_detail = {
            "name": "Python",
            "level": SkillLevelEnum.ADVANCED,
            "years_experience": 4
        }

        # En filtrado por nivel:
        experts = person_service.get_by_skill_level("Python", SkillLevelEnum.EXPERT)

        # En validación de requisitos:
        if required_level == SkillLevelEnum.ADVANCED:
            candidates = filter_by_minimum_skill_level("Python", SkillLevelEnum.ADVANCED)
    """
    BEGINNER = "BEGINNER"          # Principiante (0-1 años)
    INTERMEDIATE = "INTERMEDIATE"  # Intermedio (1-3 años)
    ADVANCED = "ADVANCED"          # Avanzado (3-5 años)
    EXPERT = "EXPERT"              # Experto (5+ años)
    MASTER = "MASTER"              # Maestro (nivel de instructor/mentor)


# ==================== UTILIDADES PARA ENUMS ====================

def get_enum_values(enum_class) -> list:
    """
    Obtiene todos los valores de un enum como lista.

    Args:
        enum_class: Clase enum

    Returns:
        Lista de valores del enum

    Ejemplo:
        document_types = get_enum_values(DocumentTypeEnum)
        # Resultado: ['RFC', 'CURP', 'PASSPORT', 'DRIVER_LICENSE', 'OTHER']
    """
    return [item.value for item in enum_class]


def get_enum_choices(enum_class) -> list:
    """
    Obtiene pares (valor, valor) para usar en formularios.

    Args:
        enum_class: Clase enum

    Returns:
        Lista de tuplas (valor, valor)

    Ejemplo:
        choices = get_enum_choices(GenderEnum)
        # Resultado: [('M', 'M'), ('F', 'F'), ('O', 'O'), ('N', 'N')]
    """
    return [(item.value, item.value) for item in enum_class]


def validate_enum_value(value: str, enum_class, field_name: str = "Campo") -> str:
    """
    Valida que un valor pertenezca a un enum específico.

    Args:
        value: Valor a validar
        enum_class: Clase enum contra la cual validar
        field_name: Nombre del campo para mensajes de error

    Returns:
        Valor validado

    Raises:
        ValueError: Si el valor no es válido para el enum

    Ejemplo:
        gender = validate_enum_value("M", GenderEnum, "Género")
    """
    valid_values = get_enum_values(enum_class)
    if value not in valid_values:
        raise ValueError(f'{field_name} debe ser uno de: {", ".join(valid_values)}')
    return value


# ==================== MAPEOS PARA DISPLAY ====================

GENDER_DISPLAY_NAMES = {
    GenderEnum.MALE: "Masculino",
    GenderEnum.FEMALE: "Femenino",
    GenderEnum.PREFER_NOT_TO_SAY: "Prefiere no decir"
}

MARITAL_STATUS_DISPLAY_NAMES = {
    MaritalStatusEnum.SINGLE: "Soltero/a",
    MaritalStatusEnum.MARRIED: "Casado/a",
    MaritalStatusEnum.DIVORCED: "Divorciado/a",
    MaritalStatusEnum.WIDOWED: "Viudo/a",
    MaritalStatusEnum.SEPARATED: "Separado/a",
    MaritalStatusEnum.DOMESTIC_PARTNERSHIP: "Unión libre",
    MaritalStatusEnum.OTHER: "Otro"
}

DOCUMENT_TYPE_DISPLAY_NAMES = {
    DocumentTypeEnum.RFC: "RFC (Registro Federal de Contribuyentes)",
    DocumentTypeEnum.CURP: "CURP (Clave Única de Registro de Población)",
    DocumentTypeEnum.PASSPORT: "Pasaporte",
    DocumentTypeEnum.DRIVER_LICENSE: "Licencia de Conducir",
    DocumentTypeEnum.OTHER: "Otro Documento"
}

SKILL_CATEGORY_DISPLAY_NAMES = {
    SkillCategoryEnum.TECHNICAL: "Habilidades Técnicas",
    SkillCategoryEnum.LANGUAGE: "Idiomas",
    SkillCategoryEnum.SOFT_SKILL: "Habilidades Blandas",
    SkillCategoryEnum.TOOL: "Herramientas",
    SkillCategoryEnum.FRAMEWORK: "Frameworks",
    SkillCategoryEnum.PLATFORM: "Plataformas",
    SkillCategoryEnum.METHODOLOGY: "Metodologías",
    SkillCategoryEnum.CERTIFICATION: "Certificaciones",
    SkillCategoryEnum.DOMAIN: "Conocimiento de Dominio",
    SkillCategoryEnum.OTHER: "Otras"
}

SKILL_LEVEL_DISPLAY_NAMES = {
    SkillLevelEnum.BEGINNER: "Principiante (0-1 años)",
    SkillLevelEnum.INTERMEDIATE: "Intermedio (1-3 años)",
    SkillLevelEnum.ADVANCED: "Avanzado (3-5 años)",
    SkillLevelEnum.EXPERT: "Experto (5+ años)",
    SkillLevelEnum.MASTER: "Maestro (Instructor/Mentor)"
}

def get_display_name(enum_value, display_dict: dict) -> str:
    """
    Obtiene el nombre de display para un valor de enum.

    Args:
        enum_value: Valor del enum
        display_dict: Diccionario de mapeo a nombres de display

    Returns:
        Nombre de display o el valor original si no se encuentra

    Ejemplo:
        display = get_display_name(GenderEnum.MALE, GENDER_DISPLAY_NAMES)
        # Resultado: "Masculino"
    """
    return display_dict.get(enum_value, str(enum_value))