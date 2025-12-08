"""
Celery Configuration for Phase 4 (PDF/QR Generation)

This file is automatically loaded by Celery when starting workers.
Configuration values are read from app/config/settings.py which loads
from config.toml and .env files.
"""

from app.config.settings import settings

# Broker settings
broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

# Serialization
task_serializer = settings.celery_task_serializer
result_serializer = settings.celery_result_serializer
accept_content = ['json']

# Timezone
timezone = settings.celery_timezone
enable_utc = settings.celery_enable_utc

# Task settings
task_track_started = True
task_time_limit = 600  # 10 minutes max per task
task_soft_time_limit = 540  # 9 minutes soft limit

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# Result backend settings
result_expires = 3600  # 1 hour

# Task routes (optional - for task routing)
task_routes = {
    'app.shared.tasks.voucher_tasks.generate_pdf_task': {'queue': 'pdf'},
    'app.shared.tasks.voucher_tasks.generate_qr_task': {'queue': 'qr'},
}

# Ignore result for tasks that don't need it
task_ignore_result = False
