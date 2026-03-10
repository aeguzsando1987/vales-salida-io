"""
Voucher Tasks (Phase 4)

Tareas asíncronas de Celery para generación de PDFs y códigos QR.
Estas tareas se ejecutan en workers separados para no bloquear la API principal.
"""

from celery import Task
from database import SessionLocal
from app.entities.vouchers.services.voucher_service import VoucherService
from app.shared.utilities import PDFGenerator, QRGenerator, FileManager
from app.config.settings import settings
from datetime import datetime
import logging
import os

# Imports de TODOS los modelos para que SQLAlchemy pueda resolver relationships
from database import User
from app.entities.individuals.models.individual import Individual
from app.entities.companies.models.company import Company
from app.entities.countries.models.country import Country
from app.entities.states.models.state import State
from app.entities.branches.models.branch import Branch
from app.entities.products.models.product import Product
from app.entities.vouchers.models.voucher import Voucher
from app.entities.voucher_details.models.voucher_detail import VoucherDetail
from app.entities.vouchers.models.entry_log import EntryLog
from app.entities.vouchers.models.out_log import OutLog

from . import celery_app

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """
    Tarea base con gestión automática de sesión de base de datos.

    Proporciona una propiedad self.db que crea una sesión de BD
    y la cierra automáticamente al finalizar la tarea.
    """
    _db = None

    @property
    def db(self):
        """Obtiene o crea una sesión de base de datos."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Hook ejecutado después de que la tarea retorna resultado."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name='voucher_tasks.generate_pdf')
def generate_pdf_task(self, voucher_id: int) -> dict:
    """
    Tarea asíncrona para generar PDF de un voucher.

    Esta tarea:
    1. Obtiene el voucher con todas sus relaciones
    2. Verifica si el token QR está expirado y lo regenera si es necesario
    3. Genera la imagen QR
    4. Genera el PDF con el QR embebido
    5. Actualiza los timestamps en el voucher

    Args:
        voucher_id: ID del voucher

    Returns:
        Dict con información del PDF generado:
        {
            'pdf_path': str,      # Ruta absoluta al PDF
            'qr_path': str,       # Ruta absoluta a imagen QR
            'file_size': int,     # Tamaño del PDF en bytes
            'generated_at': str   # Timestamp ISO format
        }

    Raises:
        Exception: Si hay error durante la generación
    """
    pdf_path = None
    qr_path = None

    try:
        logger.info(f"[TASK PDF] Iniciando generación para voucher_id={voucher_id}")

        # Obtener servicio
        service = VoucherService(self.db)

        # Obtener voucher con todas las relaciones
        voucher = service.get_voucher_with_details(voucher_id)
        logger.info(f"[TASK PDF] Voucher obtenido: folio={voucher.folio}")

        # Verificar si el token QR está expirado (>24h)
        if service._is_qr_token_expired(voucher):
            logger.info(f"[TASK PDF] Token QR expirado, regenerando...")
            voucher.qr_token = service._generate_qr_token(voucher_id)
            self.db.commit()
            # Recargar voucher con todas las relaciones después del commit
            voucher = service.get_voucher_with_details(voucher_id)

        # Generar imagen QR
        logger.info(f"[TASK PDF] Generando imagen QR...")
        qr_gen = QRGenerator(
            output_dir=settings.qr_temp_dir,
            box_size=settings.qr_box_size,
            border=settings.qr_border
        )
        qr_path = qr_gen.generate_qr_image(voucher_id, voucher.qr_token)
        logger.info(f"[TASK PDF] QR generado: {qr_path}")

        # Generar PDF
        logger.info(f"[TASK PDF] Generando PDF...")
        pdf_gen = PDFGenerator(
            template_dir=settings.pdf_template_dir,
            temp_dir=settings.pdf_temp_dir
        )
        pdf_path = pdf_gen.generate_voucher_pdf(voucher, qr_path)
        logger.info(f"[TASK PDF] PDF generado: {pdf_path}")

        # Actualizar timestamps en voucher
        voucher.pdf_last_generated_at = datetime.utcnow()
        voucher.qr_image_last_generated_at = datetime.utcnow()
        self.db.commit()

        # Obtener tamaño del archivo
        file_size = FileManager.get_file_size(pdf_path)

        result = {
            'pdf_path': pdf_path,
            'qr_path': qr_path,
            'file_size': file_size,
            'generated_at': datetime.utcnow().isoformat()
        }

        logger.info(f"[TASK PDF] Completado exitosamente para voucher_id={voucher_id}")
        return result

    except Exception as e:
        logger.error(f"[TASK PDF] Error generando PDF para voucher_id={voucher_id}: {e}", exc_info=True)

        # Limpieza de archivos en caso de error
        if qr_path:
            FileManager.delete_file(qr_path)
        if pdf_path:
            FileManager.delete_file(pdf_path)

        # Re-lanzar excepción para que Celery la maneje
        raise


@celery_app.task(base=DatabaseTask, bind=True, name='voucher_tasks.generate_qr')
def generate_qr_task(self, voucher_id: int) -> dict:
    """
    Tarea asíncrona para generar imagen QR de un voucher.

    Esta tarea:
    1. Obtiene el voucher
    2. Verifica si el token está expirado y lo regenera si es necesario
    3. Genera la imagen QR
    4. Actualiza el timestamp en el voucher

    Args:
        voucher_id: ID del voucher

    Returns:
        Dict con información del QR generado:
        {
            'qr_path': str,        # Ruta absoluta a imagen QR
            'token': str,          # Token de seguridad
            'generated_at': str    # Timestamp ISO format
        }

    Raises:
        Exception: Si hay error durante la generación
    """
    qr_path = None

    try:
        logger.info(f"[TASK QR] Iniciando generación para voucher_id={voucher_id}")

        # Obtener servicio
        service = VoucherService(self.db)

        # Obtener voucher
        voucher = service.get_voucher(voucher_id)
        logger.info(f"[TASK QR] Voucher obtenido: folio={voucher.folio}")

        # Verificar si el token está expirado
        if service._is_qr_token_expired(voucher):
            logger.info(f"[TASK QR] Token expirado, regenerando...")
            voucher.qr_token = service._generate_qr_token(voucher_id)
            self.db.commit()
            self.db.refresh(voucher)

        # Generar imagen QR
        logger.info(f"[TASK QR] Generando imagen...")
        qr_gen = QRGenerator(
            output_dir=settings.qr_temp_dir,
            box_size=settings.qr_box_size,
            border=settings.qr_border
        )
        qr_path = qr_gen.generate_qr_image(voucher_id, voucher.qr_token)
        logger.info(f"[TASK QR] QR generado: {qr_path}")

        # Actualizar timestamp
        voucher.qr_image_last_generated_at = datetime.utcnow()
        self.db.commit()

        result = {
            'qr_path': qr_path,
            'token': voucher.qr_token,
            'generated_at': datetime.utcnow().isoformat()
        }

        logger.info(f"[TASK QR] Completado exitosamente para voucher_id={voucher_id}")
        return result

    except Exception as e:
        logger.error(f"[TASK QR] Error generando QR para voucher_id={voucher_id}: {e}", exc_info=True)

        # Limpieza en caso de error
        if qr_path:
            FileManager.delete_file(qr_path)

        # Re-lanzar excepción
        raise


def _generate_pdf_for_voucher(db, voucher_id: int) -> str:
    """
    Genera PDF+QR para un voucher y devuelve la ruta del PDF.
    Función auxiliar reutilizable (no es una tarea Celery).
    """
    service = VoucherService(db)
    voucher = service.get_voucher_with_details(voucher_id)

    if service._is_qr_token_expired(voucher):
        voucher.qr_token = service._generate_qr_token(voucher_id)
        db.commit()
        voucher = service.get_voucher_with_details(voucher_id)

    qr_gen = QRGenerator(
        output_dir=settings.qr_temp_dir,
        box_size=settings.qr_box_size,
        border=settings.qr_border
    )
    qr_path = qr_gen.generate_qr_image(voucher_id, voucher.qr_token)

    pdf_gen = PDFGenerator(
        template_dir=settings.pdf_template_dir,
        temp_dir=settings.pdf_temp_dir
    )
    pdf_path = pdf_gen.generate_voucher_pdf(voucher, qr_path)

    return pdf_path


def _build_optional_rows(voucher) -> tuple:
    """Construye filas HTML opcionales de destino y retorno."""
    destination_row = ""
    if voucher.outer_destination:
        destination_row = f"""
            <div class="info-row">
              <span class="label">Destino</span>
              <span class="value">{voucher.outer_destination}</span>
            </div>"""

    return_row = ""
    if voucher.estimated_return_date:
        return_row = f"""
            <div class="info-row">
              <span class="label">Retorno estimado</span>
              <span class="value">{voucher.estimated_return_date.strftime('%d/%m/%Y')}</span>
            </div>"""

    return destination_row, return_row


@celery_app.task(base=DatabaseTask, bind=True, name='voucher_tasks.send_voucher_email')
def send_voucher_email_task(self, voucher_id: int) -> dict:
    """
    Notifica la creación de un vale nuevo (sin PDF).
    Envía a:
    - El creador del vale
    - Su jefe directo (direct_supervisor)

    Se dispara automáticamente al crear un vale nuevo.
    """
    try:
        logger.info(f"[TASK EMAIL CREATED] Iniciando para voucher_id={voucher_id}")

        from app.shared.email.mailer import get_email_config, send_email_sync
        config = get_email_config(self.db)

        if not config.get("enabled"):
            logger.info(f"[TASK EMAIL CREATED] Email desactivado, omitiendo voucher_id={voucher_id}")
            return {"status": "skipped", "reason": "email_disabled"}

        if not config.get("username") or not config.get("password"):
            logger.warning(f"[TASK EMAIL CREATED] Credenciales SMTP no configuradas, omitiendo")
            return {"status": "skipped", "reason": "smtp_not_configured"}

        voucher = self.db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            return {"status": "error", "reason": "voucher_not_found"}

        # Destinatarios: creador + jefe directo (NO io_manager)
        recipients = []
        creator_individual = self.db.query(Individual).filter(
            Individual.user_id == voucher.created_by,
            Individual.is_deleted == False
        ).first()

        if creator_individual:
            if creator_individual.email:
                recipients.append(creator_individual.email)
            if creator_individual.direct_supervisor and creator_individual.direct_supervisor.email:
                recipients.append(creator_individual.direct_supervisor.email)

        if not recipients:
            logger.warning(f"[TASK EMAIL CREATED] Sin destinatarios para voucher_id={voucher_id}")
            return {"status": "skipped", "reason": "no_recipients"}

        server_ip = getattr(settings, "server_ip", "localhost")
        app_url = f"https://{server_ip}"
        voucher_url = f"{app_url}/my-vouchers/{voucher_id}"

        company_name = voucher.company.company_name if voucher.company else "N/D"
        delivered_by_name = voucher.delivered_by.full_name if voucher.delivered_by else "N/D"
        voucher_type_display = "SALIDA" if voucher.voucher_type.value == "EXIT" else "ENTRADA"
        type_badge = "badge-exit" if voucher.voucher_type.value == "EXIT" else "badge-entry"
        destination_row, return_row = _build_optional_rows(voucher)

        template_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "email", "templates", "voucher_created.html"
        ))

        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                html_body = f.read()
            html_body = (
                html_body
                .replace("{{folio}}", voucher.folio)
                .replace("{{voucher_type}}", voucher_type_display)
                .replace("{{type_badge}}", type_badge)
                .replace("{{company_name}}", company_name)
                .replace("{{delivered_by}}", delivered_by_name)
                .replace("{{destination_row}}", destination_row)
                .replace("{{return_row}}", return_row)
                .replace("{{created_at}}", voucher.created_at.strftime('%d/%m/%Y %H:%M') if voucher.created_at else "")
                .replace("{{voucher_url}}", voucher_url)
                .replace("{{app_url}}", app_url)
            )
        else:
            html_body = (
                f'<div style="font-family:Arial,sans-serif;padding:24px;">'
                f'<h2>Nuevo Vale: {voucher.folio}</h2>'
                f'<p><strong>Tipo:</strong> {voucher_type_display}</p>'
                f'<p><strong>Empresa:</strong> {company_name}</p>'
                f'<p><a href="{voucher_url}">Ver Vale y Aprobar →</a></p>'
                f'</div>'
            )

        unique_recipients = list(set(recipients))
        send_email_sync(
            config=config,
            recipients=unique_recipients,
            subject=f"Nuevo Vale Pendiente: {voucher.folio} — {voucher_type_display}",
            html_body=html_body
        )

        logger.info(f"[TASK EMAIL CREATED] Enviado a {unique_recipients} para {voucher.folio}")
        return {"status": "sent", "folio": voucher.folio, "recipients": unique_recipients}

    except Exception as e:
        logger.error(f"[TASK EMAIL CREATED] Error en voucher_id={voucher_id}: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}


@celery_app.task(base=DatabaseTask, bind=True, name='voucher_tasks.send_voucher_approved_email')
def send_voucher_approved_email_task(self, voucher_id: int) -> dict:
    """
    Notifica la aprobación de un vale, adjuntando el PDF.
    Envía a:
    - El creador del vale
    - El encargado de IO (io_manager)

    Se dispara automáticamente cuando un vale es aprobado.
    """
    pdf_path = None

    try:
        logger.info(f"[TASK EMAIL APPROVED] Iniciando para voucher_id={voucher_id}")

        from app.shared.email.mailer import get_email_config, send_email_sync
        config = get_email_config(self.db)

        if not config.get("enabled"):
            logger.info(f"[TASK EMAIL APPROVED] Email desactivado, omitiendo voucher_id={voucher_id}")
            return {"status": "skipped", "reason": "email_disabled"}

        if not config.get("username") or not config.get("password"):
            logger.warning(f"[TASK EMAIL APPROVED] Credenciales SMTP no configuradas, omitiendo")
            return {"status": "skipped", "reason": "smtp_not_configured"}

        voucher = self.db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            return {"status": "error", "reason": "voucher_not_found"}

        # Destinatarios: creador + io_manager (NO jefe directo)
        recipients = []
        creator_individual = self.db.query(Individual).filter(
            Individual.user_id == voucher.created_by,
            Individual.is_deleted == False
        ).first()

        if creator_individual:
            if creator_individual.email:
                recipients.append(creator_individual.email)
            if creator_individual.io_manager and creator_individual.io_manager.email:
                recipients.append(creator_individual.io_manager.email)

        if not recipients:
            logger.warning(f"[TASK EMAIL APPROVED] Sin destinatarios para voucher_id={voucher_id}")
            return {"status": "skipped", "reason": "no_recipients"}

        # Generar PDF
        try:
            pdf_path = _generate_pdf_for_voucher(self.db, voucher_id)
        except Exception as e:
            logger.error(f"[TASK EMAIL APPROVED] Error generando PDF: {e}")
            return {"status": "error", "reason": f"pdf_failed: {str(e)}"}

        server_ip = getattr(settings, "server_ip", "localhost")
        app_url = f"https://{server_ip}"
        voucher_url = f"{app_url}/my-vouchers/{voucher_id}"

        company_name = voucher.company.company_name if voucher.company else "N/D"
        delivered_by_name = voucher.delivered_by.full_name if voucher.delivered_by else "N/D"
        approved_by_name = voucher.approved_by.full_name if voucher.approved_by else "N/D"
        voucher_type_display = "SALIDA" if voucher.voucher_type.value == "EXIT" else "ENTRADA"
        type_badge = "badge-exit" if voucher.voucher_type.value == "EXIT" else "badge-entry"
        destination_row, return_row = _build_optional_rows(voucher)
        approved_at = voucher.updated_at.strftime('%d/%m/%Y %H:%M') if voucher.updated_at else ""

        template_path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "email", "templates", "voucher_approved.html"
        ))

        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                html_body = f.read()
            html_body = (
                html_body
                .replace("{{folio}}", voucher.folio)
                .replace("{{voucher_type}}", voucher_type_display)
                .replace("{{type_badge}}", type_badge)
                .replace("{{company_name}}", company_name)
                .replace("{{delivered_by}}", delivered_by_name)
                .replace("{{approved_by}}", approved_by_name)
                .replace("{{destination_row}}", destination_row)
                .replace("{{return_row}}", return_row)
                .replace("{{approved_at}}", approved_at)
                .replace("{{voucher_url}}", voucher_url)
                .replace("{{app_url}}", app_url)
            )
        else:
            html_body = (
                f'<div style="font-family:Arial,sans-serif;padding:24px;">'
                f'<h2>✅ Vale Aprobado: {voucher.folio}</h2>'
                f'<p><strong>Tipo:</strong> {voucher_type_display}</p>'
                f'<p><strong>Empresa:</strong> {company_name}</p>'
                f'<p><strong>Aprobado por:</strong> {approved_by_name}</p>'
                f'<p>Se adjunta el PDF. Por favor imprímalo y recabe las firmas.</p>'
                f'<p><a href="{voucher_url}">Ver Vale en el Sistema →</a></p>'
                f'</div>'
            )

        unique_recipients = list(set(recipients))
        send_email_sync(
            config=config,
            recipients=unique_recipients,
            subject=f"Vale Aprobado: {voucher.folio} — {voucher_type_display}",
            html_body=html_body,
            attachment_path=pdf_path,
            attachment_name=f"{voucher.folio}.pdf"
        )

        logger.info(f"[TASK EMAIL APPROVED] Enviado a {unique_recipients} para {voucher.folio}")
        return {"status": "sent", "folio": voucher.folio, "recipients": unique_recipients}

    except Exception as e:
        logger.error(f"[TASK EMAIL APPROVED] Error en voucher_id={voucher_id}: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}
    finally:
        if pdf_path and os.path.exists(pdf_path):
            try:
                FileManager.delete_file(pdf_path)
            except Exception:
                pass
