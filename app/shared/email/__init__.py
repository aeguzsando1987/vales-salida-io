"""
Módulo de correo electrónico del sistema de vales.
"""
from .mailer import get_email_config, send_email_sync

__all__ = ["get_email_config", "send_email_sync"]
