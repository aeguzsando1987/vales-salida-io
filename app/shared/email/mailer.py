"""
Mailer - Envío de correos usando smtplib (sin dependencias externas adicionales).

Prioridad de configuración:
1. BD (tabla system_config) — permite configurar desde el panel de admin
2. Variables de entorno (.env) — fallback

Funciona en contextos síncronos (Celery) y asíncronos (FastAPI).
"""

import smtplib
import ssl
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Optional

logger = logging.getLogger(__name__)


def get_email_config(db=None) -> dict:
    """
    Obtiene la configuración de correo.

    Prioridad:
    1. BD (system_config) si se pasa db
    2. Variables de entorno / settings como fallback
    """
    from app.config.settings import settings

    config = {
        "enabled": getattr(settings, "mail_enabled", False),
        "server": getattr(settings, "mail_server", "smtp.gmail.com"),
        "port": getattr(settings, "mail_port", 587),
        "username": getattr(settings, "mail_username", ""),
        "password": getattr(settings, "mail_password", ""),
        "from_email": getattr(settings, "mail_from", ""),
        "from_name": getattr(settings, "mail_from_name", "Sistema de Vales GPA"),
        "use_tls": getattr(settings, "mail_use_tls", True),
    }

    if db:
        try:
            from app.shared.models.system_config import SystemConfig
            rows = db.query(SystemConfig).filter(
                SystemConfig.key.in_([
                    "mail_enabled", "mail_server", "mail_port",
                    "mail_username", "mail_password", "mail_from",
                    "mail_from_name", "mail_use_tls"
                ])
            ).all()
            db_map = {r.key: r.value for r in rows}

            if "mail_enabled" in db_map:
                config["enabled"] = db_map["mail_enabled"].lower() == "true"
            if "mail_server" in db_map and db_map["mail_server"]:
                config["server"] = db_map["mail_server"]
            if "mail_port" in db_map and db_map["mail_port"]:
                config["port"] = int(db_map["mail_port"])
            if "mail_username" in db_map and db_map["mail_username"]:
                config["username"] = db_map["mail_username"]
            if "mail_password" in db_map and db_map["mail_password"]:
                config["password"] = db_map["mail_password"]
            if "mail_from" in db_map and db_map["mail_from"]:
                config["from_email"] = db_map["mail_from"]
            if "mail_from_name" in db_map and db_map["mail_from_name"]:
                config["from_name"] = db_map["mail_from_name"]
            if "mail_use_tls" in db_map:
                config["use_tls"] = db_map["mail_use_tls"].lower() == "true"
        except Exception as e:
            logger.warning(f"[MAILER] No se pudo leer config de BD, usando .env: {e}")

    return config


def send_email_sync(
    config: dict,
    recipients: list,
    subject: str,
    html_body: str,
    attachment_path: Optional[str] = None,
    attachment_name: Optional[str] = None
) -> None:
    """
    Envía un correo de forma síncrona usando smtplib.
    Compatible con Celery tasks y contextos síncronos.

    Args:
        config: Resultado de get_email_config()
        recipients: Lista de emails destinatarios
        subject: Asunto del correo
        html_body: Cuerpo HTML del mensaje
        attachment_path: Ruta al archivo adjunto (opcional)
        attachment_name: Nombre del adjunto (opcional, default: basename del path)

    Raises:
        Exception: Si hay error al conectar o enviar
    """
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = ", ".join(recipients)

    # Cuerpo HTML
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Adjunto PDF
    if attachment_path and os.path.exists(attachment_path):
        filename = attachment_name or os.path.basename(attachment_path)
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)
    elif attachment_path:
        logger.warning(f"[MAILER] Adjunto no encontrado: {attachment_path}")

    # Enviar
    context = ssl.create_default_context()
    try:
        if config["use_tls"]:
            with smtplib.SMTP(config["server"], config["port"], timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(config["username"], config["password"])
                server.sendmail(config["from_email"], recipients, msg.as_string())
        else:
            with smtplib.SMTP_SSL(config["server"], config["port"], context=context, timeout=30) as server:
                server.login(config["username"], config["password"])
                server.sendmail(config["from_email"], recipients, msg.as_string())

        logger.info(f"[MAILER] Correo enviado a: {recipients}")
    except Exception as e:
        logger.error(f"[MAILER] Error enviando correo: {e}")
        raise
