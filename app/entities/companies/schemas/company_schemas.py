"""
Schemas Pydantic para la entidad Company

Define los modelos de validación para requests y responses de la API.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class CompanyStatus(str, Enum):
    """Estados posibles de una empresa"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    WAITING = "waiting"


class TaxSystem(str, Enum):
    """Tipos de sistemas fiscales"""
    RFC = "RFC"  # México
    EIN = "EIN"  # USA
    NIF = "NIF"  # España
    VAT = "VAT"  # Reino Unido
    CUIL = "CUIL"  # Colombia
    CUIT = "CUIT"  # Argentina
    RUC = "RUC"  # Perú, Ecuador
    RUT = "RUT"  # Chile
    CNPJ = "CNPJ"  # Brasil
    OTHER = "OTHER"  # Otros


# ==================== SCHEMAS BASE ====================

class CompanyBase(BaseModel):
    """Schema base con campos comunes"""
    company_name: str = Field(..., min_length=2, max_length=200,
                              description="Nombre comercial o razón social")
    legal_name: Optional[str] = Field(None, max_length=200,
                                      description="Nombre legal completo")
    tin: str = Field(..., min_length=5, max_length=30,
                    description="Tax Identification Number (RFC, EIN, NIF, etc.)")
    tax_system: TaxSystem = Field(..., description="Tipo de sistema fiscal")

    country_id: int = Field(..., gt=0, description="ID del país")
    state_id: Optional[int] = Field(None, gt=0, description="ID del estado/provincia")
    city: Optional[str] = Field(None, max_length=100, description="Ciudad")
    address: Optional[str] = Field(None, max_length=255, description="Domicilio fiscal")
    postal_code: Optional[str] = Field(None, max_length=10, description="Código postal")

    phone: Optional[str] = Field(None, max_length=20, description="Teléfono principal")
    email: Optional[EmailStr] = Field(None, description="Correo de contacto")
    website: Optional[str] = Field(None, max_length=150, description="Sitio web")

    status: CompanyStatus = Field(default=CompanyStatus.ACTIVE,
                                  description="Estado de la empresa")

    @field_validator('tin')
    @classmethod
    def validate_tin(cls, v: str) -> str:
        """Valida que TIN no tenga espacios y esté en mayúsculas"""
        return v.strip().upper()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Limpia y valida el teléfono"""
        if v:
            # Remover espacios y caracteres especiales excepto +, -, (), números
            cleaned = ''.join(c for c in v if c.isdigit() or c in ['+', '-', '(', ')', ' '])
            return cleaned.strip()
        return v

    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el website tenga formato correcto"""
        if v:
            v = v.strip().lower()
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
        return v


# ==================== SCHEMAS DE OPERACIONES ====================

class CompanyCreate(CompanyBase):
    """Schema para crear una empresa"""
    pass


class CompanyUpdate(BaseModel):
    """Schema para actualizar una empresa (todos los campos opcionales)"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=200)
    tin: Optional[str] = Field(None, min_length=5, max_length=30)
    tax_system: Optional[TaxSystem] = None

    country_id: Optional[int] = Field(None, gt=0)
    state_id: Optional[int] = Field(None, gt=0)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=10)

    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=150)

    status: Optional[CompanyStatus] = None

    @field_validator('tin')
    @classmethod
    def validate_tin(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip().upper()
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            cleaned = ''.join(c for c in v if c.isdigit() or c in ['+', '-', '(', ')', ' '])
            return cleaned.strip()
        return v

    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().lower()
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
        return v


# ==================== SCHEMAS DE RESPUESTA ====================

class CompanyResponse(CompanyBase):
    """Schema de respuesta con campos adicionales"""
    id: int
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by: Optional[int]
    updated_at: Optional[datetime]
    updated_by: Optional[int]
    deleted_at: Optional[datetime]
    deleted_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    """Schema para respuesta de listado con paginación"""
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Registros por página")
    total_pages: int = Field(..., description="Total de páginas")
    data: list[CompanyResponse] = Field(..., description="Lista de empresas")

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS ANIDADOS (CON RELACIONES) ====================

class CompanyWithRelations(CompanyResponse):
    """Schema de empresa con relaciones cargadas"""
    country_name: Optional[str] = None
    state_name: Optional[str] = None
    creator_name: Optional[str] = None
    updater_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE BÚSQUEDA ====================

class CompanySearch(BaseModel):
    """Schema para búsqueda de empresas"""
    search_term: Optional[str] = Field(None, min_length=2,
                                       description="Término de búsqueda")
    country_id: Optional[int] = Field(None, gt=0)
    state_id: Optional[int] = Field(None, gt=0)
    status: Optional[CompanyStatus] = None
    tax_system: Optional[TaxSystem] = None


# ==================== SCHEMAS DE ESTADÍSTICAS ====================

class CompanyStatistics(BaseModel):
    """Schema para estadísticas de empresas"""
    total_companies: int
    active_companies: int
    inactive_companies: int
    suspended_companies: int
    companies_by_country: dict[str, int]
    companies_by_tax_system: dict[str, int]

    model_config = ConfigDict(from_attributes=True)
