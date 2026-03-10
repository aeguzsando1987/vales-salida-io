"""
Router de configuración de correo electrónico.

Permite configurar SMTP desde el panel de administración sin editar .env.
Solo accesible para Admin (role=1).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from app.shared.dependencies import get_current_user
from app.shared.models.system_config import SystemConfig
from app.shared.email.mailer import get_email_config, send_email_sync
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/email-config", tags=["Admin - Email Config"])


# ==================== SCHEMAS ====================

class EmailConfigUpdate(BaseModel):
    enabled: bool = True
    server: str = "smtp.gmail.com"
    port: int = 587
    username: str
    password: Optional[str] = None  # None = no cambiar password existente
    from_email: str
    from_name: str = "Sistema de Vales GPA"
    use_tls: bool = True


class EmailConfigResponse(BaseModel):
    enabled: bool
    server: str
    port: int
    username: str
    password_set: bool  # True si hay contraseña configurada (no la devuelve)
    from_email: str
    from_name: str
    use_tls: bool
    source: str  # "database" o "env"


class TestEmailRequest(BaseModel):
    recipient: str


# ==================== HELPERS ====================

def _require_admin(current_user=Depends(get_current_user)):
    if current_user.role not in (1,):
        raise HTTPException(status_code=403, detail="Solo administradores pueden modificar la configuración de correo")
    return current_user


def _upsert_config(db: Session, key: str, value: str, user_id: int):
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = value
        row.updated_by = user_id
    else:
        row = SystemConfig(key=key, value=value, updated_by=user_id)
        db.add(row)


# ==================== ENDPOINTS ====================

@router.get("/", summary="Obtener configuración de correo actual", response_model=EmailConfigResponse)
def get_email_configuration(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Retorna la configuración de correo activa (sin mostrar la contraseña)."""
    if current_user.role not in (1,):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    config = get_email_config(db)

    # Determinar fuente: ¿está configurado en BD?
    rows = db.query(SystemConfig).filter(SystemConfig.key == "mail_server").first()
    source = "database" if rows else "env"

    return EmailConfigResponse(
        enabled=config["enabled"],
        server=config["server"],
        port=config["port"],
        username=config["username"],
        password_set=bool(config["password"]),
        from_email=config["from_email"],
        from_name=config["from_name"],
        use_tls=config["use_tls"],
        source=source
    )


@router.put("/", summary="Guardar configuración de correo en BD")
def save_email_configuration(
    data: EmailConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Guarda la configuración SMTP en la BD. Tiene prioridad sobre las variables .env."""
    if current_user.role not in (1,):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    user_id = current_user.id

    _upsert_config(db, "mail_enabled", str(data.enabled).lower(), user_id)
    _upsert_config(db, "mail_server", data.server, user_id)
    _upsert_config(db, "mail_port", str(data.port), user_id)
    _upsert_config(db, "mail_username", data.username, user_id)
    _upsert_config(db, "mail_from", data.from_email, user_id)
    _upsert_config(db, "mail_from_name", data.from_name, user_id)
    _upsert_config(db, "mail_use_tls", str(data.use_tls).lower(), user_id)

    # Solo actualizar contraseña si se proporcionó una nueva
    if data.password:
        _upsert_config(db, "mail_password", data.password, user_id)

    db.commit()

    return {"message": "Configuración de correo guardada correctamente"}


@router.post("/test", summary="Enviar correo de prueba")
def send_test_email(
    request: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Envía un correo de prueba para verificar la configuración SMTP."""
    if current_user.role not in (1,):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    config = get_email_config(db)

    if not config["enabled"]:
        raise HTTPException(status_code=400, detail="El correo está desactivado en la configuración")

    if not config["username"] or not config["password"]:
        raise HTTPException(status_code=400, detail="Faltan credenciales SMTP (usuario y/o contraseña)")

    try:
        send_email_sync(
            config=config,
            recipients=[request.recipient],
            subject="✅ Correo de prueba — Sistema de Vales GPA",
            html_body=f"""
            <div style="font-family:Arial,sans-serif;padding:24px;max-width:500px;">
              <h2 style="color:#1e3a5f;">¡Configuración correcta!</h2>
              <p>Este es un correo de prueba del <strong>Sistema de Vales GPA</strong>.</p>
              <p>Si recibiste este mensaje, la configuración SMTP está funcionando correctamente.</p>
              <hr style="margin:16px 0;border:none;border-top:1px solid #e5e7eb;">
              <p style="color:#9ca3af;font-size:12px;">Servidor: {config['server']}:{config['port']}</p>
            </div>
            """
        )
        return {"message": f"Correo de prueba enviado a {request.recipient}"}
    except Exception as e:
        logger.error(f"[EMAIL CONFIG] Error en correo de prueba: {e}")
        raise HTTPException(status_code=500, detail=f"Error al enviar correo: {str(e)}")
