"""
Schemas Pydantic: State
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class StateBase(BaseModel):
    """Schema base para State."""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del estado/provincia/departamento")
    code: str = Field(..., min_length=1, max_length=10, description="Codigo del estado")
    country_id: int = Field(..., description="ID del pais al que pertenece")


class StateResponse(StateBase):
    """Schema de respuesta para State."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StateWithCountry(StateResponse):
    """Schema de respuesta incluyendo informacion del pais."""
    country_name: str = Field(..., description="Nombre del pais")
    country_iso_code: str = Field(..., description="Codigo ISO del pais")

    model_config = ConfigDict(from_attributes=True)