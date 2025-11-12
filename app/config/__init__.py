"""
Modulo de configuracion hibrida.

Exporta el settings singleton para uso en toda la aplicacion.

Uso:
    from app.config import settings

    database_url = settings.database_url
    debug_mode = settings.debug
"""

from .settings import settings, get_settings

__all__ = ["settings", "get_settings"]
