"""
Validadores reutilizables para diferentes tipos de datos

Este módulo contiene validadores Pydantic personalizados que pueden
ser reutilizados en múltiples schemas y entidades de la aplicación.
"""

import re
from typing import Any, List, Dict, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from pydantic import validator


# ==================== VALIDADORES DE STRINGS ====================

def validate_email(email: str) -> str:
    """
    Valida formato de email.

    Args:
        email: Email a validar

    Returns:
        Email validado en minúsculas

    Raises:
        ValueError: Si el formato es inválido

    Ejemplo en schema:
        @validator('email')
        def validate_email_field(cls, v):
            return validate_email(v)
    """
    if not email:
        raise ValueError('Email es requerido')

    email = email.lower().strip()

    # Regex básico para email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError('Formato de email inválido')

    return email


def validate_phone(phone: str) -> str:
    """
    Valida y normaliza números telefónicos.

    Args:
        phone: Número telefónico a validar

    Returns:
        Teléfono normalizado

    Raises:
        ValueError: Si el formato es inválido

    Ejemplo:
        Entrada: "+52 (555) 123-4567"
        Salida: "+525551234567"
    """
    if not phone:
        raise ValueError('Teléfono es requerido')

    # Remover espacios, paréntesis, guiones
    cleaned = re.sub(r'[\s\(\)\-\.]', '', phone.strip())

    # Validar que solo contenga números y opcionalmente + al inicio
    if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
        raise ValueError('Teléfono debe contener entre 10 y 15 dígitos')

    return cleaned


def validate_non_empty_string(value: str, field_name: str = "Campo") -> str:
    """
    Valida que un string no esté vacío y lo normaliza.

    Args:
        value: Valor a validar
        field_name: Nombre del campo para el mensaje de error

    Returns:
        String normalizado

    Raises:
        ValueError: Si está vacío o solo espacios

    Ejemplo:
        @validator('first_name')
        def validate_first_name(cls, v):
            return validate_non_empty_string(v, "Nombre")
    """
    if not value or not value.strip():
        raise ValueError(f'{field_name} no puede estar vacío')

    # Normalizar espacios
    normalized = ' '.join(value.strip().split())

    if len(normalized) < 2:
        raise ValueError(f'{field_name} debe tener al menos 2 caracteres')

    return normalized


def validate_document_number(document: str, document_type: str) -> str:
    """
    Valida números de documentos según el tipo.

    Args:
        document: Número de documento
        document_type: Tipo de documento (RFC, CURP, Passport, etc.)

    Returns:
        Documento validado

    Raises:
        ValueError: Si el formato es inválido para el tipo
    """
    if not document:
        raise ValueError('Número de documento es requerido')

    document = document.upper().strip()

    if document_type == "RFC":
        # RFC: 12-13 caracteres alfanuméricos
        if not re.match(r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$', document):
            raise ValueError('Formato de RFC inválido')

    elif document_type == "CURP":
        # CURP: 18 caracteres específicos
        if not re.match(r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$', document):
            raise ValueError('Formato de CURP inválido')

    elif document_type == "PASSPORT":
        # Pasaporte: 6-9 caracteres alfanuméricos
        if not re.match(r'^[A-Z0-9]{6,9}$', document):
            raise ValueError('Formato de pasaporte inválido')

    elif document_type == "DRIVER_LICENSE":
        # Licencia: formato flexible
        if not re.match(r'^[A-Z0-9]{8,20}$', document):
            raise ValueError('Formato de licencia inválido')

    elif document_type  == "OTHER":
        # Otro dicuemnto como: carta de historial penal o numero de seguro social
        if not re.match(r'^[A-Z0-9]{8,20}$', document):
            raise ValueError('Formato de documento inválido')
        

    return document


# ==================== VALIDADORES NUMÉRICOS ====================

def validate_decimal_range(
    value: Any,
    min_val: Optional[Decimal] = None,
    max_val: Optional[Decimal] = None,
    field_name: str = "Campo"
) -> Decimal:
    """
    Valida que un decimal esté en un rango específico.

    Args:
        value: Valor a validar (puede ser str, int, float, Decimal)
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        field_name: Nombre del campo para mensajes de error

    Returns:
        Decimal validado

    Raises:
        ValueError: Si está fuera del rango o no es convertible

    Ejemplo:
        # Para altura entre 0.5 y 2.5 metros
        @validator('height')
        def validate_height(cls, v):
            return validate_decimal_range(v, Decimal('0.5'), Decimal('2.5'), "Altura")
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f'{field_name} debe ser un número válido')

    if min_val is not None and decimal_value < min_val:
        raise ValueError(f'{field_name} debe ser mayor o igual a {min_val}')

    if max_val is not None and decimal_value > max_val:
        raise ValueError(f'{field_name} debe ser menor o igual a {max_val}')

    return decimal_value


def validate_positive_integer(value: int, field_name: str = "Campo") -> int:
    """
    Valida que un entero sea positivo.

    Args:
        value: Valor a validar
        field_name: Nombre del campo

    Returns:
        Entero validado

    Raises:
        ValueError: Si no es positivo

    Ejemplo:
        @validator('age')
        def validate_age(cls, v):
            return validate_positive_integer(v, "Edad")
    """
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f'{field_name} debe ser un número entero positivo')

    return value


def validate_age(age: int) -> int:
    """
    Valida que la edad esté en un rango realista.

    Args:
        age: Edad a validar

    Returns:
        Edad validada

    Raises:
        ValueError: Si la edad es irreal
    """
    if age < 0:
        raise ValueError('La edad no puede ser negativa')

    if age > 150:
        raise ValueError('La edad no puede ser mayor a 150 años')

    return age


# ==================== VALIDADORES DE FECHAS ====================

def validate_birth_date(birth_date: date) -> date:
    """
    Valida una fecha de nacimiento.

    Args:
        birth_date: Fecha de nacimiento

    Returns:
        Fecha validada

    Raises:
        ValueError: Si la fecha es inválida

    Ejemplo:
        @validator('birth_date')
        def validate_birth(cls, v):
            return validate_birth_date(v)
    """
    if not birth_date:
        raise ValueError('Fecha de nacimiento es requerida')

    today = date.today()

    # No puede ser en el futuro
    if birth_date > today:
        raise ValueError('La fecha de nacimiento no puede ser en el futuro')

    # No puede ser más de 150 años atrás
    min_date = date(today.year - 150, today.month, today.day)
    if birth_date < min_date:
        raise ValueError('La fecha de nacimiento no puede ser anterior a 150 años')

    return birth_date


def validate_future_date(date_value: datetime, field_name: str = "Fecha") -> datetime:
    """
    Valida que una fecha sea en el futuro.

    Args:
        date_value: Fecha a validar
        field_name: Nombre del campo

    Returns:
        Fecha validada

    Raises:
        ValueError: Si la fecha no es futura
    """
    if date_value <= datetime.now():
        raise ValueError(f'{field_name} debe ser en el futuro')

    return date_value


# ==================== VALIDADORES DE ARRAYS Y JSON ====================

def validate_phone_list(phones: List[str]) -> List[str]:
    """
    Valida una lista de teléfonos.

    Args:
        phones: Lista de teléfonos

    Returns:
        Lista de teléfonos validados

    Raises:
        ValueError: Si algún teléfono es inválido

    Ejemplo:
        @validator('phones')
        def validate_phone_numbers(cls, v):
            return validate_phone_list(v)
    """
    if not phones:
        return []

    if len(phones) > 5:
        raise ValueError('Máximo 5 teléfonos permitidos')

    validated_phones = []
    for phone in phones:
        validated_phones.append(validate_phone(phone))

    # Verificar duplicados
    if len(set(validated_phones)) != len(validated_phones):
        raise ValueError('No se permiten teléfonos duplicados')

    return validated_phones


def validate_json_structure(
    json_data: Dict[str, Any],
    required_fields: Optional[List[str]] = None,
    allowed_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Valida la estructura de un objeto JSON.

    Args:
        json_data: Datos JSON a validar
        required_fields: Campos que deben estar presentes
        allowed_fields: Campos permitidos (si se especifica, rechaza otros)

    Returns:
        JSON validado

    Raises:
        ValueError: Si la estructura es inválida

    Ejemplo:
        @validator('additional_data')
        def validate_additional_data(cls, v):
            return validate_json_structure(
                v,
                required_fields=['contact_preference'],
                allowed_fields=['contact_preference', 'notes', 'tags']
            )
    """
    if not isinstance(json_data, dict):
        raise ValueError('Debe ser un objeto JSON válido')

    # Verificar campos requeridos
    if required_fields:
        missing_fields = [field for field in required_fields if field not in json_data]
        if missing_fields:
            raise ValueError(f'Campos requeridos faltantes: {", ".join(missing_fields)}')

    # Verificar campos permitidos
    if allowed_fields:
        invalid_fields = [field for field in json_data.keys() if field not in allowed_fields]
        if invalid_fields:
            raise ValueError(f'Campos no permitidos: {", ".join(invalid_fields)}')

    return json_data


# ==================== VALIDADORES DE ENUMS ====================

def validate_enum_value(value: str, valid_values: List[str], field_name: str = "Campo") -> str:
    """
    Valida que un valor esté en una lista de valores permitidos.

    Args:
        value: Valor a validar
        valid_values: Lista de valores válidos
        field_name: Nombre del campo

    Returns:
        Valor validado

    Raises:
        ValueError: Si el valor no es válido

    Ejemplo:
        @validator('gender')
        def validate_gender(cls, v):
            return validate_enum_value(v, ['M', 'F', 'O'], "Género")
    """
    if value not in valid_values:
        raise ValueError(f'{field_name} debe ser uno de: {", ".join(valid_values)}')

    return value


# ==================== UTILIDADES DE VALIDACIÓN ====================

def calculate_age_from_birth_date(birth_date: date) -> int:
    """
    Calcula la edad a partir de la fecha de nacimiento.

    Args:
        birth_date: Fecha de nacimiento

    Returns:
        Edad en años

    Ejemplo:
        @validator('age', always=True)
        def calculate_age(cls, v, values):
            if 'birth_date' in values:
                return calculate_age_from_birth_date(values['birth_date'])
            return v
    """
    today = date.today()
    age = today.year - birth_date.year

    # Ajustar si el cumpleaños no ha pasado este año
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


def normalize_text(text: str) -> str:
    """
    Normaliza texto para almacenamiento consistente.

    Args:
        text: Texto a normalizar

    Returns:
        Texto normalizado

    Ejemplo:
        @validator('first_name', 'last_name')
        def normalize_names(cls, v):
            return normalize_text(v).title()
    """
    if not text:
        return text

    # Remover espacios extra y normalizar
    normalized = ' '.join(text.strip().split())

    # Remover caracteres especiales peligrosos pero mantener acentos
    # Solo permite letras, números, espacios y algunos caracteres especiales comunes
    cleaned = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ.,\'-]', '', normalized)

    return cleaned