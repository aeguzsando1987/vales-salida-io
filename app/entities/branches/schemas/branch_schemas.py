"""
Schemas Pydantic para la entidad Branch.

Define los modelos de validación para crear, actualizar y responder
información de sucursales/ubicaciones.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class BranchType(str, Enum):
    """Tipos de sucursal/ubicación"""
    WAREHOUSE = "warehouse"      # Almacén
    PROJECT = "project"          # Proyecto/Obra
    PLANT = "plant"             # Planta industrial
    OFFICE = "office"           # Oficina
    SITE = "site"               # Sitio/Lugar temporal

class OperationalStatus(str, Enum):
    """Estados operativos de la sucursal"""
    ACTIVE = "active"           # Activa y operando
    INACTIVE = "inactive"       # Inactiva temporalmente
    MAINTENANCE = "maintenance" # En mantenimiento
    CLOSED = "closed"           # Cerrada permanentemente

# ==================== SCHEMAS BASE ====================

class BranchBase(BaseModel):
    """
    Schema base con campos comunes para Branch.

    Usado como base para Create y Update.
    """
    branch_code: str = Field(..., min_length=2, max_length=50,
                            description="Código único de la sucursal")
    branch_name: str = Field(..., min_length=3, max_length=200,
                            description="Nombre de la sucursal")
    branch_type: BranchType = Field(...,
                                   description="Tipo de sucursal")
    description: Optional[str] = Field(None, max_length=1000,
                                      description="Descripción detallada")

    company_id: int = Field(..., gt=0,
                           description="ID de la empresa a la que pertenece")

    country_id: int = Field(..., gt=0,
                           description="ID del país")
    state_id: Optional[int] = Field(None, gt=0,
                                   description="ID del estado/provincia")
    city: Optional[str] = Field(None, max_length=100,
                               description="Ciudad")
    address: Optional[str] = Field(None, max_length=255,
                                  description="Dirección física")
    postal_code: Optional[str] = Field(None, max_length=10,
                                      description="Código postal")

    phone: Optional[str] = Field(None, max_length=20,
                                description="Teléfono de contacto")
    email: Optional[str] = Field(None, max_length=150,
                                description="Correo de contacto")

    manager_id: Optional[int] = Field(None, gt=0,
                                     description="ID del responsable/gerente")

    latitude: Optional[str] = Field(None, max_length=20,
                                   description="Latitud GPS")
    longitude: Optional[str] = Field(None, max_length=20,
                                    description="Longitud GPS")

    operational_status: OperationalStatus = Field(default=OperationalStatus.ACTIVE,
                                                 description="Estado operativo")

    @field_validator('branch_code')
    @classmethod
    def validate_branch_code(cls, v: str) -> str:
        """Normaliza el código a mayúsculas y sin espacios extremos"""
        return v.strip().upper()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Limpia el teléfono dejando solo números y caracteres válidos"""
        if v:
            cleaned = ''.join(c for c in v if c.isdigit() or c in ['+', '-', '(', ')', ' '])
            return cleaned.strip()
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza email a minúsculas"""
        if v:
            return v.strip().lower()
        return v

# ==================== SCHEMAS DE OPERACIONES ====================

class BranchCreate(BranchBase):
    """
    Schema para crear una nueva sucursal.

    Hereda todos los campos de BranchBase.
    """
    pass

class BranchUpdate(BaseModel):
    """
    Schema para actualizar una sucursal existente.

    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    branch_code: Optional[str] = Field(None, min_length=2, max_length=50)
    branch_name: Optional[str] = Field(None, min_length=3, max_length=200)
    branch_type: Optional[BranchType] = None
    description: Optional[str] = Field(None, max_length=1000)

    company_id: Optional[int] = Field(None, gt=0)

    country_id: Optional[int] = Field(None, gt=0)
    state_id: Optional[int] = Field(None, gt=0)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=10)

    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=150)

    manager_id: Optional[int] = Field(None, gt=0)

    latitude: Optional[str] = Field(None, max_length=20)
    longitude: Optional[str] = Field(None, max_length=20)

    operational_status: Optional[OperationalStatus] = None

    @field_validator('branch_code')
    @classmethod
    def validate_branch_code(cls, v: Optional[str]) -> Optional[str]:
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

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip().lower()
        return v

# ==================== SCHEMAS DE RESPUESTA ====================

class BranchResponse(BranchBase):
    """
    Schema de respuesta para una sucursal.

    Incluye todos los campos del modelo más los de auditoría.
    """
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

class BranchWithRelations(BranchResponse):
    """
    Schema de respuesta con nombres de relaciones cargadas.

    Útil para mostrar información completa en detalles.
    """
    company_name: Optional[str] = None
    country_name: Optional[str] = None
    state_name: Optional[str] = None
    manager_name: Optional[str] = None
    creator_name: Optional[str] = None
    updater_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BranchListResponse(BaseModel):
    """
    Schema de respuesta para listados paginados de sucursales.
    """
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Registros por página")
    total_pages: int = Field(..., description="Total de páginas")
    data: list[BranchResponse] = Field(..., description="Lista de sucursales")

    model_config = ConfigDict(from_attributes=True)

# ==================== SCHEMAS AUXILIARES ====================

class BranchSearch(BaseModel):
    """
    Schema para búsqueda avanzada de sucursales.
    """
    search_term: Optional[str] = Field(None, max_length=200,
                                      description="Término de búsqueda (código, nombre)")
    branch_type: Optional[BranchType] = Field(None,
                                             description="Filtrar por tipo")
    company_id: Optional[int] = Field(None, gt=0,
                                     description="Filtrar por empresa")
    country_id: Optional[int] = Field(None, gt=0,
                                     description="Filtrar por país")
    state_id: Optional[int] = Field(None, gt=0,
                                   description="Filtrar por estado")
    operational_status: Optional[OperationalStatus] = Field(None,
                                                           description="Filtrar por estado operativo")
    active_only: bool = Field(default=True,
                             description="Solo registros activos")

class BranchStatusUpdate(BaseModel):
    """
    Schema para actualizar solo el estado operativo.
    """
    operational_status: OperationalStatus = Field(...,
                                                 description="Nuevo estado operativo")
