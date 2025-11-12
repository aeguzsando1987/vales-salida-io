"""
Schemas Pydantic para Individual

Mantiene compatibilidad total con schemas existentes mientras
añade funcionalidades extendidas del nuevo modelo.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, validator, Field

from app.entities.individuals.schemas.enums import (
    DocumentTypeEnum,
    GenderEnum,
    MaritalStatusEnum,
    IndividualStatusEnum,
    ContactPreferenceEnum,
    EducationLevelEnum,
    EmploymentStatusEnum
)
from app.shared.validators import (
    validate_email,
    validate_phone,
    validate_non_empty_string,
    validate_phone_list,
    validate_age,
    validate_birth_date,
    validate_document_number,
    validate_decimal_range
)


# ==================== SCHEMAS DE COMPATIBILIDAD ====================
# Estos mantienen exactamente la misma estructura que modules/individuals/schemas.py

class IndividualCreate(BaseModel):
    """
    Schema para crear individuo - COMPATIBILIDAD TOTAL con módulo existente.

    Mantiene exactamente los mismos campos y validaciones
    que IndividualCreate original.
    """
    user_id: Optional[int] = None  # FK opcional
    name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"
    country_id: Optional[int] = Field(None, description="ID del pais de residencia")
    state_id: Optional[int] = Field(None, description="ID del estado/provincia de residencia")

    @validator('name')
    def validate_name(cls, v):
        return validate_non_empty_string(v, "Nombre")

    @validator('last_name')
    def validate_last_name(cls, v):
        return validate_non_empty_string(v, "Apellido")

    @validator('email')
    def validate_email_field(cls, v):
        return validate_email(v)

    @validator('phone')
    def validate_phone_field(cls, v):
        if v:
            return validate_phone(v)
        return v


class IndividualUpdate(BaseModel):
    """
    Schema para actualizar individuo - COMPATIBILIDAD TOTAL.
    """
    user_id: Optional[int] = None
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    country_id: Optional[int] = Field(None, description="ID del pais de residencia")
    state_id: Optional[int] = Field(None, description="ID del estado/provincia de residencia")

    @validator('name')
    def validate_name(cls, v):
        if v:
            return validate_non_empty_string(v, "Nombre")
        return v

    @validator('last_name')
    def validate_last_name(cls, v):
        if v:
            return validate_non_empty_string(v, "Apellido")
        return v

    @validator('email')
    def validate_email_field(cls, v):
        if v:
            return validate_email(v)
        return v

    @validator('phone')
    def validate_phone_field(cls, v):
        if v:
            return validate_phone(v)
        return v


class IndividualWithUserCreate(BaseModel):
    """
    Schema para crear individuo con usuario - COMPATIBILIDAD TOTAL.
    """
    # Datos del usuario
    user_email: str
    user_name: str
    user_password: str
    user_role: int = 4  # Default: Lector
    # Datos de la persona
    name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"

    @validator('user_email', 'email')
    def validate_emails(cls, v):
        return validate_email(v)

    @validator('user_name', 'name', 'last_name')
    def validate_names(cls, v):
        return validate_non_empty_string(v, "Nombre")

    @validator('user_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Contraseña debe tener al menos 6 caracteres')
        return v

    @validator('phone')
    def validate_phone_field(cls, v):
        if v:
            return validate_phone(v)
        return v


class IndividualResponse(BaseModel):
    """
    Schema de respuesta - COMPATIBILIDAD TOTAL.
    """
    id: int
    user_id: Optional[int]
    name: str
    last_name: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== SCHEMAS EXTENDIDOS ====================
# Estos aprovechan todas las funcionalidades del nuevo modelo

class PhysicalInfoSchema(BaseModel):
    """Schema para información física."""
    height: Optional[Decimal] = Field(None, description="Altura en metros")
    weight: Optional[Decimal] = Field(None, description="Peso en kilogramos")

    @validator('height')
    def validate_height(cls, v):
        if v:
            return validate_decimal_range(v, Decimal('0.5'), Decimal('2.5'), "Altura")
        return v

    @validator('weight')
    def validate_weight(cls, v):
        if v:
            return validate_decimal_range(v, Decimal('1'), Decimal('500'), "Peso")
        return v


class AddressSchema(BaseModel):
    """Schema para información de dirección."""
    street: Optional[str] = Field(None, description="Calle y número")
    city: Optional[str] = Field(None, description="Ciudad")
    state: Optional[str] = Field(None, description="Estado/Provincia")
    postal_code: Optional[int] = Field(None, description="Código postal")


class BirthInfoSchema(BaseModel):
    """Schema para información de nacimiento."""
    birth_date: Optional[date] = Field(None, description="Fecha de nacimiento")
    birth_city: Optional[str] = Field(None, description="Ciudad de nacimiento")
    birth_state: Optional[str] = Field(None, description="Estado de nacimiento")
    birth_country: Optional[str] = Field(None, description="País de nacimiento")

    @validator('birth_date')
    def validate_birth_date_field(cls, v):
        if v:
            return validate_birth_date(v)
        return v


class FinancialInfoSchema(BaseModel):
    """Schema para información financiera."""
    monthly_salary: Optional[Decimal] = Field(None, description="Salario mensual")
    credit_score: Optional[Decimal] = Field(None, description="Puntuación crediticia")

    @validator('monthly_salary')
    def validate_salary(cls, v):
        if v:
            return validate_decimal_range(v, Decimal('0'), Decimal('1000000'), "Salario")
        return v

    @validator('credit_score')
    def validate_credit_score(cls, v):
        if v:
            return validate_decimal_range(v, Decimal('0'), Decimal('999.99'), "Credit Score")
        return v


class EmergencyContactSchema(BaseModel):
    """Schema para contacto de emergencia."""
    name: str = Field(..., description="Nombre del contacto de emergencia")
    relationship: str = Field(..., description="Relación (madre, padre, etc.)")
    phone: str = Field(..., description="Teléfono del contacto")
    email: Optional[str] = Field(None, description="Email del contacto")

    @validator('name')
    def validate_contact_name(cls, v):
        return validate_non_empty_string(v, "Nombre del contacto")

    @validator('phone')
    def validate_contact_phone(cls, v):
        return validate_phone(v)

    @validator('email')
    def validate_contact_email(cls, v):
        if v:
            return validate_email(v)
        return v


class IndividualCreateExtended(BaseModel):
    """
    Schema extendido para crear individuo con todas las funcionalidades.

    Incluye todos los campos del nuevo modelo Individual.
    """
    # Campos básicos requeridos
    first_name: str = Field(..., description="Nombre(s)")
    last_name: str = Field(..., description="Apellido(s)")
    email: str = Field(..., description="Email principal")

    # Campos opcionales básicos
    user_id: Optional[int] = Field(None, description="ID del usuario asociado")

    # Información de documento
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Tipo de documento")
    document_number: Optional[str] = Field(None, description="Número de documento")

    # Contacto
    phone_numbers: Optional[List[str]] = Field(default=[], description="Lista de teléfonos")
    alternate_emails: Optional[List[str]] = Field(default=[], description="Emails alternativos")

    # Información personal
    gender: Optional[GenderEnum] = Field(None, description="Género")
    marital_status: Optional[MaritalStatusEnum] = Field(None, description="Estado civil")
    age: Optional[int] = Field(None, description="Edad")
    birth_info: Optional[BirthInfoSchema] = Field(None, description="Información de nacimiento")

    # Dirección
    address: Optional[AddressSchema] = Field(None, description="Dirección completa")

    # Información física
    physical_info: Optional[PhysicalInfoSchema] = Field(None, description="Información física")

    # Información laboral y educativa
    education_level: Optional[EducationLevelEnum] = Field(None, description="Nivel educativo")
    employment_status: Optional[EmploymentStatusEnum] = Field(None, description="Estado de empleo")
    skills: Optional[List[str]] = Field(default=[], description="Habilidades")
    languages: Optional[List[str]] = Field(default=[], description="Idiomas")

    # Información financiera
    financial_info: Optional[FinancialInfoSchema] = Field(None, description="Información financiera")
    dependents_count: Optional[int] = Field(None, description="Número de dependientes")

    # Preferencias y configuración
    contact_preference: Optional[ContactPreferenceEnum] = Field(None, description="Preferencia de contacto")
    accepts_marketing: Optional[bool] = Field(False, description="Acepta marketing")
    has_vehicle: Optional[bool] = Field(False, description="Tiene vehículo")

    # Status
    status: Optional[IndividualStatusEnum] = Field(IndividualStatusEnum.ACTIVE, description="Estado en el sistema")
    is_available_for_work: Optional[bool] = Field(True, description="Disponible para trabajo")

    # Datos estructurados
    emergency_contact: Optional[EmergencyContactSchema] = Field(None, description="Contacto de emergencia")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Preferencias")

    # Validadores
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        return validate_non_empty_string(v, "Nombre")

    @validator('email')
    def validate_email_field(cls, v):
        return validate_email(v)

    @validator('phone_numbers')
    def validate_phone_numbers(cls, v):
        if v:
            return validate_phone_list(v)
        return v

    @validator('alternate_emails')
    def validate_alternate_emails(cls, v):
        if v:
            for email in v:
                validate_email(email)
        return v

    @validator('age')
    def validate_age_field(cls, v):
        if v:
            return validate_age(v)
        return v

    @validator('document_number')
    def validate_document(cls, v, values):
        if v and values.get('document_type'):
            return validate_document_number(v, values['document_type'].value)
        return v

    @validator('dependents_count')
    def validate_dependents(cls, v):
        if v is not None and v < 0:
            raise ValueError('Número de dependientes no puede ser negativo')
        return v

    @validator('skills', 'languages')
    def validate_arrays(cls, v):
        if v and len(v) > 20:
            raise ValueError('Máximo 20 elementos permitidos')
        return v


class IndividualUpdateExtended(BaseModel):
    """
    Schema extendido para actualizar individuo.

    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    # Campos básicos
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[int] = None

    # Información de documento
    document_type: Optional[DocumentTypeEnum] = None
    document_number: Optional[str] = None

    # Contacto
    phone_numbers: Optional[List[str]] = None
    alternate_emails: Optional[List[str]] = None

    # Información personal
    gender: Optional[GenderEnum] = None
    marital_status: Optional[MaritalStatusEnum] = None
    age: Optional[int] = None
    birth_info: Optional[BirthInfoSchema] = None

    # Dirección
    address: Optional[AddressSchema] = None

    # Información física
    physical_info: Optional[PhysicalInfoSchema] = None

    # Información laboral y educativa
    education_level: Optional[EducationLevelEnum] = None
    employment_status: Optional[EmploymentStatusEnum] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None

    # Información financiera
    financial_info: Optional[FinancialInfoSchema] = None
    dependents_count: Optional[int] = None

    # Preferencias y configuración
    contact_preference: Optional[ContactPreferenceEnum] = None
    accepts_marketing: Optional[bool] = None
    has_vehicle: Optional[bool] = None
    is_available_for_work: Optional[bool] = None

    # Status
    status: Optional[IndividualStatusEnum] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

    # Datos estructurados
    emergency_contact: Optional[EmergencyContactSchema] = None
    additional_data: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None

    # Mismos validadores que el schema de creación
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v:
            return validate_non_empty_string(v, "Nombre")
        return v

    @validator('email')
    def validate_email_field(cls, v):
        if v:
            return validate_email(v)
        return v

    @validator('phone_numbers')
    def validate_phone_numbers(cls, v):
        if v:
            return validate_phone_list(v)
        return v

    @validator('alternate_emails')
    def validate_alternate_emails(cls, v):
        if v:
            for email in v:
                validate_email(email)
        return v

    @validator('age')
    def validate_age_field(cls, v):
        if v:
            return validate_age(v)
        return v

    @validator('document_number')
    def validate_document(cls, v, values):
        if v and values.get('document_type'):
            return validate_document_number(v, values['document_type'].value)
        return v


class IndividualResponseExtended(BaseModel):
    """
    Schema de respuesta extendido con todas las propiedades.

    Incluye campos calculados y toda la información del modelo.
    """
    # Información básica
    id: int
    user_id: Optional[int]
    first_name: str
    last_name: str
    full_name: str  # Propiedad calculada
    email: str

    # Información de documento
    document_type: Optional[str]
    document_number: Optional[str]

    # Contacto
    phone_numbers: Optional[List[str]]
    primary_phone: Optional[str]  # Propiedad calculada
    alternate_emails: Optional[List[str]]

    # Información personal
    gender: Optional[str]
    marital_status: Optional[str]
    age: Optional[int]
    calculated_age: Optional[int]  # Propiedad calculada

    # Información de nacimiento
    birth_date: Optional[date]
    birth_city: Optional[str]
    birth_state: Optional[str]
    birth_country: Optional[str]

    # Dirección
    address_street: Optional[str]
    address_city: Optional[str]
    address_state: Optional[str]
    postal_code: Optional[int]

    # Información física
    height: Optional[Decimal]
    weight: Optional[Decimal]
    bmi: Optional[float]  # Propiedad calculada

    # Información laboral y educativa
    education_level: Optional[str]
    employment_status: Optional[str]
    skills: Optional[List[str]]
    languages: Optional[List[str]]

    # Información financiera
    monthly_salary: Optional[Decimal]
    credit_score: Optional[Decimal]
    dependents_count: Optional[int]

    # Preferencias
    contact_preference: Optional[str]
    accepts_marketing: bool
    has_vehicle: bool
    is_available_for_work: bool

    # Status
    status: Optional[str]
    is_active: bool
    is_verified: bool
    is_deleted: bool

    # Datos estructurados
    additional_data: Optional[Dict[str, Any]]
    preferences: Optional[Dict[str, Any]]
    emergency_contact: Optional[Dict[str, Any]]

    # Auditoría
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    created_by: Optional[int]
    updated_by: Optional[int]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True


# ==================== SCHEMAS DE UTILIDAD ====================

class IndividualSearchFilters(BaseModel):
    """Schema para filtros de búsqueda avanzada."""
    # Filtros básicos (compatibilidad)
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    search: Optional[str] = None

    # Filtros extendidos
    document_type: Optional[DocumentTypeEnum] = None
    document_number: Optional[str] = None
    gender: Optional[GenderEnum] = None
    marital_status: Optional[MaritalStatusEnum] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    education_level: Optional[EducationLevelEnum] = None
    employment_status: Optional[EmploymentStatusEnum] = None
    skill: Optional[str] = None
    language: Optional[str] = None
    is_verified: Optional[bool] = None
    has_vehicle: Optional[bool] = None
    is_available_for_work: Optional[bool] = None

    # Paginación
    page: int = Field(1, ge=1)
    limit: int = Field(100, ge=1, le=1000)

    # Ordenamiento
    order_by: str = "id"
    order_desc: bool = False


class IndividualStatistics(BaseModel):
    """Schema para estadísticas de individuos."""
    total_individuals: int
    active_individuals: int
    verified_individuals: int
    individuals_with_user: int
    inactive_individuals: int

    # Estadísticas por género
    by_gender: Optional[Dict[str, int]] = None

    # Estadísticas por status
    by_status: Optional[Dict[str, int]] = None

    # Estadísticas por estado civil
    by_marital_status: Optional[Dict[str, int]] = None

    # Estadísticas por nivel educativo
    by_education_level: Optional[Dict[str, int]] = None


class ValidationResult(BaseModel):
    """Schema para resultado de validación de consistencia."""
    individual_id: int
    is_consistent: bool
    validation_errors: List[str]


class IndividualAgeCalculation(BaseModel):
    """Schema para cálculo de edad."""
    individual_id: int
    birth_date: Optional[date]
    calculated_age: Optional[int]
    stored_age: Optional[int]
    age_consistent: bool


class IndividualBMICalculation(BaseModel):
    """Schema para cálculo de BMI."""
    individual_id: int
    height: Optional[Decimal]
    weight: Optional[Decimal]
    bmi: Optional[float]
    bmi_category: Optional[str]  # Bajo peso, Normal, Sobrepeso, Obesidad