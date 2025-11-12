"""
Excepciones personalizadas para la aplicación

Este módulo define excepciones específicas del dominio que proporcionan
información más clara sobre errores de negocio y facilitan el manejo
de errores en las diferentes capas de la aplicación.
"""

from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """
    Excepción base para toda la aplicación.

    Todas las excepciones custom deben heredar de esta clase
    para mantener consistencia en el manejo de errores.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ==================== EXCEPCIONES DE ENTIDADES ====================

class EntityNotFoundError(BaseAppException):
    """
    Se lanza cuando no se encuentra una entidad específica.

    Ejemplo:
        raise EntityNotFoundError("Usuario", 123)
        # Mensaje: "Usuario con ID 123 no encontrado"
    """

    def __init__(self, entity_name: str, entity_id: Any):
        message = f"{entity_name} con ID {entity_id} no encontrado"
        super().__init__(message, status_code=404, details={
            "entity": entity_name,
            "id": entity_id
        })


class EntityAlreadyExistsError(BaseAppException):
    """
    Se lanza cuando se intenta crear una entidad que ya existe.

    Ejemplo:
        raise EntityAlreadyExistsError("Usuario", "email", "test@test.com")
        # Mensaje: "Usuario con email test@test.com ya existe"
    """

    def __init__(self, entity_name: str, field_name: str, field_value: Any):
        message = f"{entity_name} con {field_name} {field_value} ya existe"
        super().__init__(message, status_code=409, details={
            "entity": entity_name,
            "field": field_name,
            "value": field_value
        })


class EntityValidationError(BaseAppException):
    """
    Se lanza cuando los datos de una entidad no pasan las validaciones.

    Ejemplo:
        raise EntityValidationError("Person", {
            "age": "Debe ser mayor a 0",
            "email": "Formato inválido"
        })
    """

    def __init__(self, entity_name: str, validation_errors: Dict[str, str]):
        message = f"Errores de validación en {entity_name}"
        super().__init__(message, status_code=422, details={
            "entity": entity_name,
            "validation_errors": validation_errors
        })


# ==================== EXCEPCIONES DE NEGOCIO ====================

class BusinessRuleError(BaseAppException):
    """
    Se lanza cuando se viola una regla de negocio.

    Ejemplo:
        raise BusinessRuleError(
            "No se puede eliminar un usuario con personas asociadas",
            details={"user_id": 123, "associated_persons": 5}
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class InsufficientPermissionsError(BaseAppException):
    """
    Se lanza cuando un usuario no tiene permisos suficientes.

    Ejemplo:
        raise InsufficientPermissionsError("admin", "delete_user")
    """

    def __init__(self, required_role: str, action: str):
        message = f"Se requiere rol '{required_role}' para realizar '{action}'"
        super().__init__(message, status_code=403, details={
            "required_role": required_role,
            "action": action
        })


# ==================== EXCEPCIONES DE DATOS ====================

class DataIntegrityError(BaseAppException):
    """
    Se lanza cuando hay problemas de integridad de datos.

    Ejemplo:
        raise DataIntegrityError(
            "No se puede eliminar el departamento porque tiene empleados asignados"
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)


class InvalidDataTypeError(BaseAppException):
    """
    Se lanza cuando un tipo de dato no es válido para una operación.

    Ejemplo:
        raise InvalidDataTypeError("height", "1.85", "Decimal")
    """

    def __init__(self, field_name: str, provided_value: Any, expected_type: str):
        message = f"Campo '{field_name}' con valor '{provided_value}' no es de tipo {expected_type}"
        super().__init__(message, status_code=422, details={
            "field": field_name,
            "provided_value": provided_value,
            "expected_type": expected_type
        })


# ==================== EXCEPCIONES DE CONFIGURACIÓN ====================

class ConfigurationError(BaseAppException):
    """
    Se lanza cuando hay problemas con la configuración de la aplicación.

    Ejemplo:
        raise ConfigurationError("DATABASE_URL no está configurada")
    """

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


# ==================== UTILIDADES PARA MANEJO DE EXCEPCIONES ====================

def format_validation_error(field: str, message: str) -> Dict[str, str]:
    """
    Formatea un error de validación para uso consistente.

    Args:
        field: Nombre del campo con error
        message: Mensaje de error

    Returns:
        Diccionario formateado para EntityValidationError

    Ejemplo:
        errors = {}
        errors.update(format_validation_error("email", "Formato inválido"))
        raise EntityValidationError("User", errors)
    """
    return {field: message}


def handle_sqlalchemy_error(error: Exception, entity_name: str) -> BaseAppException:
    """
    Convierte errores de SQLAlchemy en excepciones de aplicación.

    Args:
        error: Excepción de SQLAlchemy
        entity_name: Nombre de la entidad afectada

    Returns:
        Excepción de aplicación apropiada

    Ejemplo:
        try:
            db.commit()
        except SQLAlchemyError as e:
            raise handle_sqlalchemy_error(e, "User")
    """
    error_str = str(error).lower()

    if "unique constraint" in error_str or "duplicate key" in error_str:
        # Extraer información del campo duplicado si es posible
        return EntityAlreadyExistsError(entity_name, "field", "value")

    elif "foreign key constraint" in error_str:
        return DataIntegrityError(
            f"No se puede procesar {entity_name} debido a restricciones de integridad referencial"
        )

    elif "not null constraint" in error_str:
        return EntityValidationError(entity_name, {"field": "Campo requerido no puede estar vacío"})

    else:
        return BaseAppException(f"Error de base de datos al procesar {entity_name}", status_code=500)