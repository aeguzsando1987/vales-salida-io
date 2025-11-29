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
import os

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

    # ==================== GENERACIÓN DE FOLIOS ====================

    def _generate_folio(
        self,
        company_id: int,
        voucher_type: VoucherTypeEnum,
        year: int
    ) -> str:
        """
        Genera folio único: {company_code}-{type}-{year}-{seq}

        Ejemplos:
            GPA-SAL-2025-0001  (EXIT)
            GPA-ENT-2025-0001  (ENTRY)

        Args:
            company_id: ID de la empresa
            voucher_type: ENTRY o EXIT
            year: Año actual

        Returns:
            Folio único generado
        """
        # Obtener código de empresa (primeros 3 chars del TIN)
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise EntityNotFoundError("Company", company_id)

        # Usar primeros 3 caracteres del TIN como código
        company_code = company.tin[:3].upper()

        # Tipo de voucher
        type_code = "ENT" if voucher_type == VoucherTypeEnum.ENTRY else "SAL"

        # Obtener última secuencia
        last_seq = self.repository.get_last_sequence_for_folio(
            company_id=company_id,
            voucher_type=voucher_type,
            year=year
        )
        next_seq = last_seq + 1

        # Formatear folio
        folio = f"{company_code}-{type_code}-{year}-{next_seq:04d}"

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

    def validate_qr_token(self, voucher_id: int, token: str) -> bool:
        """
        Valida token QR (válido por 24h)

        Args:
            voucher_id: ID del voucher
            token: Token a validar

        Returns:
            True si es válido, False si no
        """
        expected = self._generate_qr_token(voucher_id)
        return token == expected

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
        entry_status: EntryStatusEnum,
        received_by_id: int,
        missing_items_description: Optional[str] = None,
        notes: Optional[str] = None,
        confirming_user_id: int = 1
    ) -> Voucher:
        """
        Confirma recepción física de material (crea entry_log automáticamente)

        Flujos:
        - ENTRY: PENDING → (registra entry_log) → CLOSED/OVERDUE
        - EXIT con retorno: IN_TRANSIT → (registra entry_log) → CLOSED/OVERDUE
        - EXIT intercompañía: IN_TRANSIT → (registra entry_log) → CLOSED/OVERDUE

        Transiciones de estado:
        - Si entry_status=COMPLETE → voucher.status=CLOSED
        - Si entry_status=INCOMPLETE/DAMAGED → voucher.status=OVERDUE

        Args:
            voucher_id: ID del voucher
            entry_status: COMPLETE, INCOMPLETE o DAMAGED
            received_by_id: ID de quien recibe el material
            missing_items_description: Descripción de faltantes (obligatorio si INCOMPLETE/DAMAGED)
            notes: Observaciones adicionales
            confirming_user_id: Usuario que confirma (default: 1 = Admin)

        Returns:
            Voucher actualizado con entry_log creado

        Raises:
            EntityNotFoundError: Si voucher no existe
            BusinessRuleError: Si estado no permite confirmar entrada
            EntityValidationError: Si validaciones fallan
        """
        voucher = self.get_voucher(voucher_id)

        # Validar estados válidos
        valid_statuses = [
            VoucherStatusEnum.PENDING,      # ENTRY puro
            VoucherStatusEnum.IN_TRANSIT,   # EXIT con retorno
            VoucherStatusEnum.APPROVED      # Casos especiales
        ]

        if voucher.status not in valid_statuses:
            raise BusinessRuleError(
                f"No se puede confirmar entrada desde estado {voucher.status.value}. "
                f"Estados válidos: {[s.value for s in valid_statuses]}"
            )

        # Crear entry_log (validaciones internas)
        self._create_entry_log(
            voucher=voucher,
            entry_status=entry_status,
            received_by_id=received_by_id,
            missing_items_description=missing_items_description,
            notes=notes,
            created_by_user_id=confirming_user_id
        )

        # Actualizar voucher.received_by_id (firma digital)
        voucher.received_by_id = received_by_id

        # Actualizar fecha de retorno si aplica
        if voucher.with_return:
            voucher.actual_return_date = date.today()

        # Transición de estado basada en entry_status
        if entry_status == EntryStatusEnum.COMPLETE:
            voucher.status = VoucherStatusEnum.CLOSED
        else:
            # INCOMPLETE o DAMAGED
            voucher.status = VoucherStatusEnum.OVERDUE

        # Auditoría
        voucher.updated_by = confirming_user_id
        voucher.updated_at = datetime.utcnow()

        # Commit atómico (voucher + entry_log)
        self.db.commit()
        self.db.refresh(voucher)

        return voucher

    def validate_exit_voucher(
        self,
        voucher_id: int,
        validation_status: ValidationStatusEnum,
        scanned_by_id: int,
        observations: Optional[str] = None,
        qr_token: Optional[str] = None,
        validating_user_id: int = 1
    ) -> Voucher:
        """
        Valida salida de material mediante QR (crea out_log automáticamente)

        Flujos:
        - EXIT sin retorno: APPROVED → (crea out_log) → CLOSED
        - EXIT con retorno: APPROVED → (crea out_log) → IN_TRANSIT
        - EXIT intercompañía: APPROVED → (crea out_log) → IN_TRANSIT

        Args:
            voucher_id: ID del voucher
            validation_status: APPROVED, REJECTED o OBSERVATION
            scanned_by_id: ID del vigilante
            observations: Observaciones de inspección visual
            qr_token: Token QR (opcional, para validar)
            validating_user_id: Usuario que valida (default: 1 = Admin)

        Returns:
            Voucher actualizado con out_log creado

        Raises:
            EntityNotFoundError: Si voucher no existe
            BusinessRuleError: Si estado no permite validar salida
            EntityValidationError: Si QR token es inválido
        """
        voucher = self.get_voucher(voucher_id)

        # Validar estado
        if voucher.status != VoucherStatusEnum.APPROVED:
            raise BusinessRuleError(
                f"Solo vouchers APPROVED pueden validar salida. Estado actual: {voucher.status.value}"
            )

        # Validar QR token si se proporciona (opcional)
        if qr_token:
            if not self.validate_qr_token(voucher.id, qr_token):
                raise EntityValidationError(
                    "OutLog",
                    {"qr_token": "Token QR inválido o expirado"}
                )

        # Crear out_log (validaciones internas)
        self._create_out_log(
            voucher=voucher,
            validation_status=validation_status,
            scanned_by_id=scanned_by_id,
            observations=observations,
            created_by_user_id=validating_user_id
        )

        # Transición de estado basada en with_return
        if validation_status == ValidationStatusEnum.APPROVED:
            if voucher.with_return:
                # EXIT con retorno → IN_TRANSIT
                voucher.status = VoucherStatusEnum.IN_TRANSIT
            else:
                # EXIT sin retorno → CLOSED directo
                voucher.status = VoucherStatusEnum.CLOSED
        else:
            # REJECTED u OBSERVATION → permanece APPROVED (requiere acción)
            pass

        # Auditoría
        voucher.updated_by = validating_user_id
        voucher.updated_at = datetime.utcnow()

        # Commit atómico (voucher + out_log)
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
        created_by_user_id: int
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

        Returns:
            Voucher creado
        """
        # Validar empresa existe
        company = self.db.query(Company).filter(
            Company.id == voucher_data.company_id
        ).first()
        if not company:
            raise EntityNotFoundError("Company", voucher_data.company_id)

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
        year = datetime.now().year
        folio = self._generate_folio(
            company_id=voucher_data.company_id,
            voucher_type=voucher_data.voucher_type,
            year=year
        )

        # Crear voucher
        new_voucher = Voucher(
            folio=folio,
            voucher_type=voucher_data.voucher_type,
            status=VoucherStatusEnum.PENDING,  # Estado inicial
            company_id=voucher_data.company_id,
            origin_branch_id=voucher_data.origin_branch_id,
            destination_branch_id=voucher_data.destination_branch_id,
            delivered_by_id=voucher_data.delivered_by_id,
            with_return=voucher_data.with_return,
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
        active_only: bool = True
    ) -> List[Voucher]:
        """
        Lista todos los vouchers

        Args:
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos

        Returns:
            Lista de vouchers
        """
        return self.repository.get_all(skip=skip, limit=limit, active_only=active_only)

    # ==================== TRANSICIONES DE ESTADO ====================

    def approve_voucher(
        self,
        voucher_id: int,
        approve_data: VoucherApprove,
        approved_by_user_id: int
    ) -> Voucher:
        """
        Aprueba un voucher: PENDING → APPROVED

        Args:
            voucher_id: ID del voucher
            approve_data: Datos de aprobación
            approved_by_user_id: Usuario que aprueba

        Returns:
            Voucher aprobado

        Raises:
            BusinessRuleError: Si no está en PENDING
        """
        voucher = self.get_voucher(voucher_id)

        # Validar estado
        if voucher.status != VoucherStatusEnum.PENDING:
            raise BusinessRuleError(
                f"Solo se pueden aprobar vouchers en estado PENDING. Estado actual: {voucher.status.value}"
            )

        # Validar aprobador existe
        approver = self.db.query(Individual).filter(
            Individual.id == approve_data.approved_by_id
        ).first()
        if not approver:
            raise EntityNotFoundError("Individual", approve_data.approved_by_id)

        # Cambiar estado
        voucher.status = VoucherStatusEnum.APPROVED
        voucher.approved_by_id = approve_data.approved_by_id

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
        cancelled_by_user_id: int
    ) -> Voucher:
        """
        Cancela un voucher: → CANCELLED

        Solo se puede cancelar desde PENDING o APPROVED

        Args:
            voucher_id: ID del voucher
            cancel_data: Razón de cancelación
            cancelled_by_user_id: Usuario que cancela

        Returns:
            Voucher cancelado

        Raises:
            BusinessRuleError: Si ya está en tránsito o cerrado
        """
        voucher = self.get_voucher(voucher_id)

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
        limit: int = 50
    ) -> List[Voucher]:
        """Búsqueda avanzada de vouchers"""
        return self.repository.search_vouchers(
            search_term=search_term,
            company_id=company_id,
            status=status,
            voucher_type=voucher_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )

    def get_statistics(self, company_id: Optional[int] = None) -> dict:
        """Obtiene estadísticas de vouchers"""
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
