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
            self.db.refresh(voucher)

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
