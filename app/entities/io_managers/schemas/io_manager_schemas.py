"""
Schemas Pydantic v2 para la entidad IOManager (Contralor).
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class IOManagerCreate(BaseModel):
    """Schema para registrar un nuevo contralor."""
    individual_id: int = Field(..., gt=0, description="ID del individual que será contralor")


class IOManagerResponse(BaseModel):
    """Schema de respuesta con datos del contralor y del individual asociado."""
    id: int
    individual_id: int
    is_active: bool
    created_at: datetime
    created_by: Optional[int] = None

    # Datos resueltos del individual (para la UI)
    individual_name: Optional[str] = None
    individual_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
