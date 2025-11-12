"""
Schemas para User Permissions (Phase 3)

Permisos a nivel de usuario que sobrescriben los permisos del rol.
Soporta permisos temporales con fecha de expiración.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserPermissionBase(BaseModel):
    """Schema base para user permissions."""
    permission_id: int = Field(..., gt=0, description="ID del permiso a asignar")
    permission_level: int = Field(..., ge=0, le=4, description="Nivel de permiso (0-4)")
    valid_from: Optional[datetime] = Field(None, description="Fecha de inicio de validez")
    valid_until: Optional[datetime] = Field(None, description="Fecha de expiración (NULL = permanente)")
    reason: Optional[str] = Field(None, max_length=500, description="Razón del override")


class UserPermissionCreate(UserPermissionBase):
    """Schema para crear un user permission."""
    pass


class UserPermissionUpdate(BaseModel):
    """Schema para actualizar un user permission."""
    permission_level: Optional[int] = Field(None, ge=0, le=4)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class UserPermissionResponse(UserPermissionBase):
    """Schema de respuesta para user permission."""
    id: int
    user_id: int
    granted_by: Optional[int] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPermissionWithDetails(UserPermissionResponse):
    """Schema de respuesta con detalles de permiso y usuario."""
    # Detalles del permiso
    permission_entity: str
    permission_action: str
    permission_endpoint: str
    permission_http_method: str

    # Detalles del usuario que otorgó
    granted_by_name: Optional[str] = None
    granted_by_email: Optional[str] = None

    # Estado
    is_expired: bool
    is_valid: bool


class UserPermissionGrant(BaseModel):
    """Schema para otorgar permiso a usuario."""
    entity: str = Field(..., min_length=1, max_length=100, description="Entidad (ej: 'companies')")
    action: str = Field(..., min_length=1, max_length=50, description="Acción (ej: 'delete')")
    level: int = Field(..., ge=0, le=4, description="Nivel de permiso (0-4)")
    hours: Optional[int] = Field(default=None, description="Duración en horas (NULL = permanente)")
    reason: Optional[str] = Field(default=None, max_length=500, description="Razón del override")


class UserPermissionRevoke(BaseModel):
    """Schema para revocar permiso."""
    reason: Optional[str] = Field(None, max_length=500, description="Razón de la revocación")


class EffectivePermissionsResponse(BaseModel):
    """Schema para mostrar permisos efectivos de un usuario."""
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    permissions: list[dict]  # Lista de permisos con nivel efectivo y fuente


class PermissionLevelInfo(BaseModel):
    """Información sobre un nivel de permiso."""
    level: int
    name: str
    description: str
    includes: str


class UserPermissionListResponse(BaseModel):
    """Schema para lista paginada de user permissions."""
    total: int
    items: list[UserPermissionWithDetails]
