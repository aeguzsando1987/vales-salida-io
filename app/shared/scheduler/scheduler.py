"""
Scheduler Module - Sistema de Tareas Programadas

¿Qué es un Scheduler?
---------------------
Un scheduler (programador de tareas) es un sistema que ejecuta funciones automáticamente
en horarios específicos, sin necesidad de intervención manual. Es como un "reloj despertador"
para tu aplicación que dice "ejecuta esta tarea todos los días a las 00:00".

¿Qué es un Job?
---------------
Un Job (trabajo/tarea) es una función específica que el scheduler ejecuta. En este caso,
nuestro job es "revisar vales vencidos y marcarlos como OVERDUE". El job puede ejecutarse:
- En horarios específicos (todos los días a las 00:00)
- Con intervalos (cada 6 horas)
- Con cron expressions (más flexibilidad)

¿Por qué usar APScheduler?
---------------------------
APScheduler (Advanced Python Scheduler) es una librería que permite:
1. Ejecutar tareas en background (sin bloquear la aplicación)
2. Configurar horarios flexibles (diario, semanal, mensual, etc.)
3. Gestionar múltiples jobs simultáneamente
4. Persistir jobs entre reinicios (opcional)

En este proyecto:
- BackgroundScheduler: Ejecuta jobs en un thread separado (no bloquea FastAPI)
- CronTrigger: Define horarios específicos (hora y minuto en UTC)
- Job ID: Identificador único para cada tarea ('check_overdue_vouchers')
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Crear instancia global del scheduler
# BackgroundScheduler ejecuta jobs en un thread separado (no bloquea el servidor)
scheduler = BackgroundScheduler()

# Logger para registrar eventos del scheduler
logger = logging.getLogger(__name__)

def start_scheduler():
    """
    Inicia el scheduler con todos los jobs configurados.

    Esta función se llama una vez al iniciar la aplicación (main.py startup event).

    Flujo:
    1. Importa configuración (settings) y el job a ejecutar
    2. Registra el job con un CronTrigger (horario específico)
    3. Inicia el scheduler (comienza a ejecutar jobs)
    4. Registra en logs que el scheduler está activo

    CronTrigger Params:
    - hour: Hora del día (0-23) en UTC
    - minute: Minuto (0-59)
    - timezone: Zona horaria ('UTC' recomendado para servidores)

    Ejemplo:
    Si settings.scheduler_overdue_hour = 0 y minute = 0
    → El job se ejecuta todos los días a las 00:00 UTC (medianoche)
    """
    # Importar settings (configuración de horario)
    from app.config.settings import settings

    # Importar el job (función) que se ejecutará
    from .jobs import check_overdue_vouchers_job

    # Registrar el job en el scheduler
    scheduler.add_job(
        check_overdue_vouchers_job,  # Función a ejecutar
        trigger=CronTrigger(          # Trigger: CUÁNDO ejecutar
            hour=settings.scheduler_overdue_hour,    # Hora (0-23 UTC)
            minute=settings.scheduler_overdue_minute, # Minuto (0-59)
            timezone='UTC'                           # Zona horaria
        ),
        id='check_overdue_vouchers',  # ID único del job (para logs y gestión)
        replace_existing=True         # Si ya existe un job con este ID, reemplazarlo
    )

    # Iniciar el scheduler (comienza a ejecutar jobs según sus triggers)
    scheduler.start()

    # Log de confirmación
    logger.info(
        f"✓ Scheduler iniciado - Check overdue: "
        f"{settings.scheduler_overdue_hour}:{settings.scheduler_overdue_minute:02d} UTC"
    )

def stop_scheduler():
    """
    Detiene el scheduler limpiamente.

    Esta función se llama al cerrar la aplicación (main.py shutdown event).

    Flujo:
    1. Verifica si el scheduler está corriendo
    2. Si está corriendo, lo detiene (shutdown)
    3. Registra en logs que el scheduler se detuvo

    Params de shutdown:
    - wait=False: No espera a que terminen los jobs en ejecución
      (Para desarrollo; en producción podría ser wait=True)
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)  # Detener scheduler
        logger.info("✓ Scheduler detenido")
