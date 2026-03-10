"""
VoucherService - Lógica de negocio para Vouchers

Responsabilidades:
- Generación de folios únicos
- Generación de tokens QR
- Transiciones de estado
- Validaciones de negocio
- Detección de vales vencidos
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, date
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

from app.entities.vouchers.models.voucher import Voucher, VoucherStatusEnum, VoucherTypeEnum
from app.entities.vouchers.models.entry_log import EntryLog, EntryStatusEnum
from app.entities.vouchers.models.out_log import OutLog, ValidationStatusEnum
from app.entities.vouchers.schemas.voucher_schemas import (
    VoucherCreate,
    VoucherUpdate,
    VoucherApprove,
    VoucherCancel
)
from app.entities.vouchers.repositories.voucher_repository import VoucherRepository
from app.entities.companies.models.company import Company
from app.entities.branches.models.branch import Branch
from app.entities.individuals.models.individual import Individual
from database import User

from app.shared.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    BusinessRuleError
)


class VoucherService:
    """
    Servicio de Vouchers con lógica de negocio completa
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = VoucherRepository(db)

    # ==================== HELPERS DE SCOPING MULTI-EMPRESA ====================

    def _get_user_company_ids(self, user_id: int, role: int) -> List[int]:
        """
        Obtiene los IDs de empresas a las que el usuario tiene acceso.

        Args:
            user_id: ID del usuario
            role: Rol del usuario (1-6)

        Returns:
            Lista de company_ids accesibles. Admin (role=1) retorna lista vacía (acceso total).
        """
        # Admin tiene acceso a todas las empresas
        if role == 1:
            return []  # Lista vacía = acceso sin restricción

        # Buscar Individual del usuario
        individual = self.db.query(Individual).filter(
            Individual.user_id == user_id,
            Individual.is_deleted == False
        ).first()

        if not individual:
            # Si no tiene Individual, no tiene acceso a empresas
            return []

        # Retornar accessible_company_ids (propiedad computada)
        return individual.accessible_company_ids

    def _validate_company_access(self, user_id: int, role: int, company_id: int) -> None:
        """
        Valida si el usuario tiene acceso a la empresa especificada.

        Args:
            user_id: ID del usuario
            role: Rol del usuario
            company_id: ID de la empresa a validar

        Raises:
            BusinessRuleError: Si el usuario no tiene acceso a la empresa
        """
        # Admin y Checker tienen acceso a cualquier empresa
        if role in [1, 6]:
            return

        accessible_ids = self._get_user_company_ids(user_id, role)

        # Si accessible_ids está vacío y no es Admin/Checker, no tiene acceso
        if not accessible_ids:
            raise BusinessRuleError(
                f"Usuario no tiene empresas asignadas. Contacte al administrador."
            )

        # Validar que la empresa esté en la lista de accesibles
        if company_id not in accessible_ids:
            raise BusinessRuleError(
                f"No tiene permiso para operar vouchers de la empresa ID {company_id}"
            )

    # ==================== GENERACIÓN DE FOLIOS ====================

    def _generate_folio(
        self,
        company_id: int,
        voucher_type: VoucherTypeEnum
    ) -> str:
        """
        Genera folio único: {company_id}-{type}-{YYYYMMDDHHmmss}-{seq:02d}

        Formato con timestamp completo para garantizar unicidad absoluta.
        Incluye secuencia corta (01-99) para manejar concurrencia en el mismo segundo.

        Ejemplos:
            2-SAL-20260119171530-01  (EXIT, empresa 2)
            3-ENT-20260119171532-01  (ENTRY, empresa 3)
            2-SAL-20260119171530-02  (EXIT, empresa 2, segundo vale en mismo segundo)

        Args:
            company_id: ID de la empresa
            voucher_type: ENTRY o EXIT

        Returns:
            Folio único generado
        """
        # Tipo de voucher
        type_code = "ENT" if voucher_type == VoucherTypeEnum.ENTRY else "SAL"

        # Obtener timestamp actual completo: YYYYMMDDHHmmss
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M%S')

        # Obtener última secuencia para este timestamp exacto
        last_seq = self.repository.get_last_sequence_for_timestamp(
            company_id=company_id,
            voucher_type=voucher_type,
            timestamp=timestamp
        )
        next_seq = last_seq + 1

        # Formatear folio: 2-SAL-20260119171530-01
        folio = f"{company_id}-{type_code}-{timestamp}-{next_seq:02d}"

        return folio

    # ==================== GENERACIÓN DE QR ====================

    def _generate_qr_token(self, voucher_id: int) -> str:
        """
        Genera token seguro para código QR

        Args:
            voucher_id: ID del voucher

        Returns:
            Token hash SHA-256
        """
        today = datetime.now().date().isoformat()
        secret_key = os.getenv("SECRET_KEY", "tu-clave-secreta-aqui")
        raw = f"{voucher_id}:{secret_key}:{today}"
        token = hashlib.sha256(raw.encode()).hexdigest()
        return token

    def validate_qr_token(self, voucher_id: int, qr_data: str) -> bool:
        """
        Valida que el voucher existe y está en estado apropiado para validación.

        El QR solo sirve para identificar el voucher rápidamente (como un ID visual).
        La validación real de seguridad NO es necesaria - el checker valida visualmente
        el material físico y luego usa validate-exit para cambiar el estado.

        Args:
            voucher_id: ID del voucher
            qr_data: Contenido del QR (no se usa, solo para compatibilidad)

        Returns:
            True si el voucher existe y está en estado válido para checking
        """
        # Verificar que el voucher existe
        voucher = self.get_voucher(voucher_id)

        # El voucher es "válido" para checking si está en estado APPROVED
        # (listo para salir) o IN_TRANSIT (esperando confirmación de entrada)
        valid_states = [VoucherStatusEnum.APPROVED, VoucherStatusEnum.IN_TRANSIT]

        return voucher.status in valid_states

    # ==================== LOG CREATION (PRIVATE METHODS) ====================

    def _create_entry_log(
        self,
        voucher: Voucher,
        entry_status: EntryStatusEnum,
        received_by_id: int,
        missing_items_description: Optional[str],
        notes: Optional[str],
        created_by_user_id: int
    ) -> EntryLog:
        """
        Crea un entry_log para el voucher (método privado)

        Args:
            voucher: Voucher al que pertenece
            entry_status: COMPLETE, INCOMPLETE o DAMAGED
            received_by_id: ID de quien recibe
            missing_items_description: Descripción de faltantes (obligatorio si INCOMPLETE/DAMAGED)
            notes: Observaciones
            created_by_user_id: Usuario que registra

        Returns:
            EntryLog creado

        Raises:
            EntityValidationError: Si ya existe entry_log o validaciones fallan
        """
        # Validar que no exista entry_log previo
        existing_log = self.db.query(EntryLog).filter(
            EntryLog.voucher_id == voucher.id
        ).first()

        if existing_log:
            raise EntityValidationError(
                "EntryLog",
                {"voucher_id": f"Ya existe un entry_log para el voucher {voucher.folio}"}
            )

        # Validar received_by existe
        receiver = self.db.query(Individual).filter(
            Individual.id == received_by_id
        ).first()
        if not receiver:
            raise EntityNotFoundError("Individual", received_by_id)

        # Validar missing_items_description si status != COMPLETE
        if entry_status in [EntryStatusEnum.INCOMPLETE, EntryStatusEnum.DAMAGED]:
            if not missing_items_description or len(missing_items_description.strip()) == 0:
                raise EntityValidationError(
                    "EntryLog",
                    {"missing_items_description": "Obligatorio cuando entry_status es INCOMPLETE o DAMAGED"}
                )

        # Crear entry_log
        entry_log = EntryLog(
            voucher_id=voucher.id,
            entry_status=entry_status,
            received_by_id=received_by_id,
            missing_items_description=missing_items_description,
            notes=notes,
            created_by=created_by_user_id,
            created_at=datetime.utcnow()
        )

        self.db.add(entry_log)
        return entry_log

    def _create_out_log(
        self,
        voucher: Voucher,
        validation_status: ValidationStatusEnum,
        scanned_by_id: int,
        observations: Optional[str],
        created_by_user_id: int
    ) -> OutLog:
        """
        Crea un out_log para el voucher (método privado)

        Args:
            voucher: Voucher al que pertenece
            validation_status: APPROVED, REJECTED o OBSERVATION
            scanned_by_id: ID del vigilante que escanea
            observations: Observaciones de inspección visual
            created_by_user_id: Usuario que registra

        Returns:
            OutLog creado

        Raises:
            EntityValidationError: Si ya existe out_log
        """
        # Validar que no exista out_log previo
        existing_log = self.db.query(OutLog).filter(
            OutLog.voucher_id == voucher.id
        ).first()

        if existing_log:
            raise EntityValidationError(
                "OutLog",
                {"voucher_id": f"Ya existe un out_log para el voucher {voucher.folio}"}
            )

        # Validar scanned_by existe
        guard = self.db.query(Individual).filter(
            Individual.id == scanned_by_id
        ).first()
        if not guard:
            raise EntityNotFoundError("Individual", scanned_by_id)

        # Crear out_log
        out_log = OutLog(
            voucher_id=voucher.id,
            validation_status=validation_status,
            scanned_by_id=scanned_by_id,
            observations=observations,
            created_by=created_by_user_id,
            created_at=datetime.utcnow()
        )

        self.db.add(out_log)
        return out_log

    # ==================== LOG OPERATIONS (PUBLIC METHODS) ====================

    def confirm_entry_voucher(
        self,
        voucher_id: int,
        received_by_id: int,
        line_validations: List[dict],
        general_observations: Optional[str] = None,
        confirming_user_id: int = 1,
        role: int = 1
    ) -> Voucher:
        """
        Confirma recepcion fisica de material LINEA POR LINEA (logica ESTRICTA)

        IMPORTANTE: Vale solo cierra si TODAS las lineas tienen ok_entry=true.
        El gerente/supervisor valida cada linea individualmente.

        Flujos:
        - ENTRY: PENDING → (valida lineas + crea entry_log) → CLOSED/INCOMPLETE_DAMAGED
        - EXIT con retorno: IN_TRANSIT → (valida lineas + crea entry_log) → CLOSED/INCOMPLETE_DAMAGED
        - EXIT intercompania: IN_TRANSIT → (valida lineas + crea entry_log) → CLOSED/INCOMPLETE_DAMAGED

        Logica de negocio:
        - Si TODAS las lineas ok=true → voucher.status=CLOSED
        - Si ALGUNA linea ok=false → voucher.status=INCOMPLETE_DAMAGED
        - Material incompleto/dañado NO cierra el vale

        Args:
            voucher_id: ID del voucher
            received_by_id: ID de quien recibe
            line_validations: Lista de validaciones [{"detail_id": 1, "ok": true, "notes": "..."}]
            general_observations: Observaciones generales
            confirming_user_id: Usuario que confirma
            role: Rol del usuario (1-6)

        Returns:
            Voucher actualizado con validaciones linea por linea

        Raises:
            EntityNotFoundError: Si voucher o detalles no existen
            BusinessRuleError: Si estado no permite confirmar entrada
            EntityValidationError: Si validaciones son invalidas
        """
        from app.entities.voucher_details.models.voucher_detail import VoucherDetail

        voucher = self.get_voucher(voucher_id, include_details=True)

        # Validar acceso a la empresa (scoping multi-empresa)
        self._validate_company_access(confirming_user_id, role, voucher.company_id)

        # Validar estados validos
        valid_statuses = [
            VoucherStatusEnum.PENDING,      # ENTRY puro
            VoucherStatusEnum.IN_TRANSIT,   # EXIT con retorno
            VoucherStatusEnum.APPROVED      # Casos especiales
        ]

        if voucher.status not in valid_statuses:
            raise BusinessRuleError(
                f"No se puede confirmar entrada desde estado {voucher.status.value}. "
                f"Estados validos: {[s.value for s in valid_statuses]}"
            )

        # Validar que haya detalles
        if not voucher.details:
            raise EntityValidationError(
                "Voucher",
                {"details": "El voucher no tiene lineas de detalle"}
            )

        # Validar que se proporcionen validaciones para todas las lineas
        detail_ids = {d.id for d in voucher.details}
        validation_ids = {v["detail_id"] for v in line_validations}

        if detail_ids != validation_ids:
            missing = detail_ids - validation_ids
            extra = validation_ids - detail_ids
            raise EntityValidationError(
                "LineValidation",
                {
                    "detail_ids": f"Faltan validaciones para: {missing}. Validaciones extras: {extra}"
                }
            )

        # Actualizar ok_entry en cada detalle
        all_ok = True
        for validation in line_validations:
            detail = self.db.query(VoucherDetail).filter(
                VoucherDetail.id == validation["detail_id"]
            ).first()

            if not detail:
                raise EntityNotFoundError("VoucherDetail", validation["detail_id"])

            detail.ok_entry = validation["ok"]
            detail.ok_entry_notes = validation.get("notes")

            if not validation["ok"]:
                all_ok = False

        # Determinar entry_status del entry_log
        if all_ok:
            entry_status = EntryStatusEnum.COMPLETE
        else:
            # Determinar si es INCOMPLETE o DAMAGED segun observaciones
            # Por defecto usamos INCOMPLETE si hay problemas
            entry_status = EntryStatusEnum.INCOMPLETE

        # Crear entry_log con descripcion de faltantes
        missing_items_description = None
        if not all_ok:
            problems_list = [
                f"Linea {v['detail_id']}: {v.get('notes', 'Sin especificar')}"
                for v in line_validations if not v["ok"]
            ]
            missing_items_description = "\n".join(problems_list)

        combined_notes = general_observations or ""
        if not all_ok and missing_items_description:
            combined_notes += f"\n\nProblemas detectados:\n{missing_items_description}"

        self._create_entry_log(
            voucher=voucher,
            entry_status=entry_status,
            received_by_id=received_by_id,
            missing_items_description=missing_items_description,
            notes=combined_notes.strip() or None,
            created_by_user_id=confirming_user_id
        )

        # Actualizar voucher.received_by_id (firma digital)
        voucher.received_by_id = received_by_id

        # Actualizar fecha de retorno si aplica
        if voucher.with_return:
            voucher.actual_return_date = date.today()

        # Transicion de estado: ESTRICTO segun validaciones de lineas
        if all_ok:
            voucher.status = VoucherStatusEnum.CLOSED
        else:
            voucher.status = VoucherStatusEnum.INCOMPLETE_DAMAGED

        # Auditoria
        voucher.updated_by = confirming_user_id
        voucher.updated_at = datetime.utcnow()

        # Commit atomico
        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    def validate_exit_voucher(
        self,
        voucher_id: int,
        scanned_by_id: int,
        line_validations: List[dict],
        general_observations: Optional[str] = None,
        validating_user_id: int = 1,
        role: int = 1
    ) -> Voucher:
        """
        Valida salida de material LINEA POR LINEA (logica FLEXIBLE)

        IMPORTANTE: Material SIEMPRE sale, incluso si hay observaciones.
        El checker valida cada linea individualmente (ok_exit true/false).

        Flujos:
        - EXIT sin retorno: APPROVED → (valida lineas + crea out_log) → CLOSED
        - EXIT con retorno: APPROVED → (valida lineas + crea out_log) → IN_TRANSIT
        - EXIT intercompania: APPROVED → (valida lineas + crea out_log) → IN_TRANSIT

        Logica de negocio:
        - Si TODAS las lineas ok=true → Material sale OK
        - Si ALGUNA linea ok=false → Material sale IGUAL, con observaciones registradas
        - NUNCA se bloquea la salida del material

        Args:
            voucher_id: ID del voucher
            scanned_by_id: ID del vigilante
            line_validations: Lista de validaciones [{"detail_id": 1, "ok": true, "notes": "..."}]
            general_observations: Observaciones generales
            validating_user_id: Usuario que valida
            role: Rol del usuario (1-6)

        Returns:
            Voucher actualizado con validaciones linea por linea

        Raises:
            EntityNotFoundError: Si voucher o detalles no existen
            BusinessRuleError: Si estado no permite validar salida
            EntityValidationError: Si validaciones son invalidas
        """
        from app.entities.voucher_details.models.voucher_detail import VoucherDetail

        voucher = self.get_voucher(voucher_id, include_details=True)

        # Validar acceso a la empresa (scoping multi-empresa)
        self._validate_company_access(validating_user_id, role, voucher.company_id)

        # Validar estado
        if voucher.status != VoucherStatusEnum.APPROVED:
            raise BusinessRuleError(
                f"Solo vouchers APPROVED pueden validar salida. Estado actual: {voucher.status.value}"
            )

        # Validar que haya detalles
        if not voucher.details:
            raise EntityValidationError(
                "Voucher",
                {"details": "El voucher no tiene lineas de detalle"}
            )

        # Validar que se proporcionen validaciones para todas las lineas
        detail_ids = {d.id for d in voucher.details}
        validation_ids = {v["detail_id"] for v in line_validations}

        if detail_ids != validation_ids:
            missing = detail_ids - validation_ids
            extra = validation_ids - detail_ids
            raise EntityValidationError(
                "LineValidation",
                {
                    "detail_ids": f"Faltan validaciones para: {missing}. Validaciones extras: {extra}"
                }
            )

        # Actualizar ok_exit en cada detalle
        has_problems = False
        for validation in line_validations:
            detail = self.db.query(VoucherDetail).filter(
                VoucherDetail.id == validation["detail_id"]
            ).first()

            if not detail:
                raise EntityNotFoundError("VoucherDetail", validation["detail_id"])

            detail.ok_exit = validation["ok"]
            detail.ok_exit_notes = validation.get("notes")

            if not validation["ok"]:
                has_problems = True

        # Determinar validation_status del out_log
        if has_problems:
            validation_status = ValidationStatusEnum.OBSERVATION
        else:
            validation_status = ValidationStatusEnum.APPROVED

        # Crear out_log con observaciones
        combined_observations = general_observations or ""
        if has_problems:
            problems_list = [
                f"Linea {v['detail_id']}: {v.get('notes', 'Sin especificar')}"
                for v in line_validations if not v["ok"]
            ]
            combined_observations += "\n\nProblemas detectados:\n" + "\n".join(problems_list)

        self._create_out_log(
            voucher=voucher,
            validation_status=validation_status,
            scanned_by_id=scanned_by_id,
            observations=combined_observations.strip() or None,
            created_by_user_id=validating_user_id
        )

        # Transicion de estado: Material SIEMPRE sale
        if voucher.with_return or voucher.is_intercompany:
            voucher.status = VoucherStatusEnum.IN_TRANSIT
        else:
            voucher.status = VoucherStatusEnum.CLOSED

        # Auditoria
        voucher.updated_by = validating_user_id
        voucher.updated_at = datetime.utcnow()

        # Commit atomico
        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    def get_voucher_logs(self, voucher_id: int) -> dict:
        """
        Obtiene los logs de auditoría de un voucher

        Returns:
            Dict con entry_log y out_log (None si no existen)
        """
        voucher = self.get_voucher(voucher_id)

        entry_log = self.db.query(EntryLog).filter(
            EntryLog.voucher_id == voucher.id
        ).first()

        out_log = self.db.query(OutLog).filter(
            OutLog.voucher_id == voucher.id
        ).first()

        return {
            "voucher_id": voucher.id,
            "folio": voucher.folio,
            "entry_log": entry_log,
            "out_log": out_log
        }

    # ==================== CRUD OPERATIONS ====================

    def create_voucher(
        self,
        voucher_data: VoucherCreate,
        created_by_user_id: int,
        role: int
    ) -> Voucher:
        """
        Crea un voucher nuevo

        Estado inicial: PENDING
        Genera automáticamente:
        - Folio único
        - Token QR

        Args:
            voucher_data: Datos del voucher
            created_by_user_id: Usuario que crea
            role: Rol del usuario (1-6)

        Returns:
            Voucher creado
        """
        # Validar empresa existe
        company = self.db.query(Company).filter(
            Company.id == voucher_data.company_id
        ).first()
        if not company:
            raise EntityNotFoundError("Company", voucher_data.company_id)

        # Validar acceso a la empresa (scoping multi-empresa)
        self._validate_company_access(created_by_user_id, role, voucher_data.company_id)

        # Validar origin_branch si existe
        if voucher_data.origin_branch_id:
            origin_branch = self.db.query(Branch).filter(
                Branch.id == voucher_data.origin_branch_id
            ).first()
            if not origin_branch:
                raise EntityNotFoundError("Branch", voucher_data.origin_branch_id)

        # Validar destination_branch si existe
        if voucher_data.destination_branch_id:
            dest_branch = self.db.query(Branch).filter(
                Branch.id == voucher_data.destination_branch_id
            ).first()
            if not dest_branch:
                raise EntityNotFoundError("Branch", voucher_data.destination_branch_id)

        # Validar delivered_by existe
        delivered_by = self.db.query(Individual).filter(
            Individual.id == voucher_data.delivered_by_id
        ).first()
        if not delivered_by:
            raise EntityNotFoundError("Individual", voucher_data.delivered_by_id)

        # Validar fecha de retorno si es con retorno
        if voucher_data.with_return:
            if not voucher_data.estimated_return_date:
                raise EntityValidationError(
                    "Voucher",
                    {"estimated_return_date": "Requerido si with_return=True"}
                )
            if voucher_data.estimated_return_date < date.today():
                raise EntityValidationError(
                    "Voucher",
                    {"estimated_return_date": "Debe ser fecha futura"}
                )

        # Generar folio único
        folio = self._generate_folio(
            company_id=voucher_data.company_id,
            voucher_type=voucher_data.voucher_type
        )

        # Crear voucher
        new_voucher = Voucher(
            folio=folio,
            voucher_type=voucher_data.voucher_type,
            status=VoucherStatusEnum.PENDING,  # Estado inicial
            company_id=voucher_data.company_id,
            origin_branch_id=voucher_data.origin_branch_id,
            destination_branch_id=voucher_data.destination_branch_id,
            outer_destination=voucher_data.outer_destination,
            delivered_by_id=voucher_data.delivered_by_id,
            with_return=voucher_data.with_return,
            is_intercompany=voucher_data.is_intercompany,
            estimated_return_date=voucher_data.estimated_return_date,
            notes=voucher_data.notes,
            internal_notes=voucher_data.internal_notes,
            is_active=True,
            is_deleted=False,
            created_by=created_by_user_id
        )

        self.db.add(new_voucher)
        self.db.commit()
        self.db.refresh(new_voucher)

        # Generar token QR
        qr_token = self._generate_qr_token(new_voucher.id)
        new_voucher.qr_token = qr_token
        self.db.commit()
        self.db.refresh(new_voucher)

        # Enviar correo en background (no bloquea la respuesta al usuario)
        try:
            from app.shared.tasks.voucher_tasks import send_voucher_email_task
            send_voucher_email_task.delay(new_voucher.id)
        except Exception as e:
            # El error de email no debe bloquear la creación del vale
            import logging
            logging.getLogger(__name__).warning(f"[VOUCHER] No se pudo encolar email task: {e}")

        return new_voucher

    def get_voucher(self, voucher_id: int, include_details: bool = False) -> Voucher:
        """
        Obtiene un voucher por ID

        Args:
            voucher_id: ID del voucher
            include_details: Si True, carga las líneas de detalle en voucher.details

        Returns:
            Voucher encontrado (con details cargados si include_details=True)

        Raises:
            EntityNotFoundError: Si no existe
        """
        voucher = self.repository.get_by_id(voucher_id)
        if not voucher:
            raise EntityNotFoundError("Voucher", voucher_id)

        # Si include_details=True, cargar las líneas explícitamente
        if include_details:
            # Forzar carga de la relación details (lazy loading)
            # SQLAlchemy automáticamente carga la relación cuando se accede
            _ = voucher.details

        return voucher

    def get_voucher_by_folio(self, folio: str) -> Voucher:
        """
        Obtiene un voucher por folio

        Args:
            folio: Folio del voucher

        Returns:
            Voucher encontrado

        Raises:
            EntityNotFoundError: Si no existe
        """
        voucher = self.repository.find_by_folio(folio)
        if not voucher:
            raise EntityNotFoundError("Voucher", f"folio={folio}")
        return voucher

    def update_voucher(
        self,
        voucher_id: int,
        voucher_data: VoucherUpdate,
        updated_by_user_id: int
    ) -> Voucher:
        """
        Actualiza un voucher

        Solo se permite actualizar vouchers en estado PENDING

        Args:
            voucher_id: ID del voucher
            voucher_data: Datos a actualizar
            updated_by_user_id: Usuario que actualiza

        Returns:
            Voucher actualizado

        Raises:
            BusinessRuleError: Si no está en PENDING
        """
        voucher = self.get_voucher(voucher_id)

        # Solo se puede actualizar si está PENDING
        if voucher.status != VoucherStatusEnum.PENDING:
            raise BusinessRuleError(
                f"No se puede actualizar un voucher en estado {voucher.status.value}"
            )

        # Actualizar campos
        update_data = voucher_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(voucher, field, value)

        voucher.updated_by = updated_by_user_id
        voucher.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    def list_vouchers(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        status: Optional[VoucherStatusEnum] = None,
        voucher_type: Optional[VoucherTypeEnum] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = "desc",
        current_user_id: Optional[int] = None,
        current_user_role: Optional[int] = None
    ) -> List[Voucher]:
        """
        Lista todos los vouchers con filtros y ordenamiento.

        - Admin/Manager/Supervisor (roles 1,2,3): ven todos los vales
        - Reader (role 4): solo ve sus propios vales (created_by)

        Args:
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos
            status: Filtrar por estado
            voucher_type: Filtrar por tipo
            order_by: Campo para ordenar
            order_direction: Dirección de ordenamiento
            current_user_id: ID del usuario actual
            current_user_role: Rol del usuario actual

        Returns:
            Lista de vouchers
        """
        # Construir query base
        query = self.db.query(Voucher).filter(Voucher.is_deleted == False)

        # Aplicar filtros comunes
        if active_only:
            query = query.filter(Voucher.is_active == True)

        if status:
            query = query.filter(Voucher.status == status)

        if voucher_type:
            query = query.filter(Voucher.voucher_type == voucher_type)

        # Scoping multi-empresa y filtro por rol
        if current_user_role is not None and current_user_id is not None:
            if current_user_role == 4:
                # Reader: solo sus propios vales
                query = query.filter(Voucher.created_by == current_user_id)
            elif current_user_role not in [1, 6]:
                # Roles 2,3,5: filtrar por empresas accesibles
                accessible_ids = self._get_user_company_ids(current_user_id, current_user_role)
                if accessible_ids:
                    query = query.filter(Voucher.company_id.in_(accessible_ids))
                else:
                    # Sin empresas asignadas → no ver nada
                    return []

        # Aplicar ordenamiento
        if order_by:
            if order_by == 'folio':
                order_field = Voucher.folio
            elif order_by == 'created_at':
                order_field = Voucher.created_at
            else:
                order_field = Voucher.created_at  # Default

            if order_direction == 'asc':
                query = query.order_by(order_field.asc())
            else:
                query = query.order_by(order_field.desc())
        else:
            # Ordenamiento por defecto: fecha de creación descendente
            query = query.order_by(Voucher.created_at.desc())

        # Aplicar paginación
        return query.offset(skip).limit(limit).all()

    def count_vouchers(
        self,
        active_only: bool = True,
        status: Optional[VoucherStatusEnum] = None,
        voucher_type: Optional[VoucherTypeEnum] = None,
        current_user_id: Optional[int] = None,
        current_user_role: Optional[int] = None
    ) -> int:
        """
        Cuenta total de vouchers con filtros.

        Args:
            active_only: Solo activos
            status: Filtrar por estado
            voucher_type: Filtrar por tipo
            current_user_id: ID del usuario actual
            current_user_role: Rol del usuario actual

        Returns:
            Total de registros
        """
        # Construir query base
        query = self.db.query(Voucher).filter(Voucher.is_deleted == False)

        # Aplicar filtros comunes
        if active_only:
            query = query.filter(Voucher.is_active == True)

        if status:
            query = query.filter(Voucher.status == status)

        if voucher_type:
            query = query.filter(Voucher.voucher_type == voucher_type)

        # Scoping multi-empresa y filtro por rol
        if current_user_role is not None and current_user_id is not None:
            if current_user_role == 4:
                query = query.filter(Voucher.created_by == current_user_id)
            elif current_user_role not in [1, 6]:
                accessible_ids = self._get_user_company_ids(current_user_id, current_user_role)
                if accessible_ids:
                    query = query.filter(Voucher.company_id.in_(accessible_ids))
                else:
                    return 0

        return query.count()

    # ==================== TRANSICIONES DE ESTADO ====================

    def approve_voucher(
        self,
        voucher_id: int,
        approve_data: VoucherApprove,
        approved_by_user_id: int,
        role: int
    ) -> Voucher:
        """
        Aprueba un voucher: PENDING → APPROVED

        Args:
            voucher_id: ID del voucher
            approve_data: Datos de aprobación
            approved_by_user_id: Usuario que aprueba
            role: Rol del usuario (1-6)

        Returns:
            Voucher aprobado

        Raises:
            BusinessRuleError: Si no está en PENDING
        """
        voucher = self.get_voucher(voucher_id)

        # Validar acceso a la empresa (scoping multi-empresa)
        self._validate_company_access(approved_by_user_id, role, voucher.company_id)

        # Validar estado
        if voucher.status != VoucherStatusEnum.PENDING:
            raise BusinessRuleError(
                f"Solo se pueden aprobar vouchers en estado PENDING. Estado actual: {voucher.status.value}"
            )

        # Validar aprobador existe (solo si se proporciona)
        if approve_data.approved_by_id:
            approver = self.db.query(Individual).filter(
                Individual.id == approve_data.approved_by_id
            ).first()
            if not approver:
                raise EntityNotFoundError("Individual", approve_data.approved_by_id)
            voucher.approved_by_id = approve_data.approved_by_id
        else:
            # Si no se proporciona, queda como NULL
            voucher.approved_by_id = None

        # Cambiar estado
        voucher.status = VoucherStatusEnum.APPROVED

        # Agregar notas si existen
        if approve_data.notes:
            if voucher.internal_notes:
                voucher.internal_notes += f"\n[APROBACIÓN] {approve_data.notes}"
            else:
                voucher.internal_notes = f"[APROBACIÓN] {approve_data.notes}"

        voucher.updated_by = approved_by_user_id
        voucher.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(voucher)

        # Enviar correo de aprobación en background (con PDF)
        try:
            from app.shared.tasks.voucher_tasks import send_voucher_approved_email_task
            send_voucher_approved_email_task.delay(voucher_id)
        except Exception as e:
            logger.warning(f"[VOUCHER SERVICE] No se pudo encolar tarea de email aprobación: {e}")

        return voucher

    def close_voucher(
        self,
        voucher_id: int,
        closed_by_user_id: int,
        received_by_id: Optional[int] = None
    ) -> Voucher:
        """
        Cierra un voucher: → CLOSED

        Casos de uso:
        - EXIT sin retorno: APPROVED → CLOSED (al escanear)
        - EXIT con retorno: IN_TRANSIT → CLOSED (al registrar entry_log COMPLETE)
        - ENTRY: PENDING → CLOSED (al registrar entry_log COMPLETE)

        Args:
            voucher_id: ID del voucher
            closed_by_user_id: Usuario que cierra
            received_by_id: ID de quien recibe (opcional)

        Returns:
            Voucher cerrado
        """
        voucher = self.get_voucher(voucher_id)

        # Estados válidos para cerrar
        valid_states = [
            VoucherStatusEnum.APPROVED,  # EXIT sin retorno
            VoucherStatusEnum.IN_TRANSIT,  # EXIT con retorno completo
            VoucherStatusEnum.PENDING  # ENTRY registrado
        ]

        if voucher.status not in valid_states:
            raise BusinessRuleError(
                f"No se puede cerrar desde estado {voucher.status.value}"
            )

        # Asignar received_by si aplica
        if received_by_id:
            receiver = self.db.query(Individual).filter(
                Individual.id == received_by_id
            ).first()
            if not receiver:
                raise EntityNotFoundError("Individual", received_by_id)
            voucher.received_by_id = received_by_id

        # Si es con retorno, registrar fecha real
        if voucher.with_return:
            voucher.actual_return_date = date.today()

        # Cambiar estado
        voucher.status = VoucherStatusEnum.CLOSED
        voucher.updated_by = closed_by_user_id
        voucher.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    def mark_overdue(
        self,
        voucher_id: int,
        system_user_id: Optional[int] = None
    ) -> Voucher:
        """
        Marca un voucher como vencido: IN_TRANSIT → OVERDUE

        Ocurre cuando:
        - Fecha de retorno estimada ya pasó
        - Entry_log registrado como INCOMPLETE o DAMAGED

        Args:
            voucher_id: ID del voucher
            system_user_id: Usuario del sistema (opcional)

        Returns:
            Voucher marcado como vencido
        """
        voucher = self.get_voucher(voucher_id)

        # Cambiar estado
        voucher.status = VoucherStatusEnum.OVERDUE

        if system_user_id:
            voucher.updated_by = system_user_id

        voucher.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    def cancel_voucher(
        self,
        voucher_id: int,
        cancel_data: VoucherCancel,
        cancelled_by_user_id: int,
        role: int
    ) -> Voucher:
        """
        Cancela un voucher: → CANCELLED

        Solo se puede cancelar desde PENDING o APPROVED

        Args:
            voucher_id: ID del voucher
            cancel_data: Razón de cancelación
            cancelled_by_user_id: Usuario que cancela
            role: Rol del usuario (1-6)

        Returns:
            Voucher cancelado

        Raises:
            BusinessRuleError: Si ya está en tránsito o cerrado
        """
        voucher = self.get_voucher(voucher_id)

        # Validar acceso a la empresa (scoping multi-empresa)
        self._validate_company_access(cancelled_by_user_id, role, voucher.company_id)

        # Estados válidos para cancelar
        valid_states = [VoucherStatusEnum.PENDING, VoucherStatusEnum.APPROVED]

        if voucher.status not in valid_states:
            raise BusinessRuleError(
                f"No se puede cancelar un voucher en estado {voucher.status.value}"
            )

        # Cambiar estado
        voucher.status = VoucherStatusEnum.CANCELLED

        # Agregar razón de cancelación
        if voucher.internal_notes:
            voucher.internal_notes += f"\n[CANCELADO] {cancel_data.cancellation_reason}"
        else:
            voucher.internal_notes = f"[CANCELADO] {cancel_data.cancellation_reason}"

        voucher.updated_by = cancelled_by_user_id
        voucher.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    # ==================== BÚSQUEDAS Y FILTROS ====================

    def find_by_company(
        self,
        company_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Voucher]:
        """Busca vouchers por empresa"""
        return self.repository.find_by_company(
            company_id=company_id,
            skip=skip,
            limit=limit
        )

    def find_by_status(
        self,
        status: VoucherStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Voucher]:
        """Busca vouchers por estado"""
        return self.repository.find_by_status(
            status=status,
            skip=skip,
            limit=limit
        )

    def find_overdue_vouchers(self) -> List[Voucher]:
        """
        Encuentra vouchers vencidos

        Para uso en proceso automático diario
        """
        return self.repository.find_overdue_vouchers()

    def search_vouchers(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[int] = None,
        status: Optional[VoucherStatusEnum] = None,
        voucher_type: Optional[VoucherTypeEnum] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50,
        user_id: Optional[int] = None,
        role: Optional[int] = None
    ) -> List[Voucher]:
        """
        Búsqueda avanzada de vouchers con scoping multi-empresa.

        Si user_id y role se proporcionan, aplica filtro de empresas accesibles:
        - Admin (role=1): Sin restricción
        - Otros roles: Solo vouchers de empresas accesibles
        """
        # Aplicar scoping multi-empresa si se proporciona user_id y role
        company_ids_filter: Optional[List[int]] = None
        if user_id and role:
            # Admin y Checker no tienen restricción de empresa
            if role not in [1, 6]:
                accessible_ids = self._get_user_company_ids(user_id, role)

                # Si no tiene empresas asignadas, retornar lista vacía
                if not accessible_ids:
                    return []

                # Si se proporciona company_id específico, validar acceso
                if company_id:
                    if company_id not in accessible_ids:
                        raise BusinessRuleError(
                            f"No tiene permiso para ver vouchers de la empresa ID {company_id}"
                        )
                    # company_id es válido, se pasa directamente
                else:
                    # Sin company_id específico: buscar en TODAS las empresas accesibles
                    company_ids_filter = accessible_ids
                    company_id = None  # Evitar conflicto

        return self.repository.search_vouchers(
            search_term=search_term,
            company_id=company_id,
            company_ids=company_ids_filter,
            status=status,
            voucher_type=voucher_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )

    def get_statistics(
        self,
        company_id: Optional[int] = None,
        user_id: Optional[int] = None,
        role: Optional[int] = None
    ) -> dict:
        """
        Obtiene estadísticas de vouchers con scoping multi-empresa.

        Si user_id y role se proporcionan, aplica filtro de empresas accesibles:
        - Admin (role=1): Sin restricción (todas las empresas)
        - Otros roles: Solo estadísticas de empresas accesibles
        """
        # Aplicar scoping multi-empresa si se proporciona user_id y role
        if user_id and role:
            # Admin no tiene restricción
            if role != 1:
                accessible_ids = self._get_user_company_ids(user_id, role)

                # Si no tiene empresas asignadas, retornar estadísticas vacías
                if not accessible_ids:
                    return {
                        "total": 0,
                        "pending": 0,
                        "approved": 0,
                        "in_transit": 0,
                        "closed": 0,
                        "cancelled": 0,
                        "overdue": 0
                    }

                # Si se proporciona company_id específico, validar acceso
                if company_id:
                    if company_id not in accessible_ids:
                        raise BusinessRuleError(
                            f"No tiene permiso para ver estadísticas de la empresa ID {company_id}"
                        )
                # Si no se proporciona company_id, usar primera empresa accesible
                else:
                    company_id = accessible_ids[0] if accessible_ids else None

        return self.repository.get_statistics(company_id=company_id)

    # ==================== PROCESO AUTOMÁTICO ====================

    def check_and_mark_overdue(self, system_user_id: Optional[int] = None) -> int:
        """
        Proceso automático para marcar vouchers vencidos

        Busca vouchers con:
        - status = IN_TRANSIT
        - with_return = True
        - estimated_return_date < hoy

        Returns:
            Cantidad de vouchers marcados como vencidos
        """
        overdue_vouchers = self.find_overdue_vouchers()
        count = 0

        for voucher in overdue_vouchers:
            self.mark_overdue(voucher.id, system_user_id)
            count += 1

        return count

    # ==================== GENERACIÓN PDF/QR (Phase 4) ====================

    def get_voucher_with_details(self, voucher_id: int) -> Voucher:
        """
        Obtiene un voucher con todas sus relaciones cargadas (eager loading)
        para generar PDFs sin queries N+1.

        Args:
            voucher_id: ID del voucher

        Returns:
            Voucher con todas las relaciones cargadas

        Raises:
            EntityNotFoundError: Si el voucher no existe
        """
        from sqlalchemy.orm import joinedload

        voucher = self.db.query(Voucher).options(
            joinedload(Voucher.company),
            joinedload(Voucher.origin_branch),
            joinedload(Voucher.destination_branch),
            joinedload(Voucher.delivered_by),
            joinedload(Voucher.approved_by),
            joinedload(Voucher.received_by),
            joinedload(Voucher.details),
            joinedload(Voucher.entry_log),
            joinedload(Voucher.out_log)
        ).filter(
            Voucher.id == voucher_id,
            Voucher.is_deleted == False
        ).first()

        if not voucher:
            raise EntityNotFoundError("Voucher", voucher_id)

        return voucher

    def _is_qr_token_expired(self, voucher: Voucher) -> bool:
        """
        Verifica si el token QR ha expirado (>24 horas).

        Args:
            voucher: Instancia del voucher

        Returns:
            True si el token expiró o no existe
        """
        if not voucher.qr_token or not voucher.qr_image_last_generated_at:
            return True

        from datetime import timedelta
        expiration_time = voucher.qr_image_last_generated_at + timedelta(hours=24)
        return datetime.utcnow() > expiration_time

    def initiate_pdf_generation(self, voucher_id: int, current_user_id: int) -> dict:
        """
        Inicia la generación asíncrona de PDF usando Celery.

        Args:
            voucher_id: ID del voucher
            current_user_id: ID del usuario que solicita la generación

        Returns:
            dict con task_id, status, y message

        Raises:
            EntityNotFoundError: Si el voucher no existe
        """
        # Verificar que el voucher existe
        voucher = self.get_voucher(voucher_id)

        # Importar la tarea de Celery
        from app.shared.tasks.voucher_tasks import generate_pdf_task

        # Lanzar tarea asíncrona
        task = generate_pdf_task.delay(voucher_id)

        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": f"Generación de PDF iniciada para voucher {voucher.folio}"
        }

    def initiate_qr_generation(self, voucher_id: int, current_user_id: int) -> dict:
        """
        Inicia la generación asíncrona de imagen QR usando Celery.

        Args:
            voucher_id: ID del voucher
            current_user_id: ID del usuario que solicita la generación

        Returns:
            dict con task_id, status, y message

        Raises:
            EntityNotFoundError: Si el voucher no existe
        """
        # Verificar que el voucher existe
        voucher = self.get_voucher(voucher_id)

        # Importar la tarea de Celery
        from app.shared.tasks.voucher_tasks import generate_qr_task

        # Lanzar tarea asíncrona
        task = generate_qr_task.delay(voucher_id)

        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": f"Generación de QR iniciada para voucher {voucher.folio}"
        }

    def get_task_status(self, task_id: str) -> dict:
        """
        Consulta el estado de una tarea de Celery.

        Args:
            task_id: ID de la tarea de Celery

        Returns:
            dict con información del estado de la tarea:
            - task_id: ID de la tarea
            - status: PENDING, SUCCESS, FAILURE, RETRY
            - result: Resultado si SUCCESS, error si FAILURE
            - message: Mensaje descriptivo
        """
        from celery.result import AsyncResult
        from app.shared.tasks import celery_app

        task_result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": task_result.status,
            "message": ""
        }

        if task_result.status == "SUCCESS":
            response["result"] = task_result.result
            response["message"] = "Tarea completada exitosamente"
        elif task_result.status == "FAILURE":
            response["error"] = str(task_result.info)
            response["message"] = "Tarea falló durante la ejecución"
        elif task_result.status == "PENDING":
            response["message"] = "Tarea en cola o ejecutándose"
        elif task_result.status == "RETRY":
            response["message"] = "Tarea reintentando después de un error"
        else:
            response["message"] = f"Estado desconocido: {task_result.status}"

        return response
