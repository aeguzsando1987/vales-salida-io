"""
Celery Tasks Module (Phase 4)

Configuración de Celery y exportación de tareas asíncronas.
Las tareas se ejecutan en workers separados para no bloquear la API.
"""

from celery import Celery
from app.config.settings import settings

# Crear instancia de Celery
celery_app = Celery('voucher_tasks')

# Cargar configuración desde celeryconfig.py
celery_app.config_from_object('celeryconfig')

# Importar tareas (después de configurar celery_app)
from .voucher_tasks import generate_pdf_task, generate_qr_task

__all__ = ["celery_app", "generate_pdf_task", "generate_qr_task"]
