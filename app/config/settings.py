"""
Sistema de configuración híbrida: config.toml + .env

Este módulo carga configuraciones desde dos fuentes:
1. config.toml - Configuraciones públicas y estáticas
2. .env - Variables de entorno y secretos

La precedencia es: .env > config.toml > valores por defecto
"""

import os
import toml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración híbrida de la aplicación.

    Carga configuraciones desde:
    - config.toml (configuraciones públicas)
    - .env (secretos y variables de entorno)

    Los valores de .env tienen prioridad sobre config.toml
    """

    # ==================== APP ====================
    app_name: str = Field(default="Demo API", env="APP_NAME")
    app_title: str = Field(default="Demo API - Plantilla Escalable")
    app_description: str = Field(default="API FastAPI con arquitectura de capas")
    app_version: str = Field(default="1.0.0", env="VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # ==================== SERVER ====================
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    reload: bool = Field(default=False)
    workers: int = Field(default=4)

    # ==================== DATABASE ====================
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)
    db_pool_timeout: int = Field(default=30)
    db_pool_recycle: int = Field(default=1800)
    db_echo_sql: bool = Field(default=False)

    # ==================== SECURITY ====================
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7)
    password_min_length: int = Field(default=8)
    max_login_attempts: int = Field(default=5)
    token_blacklist_enabled: bool = Field(default=True)

    # Admin por defecto
    default_admin_email: str = Field(..., env="DEFAULT_ADMIN_EMAIL")
    default_admin_password: str = Field(..., env="DEFAULT_ADMIN_PASSWORD")

    # ==================== CORS ====================
    cors_allow_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    # ==================== FEATURES ====================
    enable_swagger: bool = Field(default=True)
    enable_redoc: bool = Field(default=True)
    enable_cors: bool = Field(default=True)
    enable_webhooks: bool = Field(default=False)
    enable_rate_limiting: bool = Field(default=False)
    enable_email_notifications: bool = Field(default=False)

    # ==================== PAGINATION ====================
    default_page: int = Field(default=1)
    default_page_size: int = Field(default=20)
    max_page_size: int = Field(default=100)
    max_limit: int = Field(default=1000)

    # ==================== VALIDATION ====================
    # Person validations
    person_min_age: int = Field(default=0)
    person_max_age: int = Field(default=150)
    person_min_height: float = Field(default=0.5)
    person_max_height: float = Field(default=2.5)
    person_min_weight: float = Field(default=20.0)
    person_max_weight: float = Field(default=300.0)
    person_min_salary: float = Field(default=0.0)
    person_max_salary: float = Field(default=10000000.0)

    # String validations
    min_name_length: int = Field(default=2)
    max_name_length: int = Field(default=100)
    min_email_length: int = Field(default=5)
    max_email_length: int = Field(default=255)

    # Array validations
    max_phone_numbers: int = Field(default=5)
    max_alternate_emails: int = Field(default=3)
    max_skills: int = Field(default=50)
    max_languages: int = Field(default=10)

    # ==================== LOGGING ====================
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    log_file_path: str = Field(default="logs/app.log")
    enable_correlation_id: bool = Field(default=True)
    log_max_bytes: int = Field(default=10485760)  # 10MB
    log_backup_count: int = Field(default=5)

    # ==================== MONITORING ====================
    enable_metrics: bool = Field(default=False)
    metrics_endpoint: str = Field(default="/metrics")
    enable_health_check: bool = Field(default=True)
    health_check_endpoint: str = Field(default="/health")

    # ==================== API ====================
    api_prefix: str = Field(default="")
    api_version_prefix: str = Field(default="")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")

    # Response configuration
    include_timestamp: bool = Field(default=True)
    include_request_id: bool = Field(default=True)
    pretty_json: bool = Field(default=False)

    # ==================== CACHE ====================
    cache_enabled: bool = Field(default=False)
    cache_backend: str = Field(default="memory")
    cache_default_ttl: int = Field(default=300)

    # ==================== ENVIRONMENT ====================
    environment: str = Field(default="development", env="ENVIRONMENT")

    # ==================== SCHEDULER ====================
    scheduler_enabled: bool = Field(
        default=True,
        description="Activar/desactivar scheduler automático"
    )

    scheduler_overdue_hour: int = Field(
        default=0,
        ge=0,
        le=23,
        description="Hora de ejecución del job de vencimientos (0-23 UTC)"
    )

    scheduler_overdue_minute: int = Field(
        default=0,
        ge=0,
        le=59,
        description="Minuto de ejecución del job de vencimientos (0-59)"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def __init__(self, **kwargs):
        """Inicializa configuración cargando config.toml primero."""
        # Cargar config.toml
        config_path = Path(__file__).parent.parent.parent / "config.toml"
        config_toml_data = {}
        if config_path.exists():
            config_toml_data = toml.load(config_path)
            # Aplicar configuraciones del config.toml
            kwargs = self._apply_toml_config(kwargs, config_toml_data)

        super().__init__(**kwargs)

        # Aplicar configuraciones específicas del ambiente
        self._apply_environment_config(config_toml_data)

    def _apply_toml_config(self, kwargs: Dict[str, Any], toml_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica configuraciones desde config.toml.
        Solo aplica si no están en kwargs (precedencia de .env).
        """

        # Mapeo de campos del TOML a campos de Settings
        mappings = {
            # App
            ("app", "title"): "app_title",
            ("app", "description"): "app_description",
            ("app", "version"): "app_version",
            ("app", "debug"): "debug",

            # Server
            ("server", "host"): "host",
            ("server", "port"): "port",
            ("server", "reload"): "reload",
            ("server", "workers"): "workers",

            # Database
            ("database", "pool_size"): "db_pool_size",
            ("database", "max_overflow"): "db_max_overflow",
            ("database", "pool_timeout"): "db_pool_timeout",
            ("database", "pool_recycle"): "db_pool_recycle",
            ("database", "echo_sql"): "db_echo_sql",

            # Security
            ("security", "algorithm"): "algorithm",
            ("security", "access_token_expire_minutes"): "access_token_expire_minutes",
            ("security", "refresh_token_expire_days"): "refresh_token_expire_days",
            ("security", "password_min_length"): "password_min_length",
            ("security", "max_login_attempts"): "max_login_attempts",
            ("security", "token_blacklist_enabled"): "token_blacklist_enabled",

            # CORS
            ("security", "cors", "allow_origins"): "cors_allow_origins",
            ("security", "cors", "allow_credentials"): "cors_allow_credentials",
            ("security", "cors", "allow_methods"): "cors_allow_methods",
            ("security", "cors", "allow_headers"): "cors_allow_headers",

            # Features
            ("app", "features", "enable_swagger"): "enable_swagger",
            ("app", "features", "enable_redoc"): "enable_redoc",
            ("app", "features", "enable_cors"): "enable_cors",
            ("app", "features", "enable_webhooks"): "enable_webhooks",
            ("app", "features", "enable_rate_limiting"): "enable_rate_limiting",
            ("app", "features", "enable_email_notifications"): "enable_email_notifications",

            # Pagination
            ("pagination", "default_page"): "default_page",
            ("pagination", "default_page_size"): "default_page_size",
            ("pagination", "max_page_size"): "max_page_size",
            ("pagination", "max_limit"): "max_limit",

            # Validation - Person
            ("validation", "person", "min_age"): "person_min_age",
            ("validation", "person", "max_age"): "person_max_age",
            ("validation", "person", "min_height"): "person_min_height",
            ("validation", "person", "max_height"): "person_max_height",
            ("validation", "person", "min_weight"): "person_min_weight",
            ("validation", "person", "max_weight"): "person_max_weight",
            ("validation", "person", "min_salary"): "person_min_salary",
            ("validation", "person", "max_salary"): "person_max_salary",

            # Validation - Strings
            ("validation", "strings", "min_name_length"): "min_name_length",
            ("validation", "strings", "max_name_length"): "max_name_length",
            ("validation", "strings", "min_email_length"): "min_email_length",
            ("validation", "strings", "max_email_length"): "max_email_length",

            # Validation - Arrays
            ("validation", "arrays", "max_phone_numbers"): "max_phone_numbers",
            ("validation", "arrays", "max_alternate_emails"): "max_alternate_emails",
            ("validation", "arrays", "max_skills"): "max_skills",
            ("validation", "arrays", "max_languages"): "max_languages",

            # Logging
            ("logging", "level"): "log_level",
            ("logging", "format"): "log_format",
            ("logging", "file_path"): "log_file_path",
            ("logging", "enable_correlation_id"): "enable_correlation_id",
            ("logging", "max_bytes"): "log_max_bytes",
            ("logging", "backup_count"): "log_backup_count",

            # Monitoring
            ("monitoring", "enable_metrics"): "enable_metrics",
            ("monitoring", "metrics_endpoint"): "metrics_endpoint",
            ("monitoring", "enable_health_check"): "enable_health_check",
            ("monitoring", "health_check_endpoint"): "health_check_endpoint",

            # API
            ("api", "prefix"): "api_prefix",
            ("api", "version_prefix"): "api_version_prefix",
            ("api", "docs_url"): "docs_url",
            ("api", "redoc_url"): "redoc_url",
            ("api", "openapi_url"): "openapi_url",

            # API Response
            ("api", "response", "include_timestamp"): "include_timestamp",
            ("api", "response", "include_request_id"): "include_request_id",
            ("api", "response", "pretty_json"): "pretty_json",

            # Cache
            ("cache", "enabled"): "cache_enabled",
            ("cache", "backend"): "cache_backend",
            ("cache", "default_ttl"): "cache_default_ttl",

            # Scheduler
            ("scheduler", "enabled"): "scheduler_enabled",
            ("scheduler", "overdue_check_hour"): "scheduler_overdue_hour",
            ("scheduler", "overdue_check_minute"): "scheduler_overdue_minute",
        }

        for toml_path, setting_name in mappings.items():
            if setting_name not in kwargs:  # Solo si no viene de .env
                value = toml_data
                try:
                    for key in toml_path:
                        value = value[key]
                    kwargs[setting_name] = value
                except KeyError:
                    pass  # El valor no existe en el TOML, usar default

        return kwargs

    def _apply_environment_config(self, toml_data: Dict[str, Any]):
        """Aplica configuraciones específicas del ambiente actual."""
        env = self.environment.lower()
        env_config = toml_data.get("environments", {}).get(env, {})

        for key, value in env_config.items():
            # Convertir snake_case si es necesario
            if hasattr(self, key):
                setattr(self, key, value)

    @validator("port", pre=True)
    def validate_port(cls, v):
        """Valida que el puerto sea un entero válido."""
        if isinstance(v, str):
            # Remover caracteres no numéricos
            v = ''.join(filter(str.isdigit, v))
        return int(v) if v else 8001

    @validator("debug", pre=True)
    def validate_debug(cls, v):
        """Convierte string a boolean."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    def get_database_url(self) -> str:
        """Retorna la URL de la base de datos."""
        return self.database_url

    def is_development(self) -> bool:
        """Verifica si está en ambiente de desarrollo."""
        return self.environment.lower() == "development"

    def is_production(self) -> bool:
        """Verifica si está en ambiente de producción."""
        return self.environment.lower() == "production"

    def get_cors_origins(self) -> List[str]:
        """Retorna lista de orígenes permitidos para CORS."""
        return self.cors_allow_origins


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia singleton de Settings.

    Usa lru_cache para asegurar que solo se crea una instancia.
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()
