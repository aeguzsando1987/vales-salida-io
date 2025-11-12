"""
Schemas Pydantic: Country
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CountryBase(BaseModel):
    """Schema base para Country."""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del pais")
    iso_code_2: str = Field(..., min_length=2, max_length=2, description="Codigo ISO 3166-1 alpha-2")
    iso_code_3: str = Field(..., min_length=3, max_length=3, description="Codigo ISO 3166-1 alpha-3")
    numeric_code: Optional[str] = Field(None, max_length=3, description="Codigo numerico ISO")
    phone_code: Optional[str] = Field(None, max_length=10, description="Codigo telefonico (+1, +52, +57)")
    currency_code: Optional[str] = Field(None, max_length=3, description="Codigo de moneda ISO 4217")
    currency_name: Optional[str] = Field(None, max_length=50, description="Nombre de la moneda")


class CountryResponse(CountryBase):
    """Schema de respuesta para Country."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CountryWithStates(CountryResponse):
    """Schema de respuesta incluyendo estados."""
    states_count: int = Field(..., description="Cantidad de estados/provincias")

    model_config = ConfigDict(from_attributes=True)