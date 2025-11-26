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

    def start_transit(
        self,
        voucher_id: int,
        scanned_by_user_id: int
    ) -> Voucher:
        """
        Inicia tránsito de un voucher: APPROVED → IN_TRANSIT

        Esto ocurre cuando:
        - EXIT con retorno es escaneado por vigilancia
        - EXIT intercompañía es escaneado

        NO aplica para EXIT sin retorno (va directo a CLOSED)

        Args:
            voucher_id: ID del voucher
            scanned_by_user_id: Usuario que escanea

        Returns:
            Voucher en tránsito

        Raises:
            BusinessRuleError: Si no está en APPROVED o no requiere tránsito
        """
        voucher = self.get_voucher(voucher_id)

        # Validar estado
        if voucher.status != VoucherStatusEnum.APPROVED:
            raise BusinessRuleError(
                f"Solo vouchers APPROVED pueden iniciar tránsito. Estado actual: {voucher.status.value}"
            )

        # Validar que sea EXIT con retorno o intercompañía
        if voucher.voucher_type == VoucherTypeEnum.EXIT:
            if not voucher.with_return:
                raise BusinessRuleError(
                    "EXIT sin retorno va directo a CLOSED al escanear"
                )

        # Cambiar estado
        voucher.status = VoucherStatusEnum.IN_TRANSIT
        voucher.updated_by = scanned_by_user_id
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
