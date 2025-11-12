"""
Modelo Individual - Ejemplo completo de todos los tipos de datos en SQLAlchemy

Este modelo demuestra el uso de TODOS los tipos de datos disponibles en PostgreSQL
y SQLAlchemy, sirviendo como referencia educativa para futuras entidades.

TIPOS DE DATOS DEMOSTRADOS:
- Strings: nombre, apellido, email, teléfonos
- Integers: edad, código postal
- Decimals: altura, peso, salario
- Dates: fecha_nacimiento, fecha_registro
- Booleans: activo, verificado, acepta_marketing
- Enums: tipo_documento, género, estado_civil
- JSON/JSONB: datos_adicionales, preferencias
- Arrays: teléfonos, direcciones
- Relaciones FK: user_id, department_id
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey,
    Date, Enum as SQLEnum, JSON
)
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, date
from decimal import Decimal as PythonDecimal

# Importar base de datos y enums
from database import Base
from app.entities.individuals.schemas.enums import (
    DocumentTypeEnum, GenderEnum, MaritalStatusEnum,
    IndividualStatusEnum, ContactPreferenceEnum, EducationLevelEnum,
    EmploymentStatusEnum
)


class Individual(Base):
    """
    Modelo Individual - Demostración completa de tipos de datos.

    Esta entidad ejemplifica cómo manejar diferentes tipos de datos
    en una aplicación real, incluyendo validaciones, relaciones,
    y estructuras complejas como JSON y Arrays.

    Relaciones:
    - 1:1 opcional con User (para individuos que tienen cuenta)
    - N:1 con Department (departamento de trabajo)
    """
    __tablename__ = "individuals"

    # ==================== CAMPOS PRIMARIOS ====================

    id = Column(Integer, primary_key=True, index=True, comment="ID único del individuo")

    # Relación opcional con Usuario (para personas que tienen cuenta en el sistema)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="ID del usuario asociado (opcional)"
    )

    # ==================== STRINGS - Información Personal ====================

    # Nombres (requeridos, con validaciones de longitud)
    first_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Nombre(s) del individuo"
    )

    last_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Apellido(s) del individuo"
    )

    # Email único opcional (para contacto)
    email = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Email de contacto (único en el sistema)"
    )

    # Documento de identificación
    document_number = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Número de documento de identificación"
    )

    # Información de lugar de nacimiento/residencia
    birth_city = Column(
        String(100),
        nullable=True,
        comment="Ciudad de nacimiento"
    )

    birth_state = Column(
        String(100),
        nullable=True,
        comment="Estado/Provincia de nacimiento"
    )

    birth_country = Column(
        String(100),
        nullable=True,
        default="México",
        comment="País de nacimiento"
    )

    # Dirección actual
    address_street = Column(
        Text,
        nullable=True,
        comment="Calle y número de dirección"
    )

    address_city = Column(
        String(100),
        nullable=True,
        comment="Ciudad de residencia actual"
    )

    address_state = Column(
        String(100),
        nullable=True,
        comment="Estado de residencia actual"
    )

    # ==================== INTEGERS - Datos Numéricos Enteros ====================

    # Edad (calculada o almacenada)
    age = Column(
        Integer,
        nullable=True,
        comment="Edad en años (puede ser calculada desde birth_date)"
    )

    # Código postal
    postal_code = Column(
        Integer,
        nullable=True,
        comment="Código postal de residencia"
    )

    # Número de dependientes económicos
    dependents_count = Column(
        Integer,
        nullable=True,
        default=0,
        comment="Número de dependientes económicos"
    )

    # ==================== DECIMALS - Datos Numéricos Precisos ====================

    # Características físicas
    height = Column(
        DECIMAL(precision=5, scale=2),
        nullable=True,
        comment="Altura en metros (ej: 1.75)"
    )

    weight = Column(
        DECIMAL(precision=5, scale=2),
        nullable=True,
        comment="Peso en kilogramos (ej: 70.50)"
    )

    # Información financiera
    monthly_salary = Column(
        DECIMAL(precision=10, scale=2),
        nullable=True,
        comment="Salario mensual en moneda local"
    )

    credit_score = Column(
        DECIMAL(precision=5, scale=2),
        nullable=True,
        comment="Puntuación crediticia (0.00 - 999.99)"
    )

    # ==================== DATES - Fechas y Timestamps ====================

    # Fecha de nacimiento
    birth_date = Column(
        Date,
        nullable=True,
        comment="Fecha de nacimiento"
    )

    # Fecha de contratación (para empleados)
    hire_date = Column(
        Date,
        nullable=True,
        comment="Fecha de contratación"
    )

    # Timestamp de último contacto
    last_contact_date = Column(
        DateTime,
        nullable=True,
        comment="Última fecha de contacto con la persona"
    )

    # ==================== BOOLEANS - Campos de Estado (Ejemplo de Diferentes Tipos) ====================

    # Verificación de datos
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indica si los datos han sido verificados"
    )

    # Preferencias de marketing
    accepts_marketing = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Acepta recibir comunicaciones de marketing"
    )

    # Disponibilidad para trabajar (para candidatos)
    is_available_for_work = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Disponible para oportunidades laborales"
    )

    # Tiene carro (ejemplo de booleano de información adicional)
    has_vehicle = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Posee vehículo propio"
    )

    # ==================== ENUMS - Valores Categóricos ====================

    # Tipo de documento
    document_type = Column(
        SQLEnum(DocumentTypeEnum),
        nullable=True,
        comment="Tipo de documento de identificación"
    )

    # Género
    gender = Column(
        SQLEnum(GenderEnum),
        nullable=True,
        comment="Género del individuo"
    )

    # Estado civil
    marital_status = Column(
        SQLEnum(MaritalStatusEnum),
        nullable=True,
        comment="Estado civil actual"
    )

    # Estado en el sistema
    status = Column(
        SQLEnum(IndividualStatusEnum),
        default=IndividualStatusEnum.ACTIVE,
        nullable=False,
        comment="Estado del individuo en el sistema"
    )

    # Preferencia de contacto
    contact_preference = Column(
        SQLEnum(ContactPreferenceEnum),
        default=ContactPreferenceEnum.EMAIL,
        nullable=True,
        comment="Método preferido de contacto"
    )

    # Nivel educativo
    education_level = Column(
        SQLEnum(EducationLevelEnum),
        nullable=True,
        comment="Máximo nivel educativo alcanzado"
    )

    # Estado de empleo
    employment_status = Column(
        SQLEnum(EmploymentStatusEnum),
        nullable=True,
        comment="Estado actual de empleo"
    )

    # ==================== JSON/JSONB - Datos Estructurados ====================

    # Datos adicionales flexibles (JSON estándar)
    additional_data = Column(
        JSON,
        nullable=True,
        comment="Datos adicionales en formato JSON"
    )

    # Preferencias del usuario (JSONB para búsquedas optimizadas)
    preferences = Column(
        JSONB,
        nullable=True,
        comment="Preferencias del usuario en formato JSONB"
    )

    # Información de emergencia en JSON
    emergency_contact = Column(
        JSONB,
        nullable=True,
        comment="Información de contacto de emergencia"
    )

    # ==================== ARRAYS - Listas de Valores ====================

    # Lista de teléfonos
    phone_numbers = Column(
        ARRAY(String(20)),
        nullable=True,
        default=[],
        comment="Lista de números telefónicos"
    )

    # Lista de emails alternativos
    alternate_emails = Column(
        ARRAY(String(255)),
        nullable=True,
        default=[],
        comment="Emails alternativos"
    )

    # Lista de habilidades (para contexto laboral)
    skills = Column(
        ARRAY(String(50)),
        nullable=True,
        default=[],
        comment="Lista de habilidades o competencias"
    )

    # Lista de idiomas
    languages = Column(
        ARRAY(String(30)),
        nullable=True,
        default=[],
        comment="Idiomas que habla el individuo"
    )

    # Skills detalladas (JSONB para información estructurada)
    skill_details = Column(
        JSON,
        nullable=True,
        comment="Detalles estructurados de habilidades (categoría, nivel, años de experiencia)"
    )

    # ==================== RELACIONES GEOGRÁFICAS ====================

    # País de residencia
    country_id = Column(
        Integer,
        ForeignKey("countries.id"),
        nullable=True,
        index=True,
        comment="ID del país de residencia"
    )

    # Estado/Provincia/Departamento de residencia
    state_id = Column(
        Integer,
        ForeignKey("states.id"),
        nullable=True,
        index=True,
        comment="ID del estado/provincia/departamento de residencia"
    )

    # Relaciones
    country = relationship("Country", foreign_keys=[country_id])
    state = relationship("State", foreign_keys=[state_id])

    # ==================== CAMPOS DE AUDITORÍA ESTÁNDAR ====================
    # IMPORTANTE: Estos campos siguen el patrón de la plantilla original
    # y deben mantenerse consistentes con todas las entidades del sistema

    # Gestión de estado (como en User model)
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Para activar/desactivar el individuo"
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Para soft delete (no eliminar físicamente)"
    )

    # Timestamps automáticos (como en User model)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Fecha y hora de creación del registro"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Fecha y hora de última actualización"
    )

    # Timestamp de eliminación lógica
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="Fecha y hora de eliminación lógica (soft delete)"
    )

    # Usuario que realizó las acciones (como en User model)
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="Usuario que creó el registro"
    )

    updated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="Usuario que actualizó el registro por última vez"
    )

    deleted_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="Usuario que eliminó el registro (soft delete)"
    )

    # ==================== RELACIONES ====================

    # Relación con Usuario (opcional) - Unidireccional para evitar conflictos
    user = relationship(
        "User",
        foreign_keys=[user_id]
    )

    # Usuario que creó el registro
    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    # Usuario que actualizó el registro
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )

    # Usuario que eliminó el registro (soft delete)
    deleter = relationship(
        "User",
        foreign_keys=[deleted_by]
    )

    # ==================== PROPIEDADES CALCULADAS ====================

    @property
    def full_name(self) -> str:
        """Nombre completo del individuo."""
        return f"{self.first_name} {self.last_name}"

    @property
    def calculated_age(self) -> int:
        """Calcula la edad a partir de la fecha de nacimiento."""
        if not self.birth_date:
            return self.age or 0

        today = date.today()
        age = today.year - self.birth_date.year

        # Ajustar si el cumpleaños no ha pasado este año
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    @property
    def primary_phone(self) -> str:
        """Primer teléfono de la lista o None."""
        return self.phone_numbers[0] if self.phone_numbers else None

    @property
    def bmi(self) -> float:
        """Calcula el Índice de Masa Corporal si hay altura y peso."""
        if self.height and self.weight and self.height > 0:
            height_m = float(self.height)
            weight_kg = float(self.weight)
            return round(weight_kg / (height_m ** 2), 2)
        return None

    # ==================== MÉTODOS DE VALIDACIÓN ====================

    def validate_consistency(self) -> list:
        """
        Valida la consistencia de los datos.

        Returns:
            Lista de errores encontrados
        """
        errors = []

        # Validar edad vs fecha de nacimiento
        if self.age and self.birth_date:
            calculated_age = self.calculated_age
            if abs(self.age - calculated_age) > 1:
                errors.append("La edad no coincide con la fecha de nacimiento")

        # Validar que tenga al menos un método de contacto
        if not self.email and not self.phone_numbers:
            errors.append("Debe tener al menos un email o teléfono")

        # Validar documento requerido si está verificado
        if self.is_verified and not self.document_number:
            errors.append("Persona verificada debe tener número de documento")

        return errors

    # ==================== MÉTODOS DE UTILIDAD ====================

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convierte la entidad a diccionario.

        Args:
            include_sensitive: Si incluir datos sensibles

        Returns:
            Diccionario con los datos del individuo
        """
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "age": self.calculated_age,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

        if include_sensitive:
            data.update({
                "document_number": self.document_number,
                "monthly_salary": float(self.monthly_salary) if self.monthly_salary else None,
                "phone_numbers": self.phone_numbers,
                "additional_data": self.additional_data
            })

        return data

    # ==================== MÉTODOS DE SKILLS ====================

    def add_skill_detail(self, skill_name: str, category: str, level: str, years_experience: int = 0, notes: str = None):
        """Añadir skill detallada al individuo."""
        # Añadir al array simple si no existe
        if self.skills is None:
            self.skills = []
        if skill_name not in self.skills:
            self.skills.append(skill_name)
            flag_modified(self, 'skills')  # Forzar detección de cambio

        # Añadir a skill_details (JSONB)
        if self.skill_details is None:
            self.skill_details = []

        skill_detail = {
            "name": skill_name,
            "category": category,
            "level": level,
            "years_experience": years_experience
        }
        if notes:
            skill_detail["notes"] = notes

        self.skill_details.append(skill_detail)
        flag_modified(self, 'skill_details')  # Forzar detección de cambio

    def remove_skill(self, skill_name: str):
        """Eliminar skill del individuo."""
        # Remover del array simple
        if self.skills and skill_name in self.skills:
            self.skills.remove(skill_name)
            flag_modified(self, 'skills')  # Forzar detección de cambio

        # Remover de skill_details
        if self.skill_details:
            self.skill_details = [s for s in self.skill_details if s.get("name") != skill_name]
            flag_modified(self, 'skill_details')  # Forzar detección de cambio

    def update_skill_level(self, skill_name: str, level: str = None, years_experience: int = None, notes: str = None):
        """Actualizar nivel de una skill existente."""
        if not self.skill_details:
            return False

        for skill in self.skill_details:
            if skill.get("name") == skill_name:
                if level:
                    skill["level"] = level
                if years_experience is not None:
                    skill["years_experience"] = years_experience
                if notes:
                    skill["notes"] = notes
                flag_modified(self, 'skill_details')  # Forzar detección de cambio
                return True
        return False

    def get_skills_summary(self) -> dict:
        """Obtener resumen estadístico de skills."""
        if not self.skill_details:
            return {
                "total_skills": len(self.skills) if self.skills else 0,
                "detailed_skills": 0,
                "by_category": {},
                "by_level": {},
                "expert_skills": [],
                "total_years_experience": 0
            }

        by_category = {}
        by_level = {}
        expert_skills = []
        total_years = 0

        for skill in self.skill_details:
            # Por categoría
            cat = skill.get("category", "OTHER")
            by_category[cat] = by_category.get(cat, 0) + 1

            # Por nivel
            level = skill.get("level", "BEGINNER")
            by_level[level] = by_level.get(level, 0) + 1

            # Skills expertas
            if level in ["EXPERT", "MASTER"]:
                expert_skills.append(skill.get("name"))

            # Total años
            total_years += skill.get("years_experience", 0)

        return {
            "total_skills": len(self.skills) if self.skills else 0,
            "detailed_skills": len(self.skill_details),
            "by_category": by_category,
            "by_level": by_level,
            "expert_skills": expert_skills,
            "total_years_experience": total_years
        }

    def get_skills_by_category(self, category: str) -> list:
        """Obtener skills filtradas por categoría."""
        if not self.skill_details:
            return []
        return [s for s in self.skill_details if s.get("category") == category]

    def get_expert_skills(self) -> list:
        """Obtener solo skills de nivel EXPERT o MASTER."""
        if not self.skill_details:
            return []
        return [s for s in self.skill_details if s.get("level") in ["EXPERT", "MASTER"]]

    def get_skill_detail(self, skill_name: str) -> dict:
        """Obtener detalle de una skill específica por nombre."""
        if not self.skill_details:
            return None
        for skill in self.skill_details:
            if skill.get("name") == skill_name:
                return skill
        return None

    def __repr__(self):
        return f"<Individual(id={self.id}, name='{self.full_name}', email='{self.email}')>"

    def __str__(self):
        return self.full_name