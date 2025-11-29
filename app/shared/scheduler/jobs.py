from database import SessionLocal
from app.entities.vouchers.services.voucher_service import VoucherService
import logging

logger = logging.getLogger(__name__)

def check_overdue_vouchers_job():
    """
    Job automático que marca vouchers vencidos.

    Se ejecuta diariamente según configuración.
    Busca vales con status=IN_TRANSIT, with_return=True,
    y estimated_return_date vencida.
    """
    db = SessionLocal()
    try:
        service = VoucherService(db)
        count = service.check_and_mark_overdue(system_user_id=1)

        if count > 0:
            logger.warning(f"[SCHEDULER] {count} vouchers marcados como OVERDUE")
        else:
            logger.info("[SCHEDULER] No hay vouchers vencidos")

    except Exception as e:
        logger.error(f"[SCHEDULER ERROR] {str(e)}", exc_info=True)
    finally:
        db.close()
