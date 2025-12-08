"""
Controller para la entidad Voucher.

Orquesta las operaciones HTTP, maneja request/response y delega
la lógica de negocio al VoucherService.

Autor: E. Guzman
Fecha: 2025-11-12
"""

from typing import Optional
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.entities.vouchers.services.voucher_service import VoucherService
from app.entities.vouchers.schemas.voucher_schemas import (
    VoucherCreate,
    VoucherUpdate,
    VoucherApprove,
    VoucherCancel,
    VoucherResponse,
    VoucherDetailedResponse,
    VoucherWithDetailsResponse,
    VoucherListResponse,
    VoucherSearchResponse,
    VoucherStatistics,
    # Schemas de logs
    EntryLogCreate,
    EntryLogResponse,
    OutLogCreate,
    OutLogResponse,
    # Schemas de validacion linea por linea
    ConfirmEntryRequest,
    ValidateExitRequest,
    # Schemas de PDF/QR (Phase 4)
    TaskInitiatedResponse,
    TaskStatusResponse,
    VoucherWithGenerationInfo,
    PDFDownloadMetadata
)
from app.entities.vouchers.models.voucher import VoucherStatusEnum, VoucherTypeEnum
from app.entities.vouchers.models.entry_log import EntryStatusEnum
from app.entities.vouchers.models.out_log import ValidationStatusEnum

from app.shared.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    BusinessRuleError
)


class VoucherController:
    """
    Controller para Voucher.

    Maneja request/response y orquesta llamadas al Service.
    """

    def __init__(self, db: Session):
        """
        Inicializa el controller con su service.

        Args:
            db: Sesión de base de datos
        """
        self.service = VoucherService(db)

    # ==================== OPERACIONES CRUD ====================

    def create(
        self,
        voucher_data: VoucherCreate,
        current_user_id: int
    ) -> VoucherResponse:
        """
        Crea un nuevo voucher.

        Estado inicial: PENDING
        Genera automáticamente: folio y token QR

        Args:
            voucher_data: Datos del voucher
            current_user_id: ID del usuario autenticado

        Returns:
            Voucher creado

        Raises:
            HTTPException 400: Si validaciones fallan
            HTTPException 404: Si relaciones no existen
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.create_voucher(voucher_data, current_user_id)
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except EntityValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear voucher: {str(e)}"
            )

    def get_by_id(
        self,
        voucher_id: int,
        detailed: bool = False,
        include_details: bool = False
    ) -> VoucherResponse | VoucherDetailedResponse | VoucherWithDetailsResponse:
        """
        Obtiene un voucher por ID.

        Args:
            voucher_id: ID del voucher
            detailed: Si incluir nombres de relaciones expandidos
            include_details: Si incluir líneas de detalle del voucher

        Returns:
            Voucher encontrado (con o sin líneas de detalle)

        Raises:
            HTTPException 404: Si no existe
            HTTPException 500: Si error interno
        """
        try:
            # Obtener voucher del servicio (con o sin details cargados)
            voucher = self.service.get_voucher(voucher_id, include_details=include_details)

            # Si se solicitan las líneas de detalle
            if include_details:
                # Siempre usar VoucherWithDetailsResponse (que ya incluye campos detailed)
                response = VoucherWithDetailsResponse.model_validate(voucher)
                # Expandir nombres de relaciones
                response.company_name = voucher.company.company_name if voucher.company else None
                response.approved_by_name = voucher.approved_by.full_name if voucher.approved_by else None
                response.delivered_by_name = voucher.delivered_by.full_name if voucher.delivered_by else None
                response.received_by_name = voucher.received_by.full_name if voucher.received_by else None
                return response

            # Si solo se solicita información detallada (sin líneas)
            elif detailed:
                response = VoucherDetailedResponse.model_validate(voucher)
                response.company_name = voucher.company.company_name if voucher.company else None
                response.approved_by_name = voucher.approved_by.full_name if voucher.approved_by else None
                response.delivered_by_name = voucher.delivered_by.full_name if voucher.delivered_by else None
                response.received_by_name = voucher.received_by.full_name if voucher.received_by else None
                return response

            # Respuesta básica
            else:
                return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener voucher: {str(e)}"
            )

    def get_by_folio(self, folio: str) -> VoucherResponse:
        """
        Obtiene un voucher por folio.

        Args:
            folio: Folio del voucher

        Returns:
            Voucher encontrado

        Raises:
            HTTPException 404: Si no existe
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.get_voucher_by_folio(folio)
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener voucher por folio: {str(e)}"
            )

    def update(
        self,
        voucher_id: int,
        voucher_data: VoucherUpdate,
        current_user_id: int
    ) -> VoucherResponse:
        """
        Actualiza un voucher.

        Solo permitido en estado PENDING.

        Args:
            voucher_id: ID del voucher
            voucher_data: Datos a actualizar
            current_user_id: Usuario autenticado

        Returns:
            Voucher actualizado

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si no está en PENDING
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.update_voucher(
                voucher_id,
                voucher_data,
                current_user_id
            )
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except BusinessRuleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar voucher: {str(e)}"
            )

    def list_vouchers(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> VoucherListResponse:
        """
        Lista todos los vouchers paginados.

        Args:
            skip: Registros a saltar
            limit: Máximo de registros
            active_only: Solo activos

        Returns:
            Lista paginada de vouchers

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            vouchers = self.service.list_vouchers(skip, limit, active_only)
            total = len(vouchers)

            # Calcular total de páginas
            import math
            total_pages = math.ceil(total / limit) if limit > 0 else 1

            return VoucherListResponse(
                vouchers=[VoucherResponse.model_validate(v) for v in vouchers],
                total=total,
                page=1,
                per_page=limit,
                total_pages=total_pages
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar vouchers: {str(e)}"
            )

    # ==================== TRANSICIONES DE ESTADO ====================

    def approve(
        self,
        voucher_id: int,
        approve_data: VoucherApprove,
        current_user_id: int
    ) -> VoucherResponse:
        """
        Aprueba un voucher: PENDING → APPROVED

        Args:
            voucher_id: ID del voucher
            approve_data: Datos de aprobación (quién aprueba)
            current_user_id: Usuario autenticado

        Returns:
            Voucher aprobado

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si no está en PENDING
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.approve_voucher(
                voucher_id,
                approve_data,
                current_user_id
            )
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except BusinessRuleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al aprobar voucher: {str(e)}"
            )

    def start_transit(
        self,
        voucher_id: int,
        current_user_id: int
    ) -> VoucherResponse:
        """
        Inicia tránsito: APPROVED → IN_TRANSIT

        Solo para EXIT con retorno o EXIT intercompañía.

        Args:
            voucher_id: ID del voucher
            current_user_id: Usuario que escanea QR

        Returns:
            Voucher en tránsito

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si no aplica
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.start_transit(voucher_id, current_user_id)
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except BusinessRuleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al iniciar tránsito: {str(e)}"
            )

    def close(
        self,
        voucher_id: int,
        current_user_id: int,
        received_by_id: Optional[int] = None
    ) -> VoucherResponse:
        """
        Cierra un voucher: → CLOSED

        Args:
            voucher_id: ID del voucher
            current_user_id: Usuario que cierra
            received_by_id: ID de quien recibe (opcional)

        Returns:
            Voucher cerrado

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si estado no permite cierre
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.close_voucher(
                voucher_id,
                current_user_id,
                received_by_id
            )
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except BusinessRuleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al cerrar voucher: {str(e)}"
            )

    def cancel(
        self,
        voucher_id: int,
        cancel_data: VoucherCancel,
        current_user_id: int
    ) -> VoucherResponse:
        """
        Cancela un voucher: → CANCELLED

        Solo desde PENDING o APPROVED.

        Args:
            voucher_id: ID del voucher
            cancel_data: Razón de cancelación
            current_user_id: Usuario que cancela

        Returns:
            Voucher cancelado

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si ya está en tránsito o cerrado
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.cancel_voucher(
                voucher_id,
                cancel_data,
                current_user_id
            )
            return VoucherResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except BusinessRuleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al cancelar voucher: {str(e)}"
            )

    # ==================== LOG OPERATIONS ====================

    def confirm_entry(
        self,
        voucher_id: int,
        entry_data: ConfirmEntryRequest,
        current_user
    ) -> VoucherDetailedResponse:
        """
        Confirma recepcion fisica de material LINEA POR LINEA (crea entry_log automaticamente).

        Logica ESTRICTA: Vale solo cierra si TODAS las lineas tienen ok=true.
        Si alguna linea tiene ok=false, el voucher cambia a INCOMPLETE_DAMAGED.

        Args:
            voucher_id: ID del voucher
            entry_data: ConfirmEntryRequest con line_validations y observaciones
            current_user: Usuario que confirma (usado para firma digital automatica)

        Returns:
            Voucher actualizado con entry_log incluido

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si estado no permite o validaciones fallan
            HTTPException 500: Si error interno
        """
        try:
            # Convertir LineValidation Pydantic objects a dicts para service
            line_validations = [
                {
                    "detail_id": validation.detail_id,
                    "ok": validation.ok,
                    "notes": validation.notes
                }
                for validation in entry_data.line_validations
            ]

            voucher = self.service.confirm_entry_voucher(
                voucher_id=voucher_id,
                received_by_id=entry_data.received_by_id,
                line_validations=line_validations,
                general_observations=entry_data.general_observations,
                confirming_user_id=current_user.id
            )

            # Retornar voucher actualizado
            return VoucherDetailedResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except (BusinessRuleError, EntityValidationError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al confirmar entrada: {str(e)}"
            )

    def validate_exit(
        self,
        voucher_id: int,
        validation_data: ValidateExitRequest,
        qr_token: Optional[str],
        current_user_id: int
    ) -> VoucherDetailedResponse:
        """
        Valida salida de material LINEA POR LINEA mediante QR (crea out_log automaticamente).

        Logica FLEXIBLE: Material SIEMPRE sale, incluso si hay observaciones.
        El checker valida cada linea individualmente (ok_exit true/false).

        Args:
            voucher_id: ID del voucher
            validation_data: ValidateExitRequest con line_validations y observaciones
            qr_token: Token QR (opcional)
            current_user_id: Usuario que valida

        Returns:
            Voucher actualizado con out_log incluido

        Raises:
            HTTPException 404: Si no existe
            HTTPException 400: Si estado no permite o QR invalido
            HTTPException 500: Si error interno
        """
        try:
            # Convertir LineValidation Pydantic objects a dicts para service
            line_validations = [
                {
                    "detail_id": validation.detail_id,
                    "ok": validation.ok,
                    "notes": validation.notes
                }
                for validation in validation_data.line_validations
            ]

            voucher = self.service.validate_exit_voucher(
                voucher_id=voucher_id,
                scanned_by_id=validation_data.scanned_by_id,
                line_validations=line_validations,
                general_observations=validation_data.general_observations,
                validating_user_id=current_user_id
            )

            # Retornar voucher actualizado
            return VoucherDetailedResponse.model_validate(voucher)

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except (BusinessRuleError, EntityValidationError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al validar salida: {str(e)}"
            )

    def get_logs(self, voucher_id: int) -> dict:
        """
        Obtiene la bitácora completa de un voucher (entry_log + out_log).

        Args:
            voucher_id: ID del voucher

        Returns:
            Dict con entry_log y out_log formateados

        Raises:
            HTTPException 404: Si no existe
            HTTPException 500: Si error interno
        """
        try:
            logs_data = self.service.get_voucher_logs(voucher_id)

            # Formatear logs con nombres
            formatted_logs = {
                "voucher_id": logs_data["voucher_id"],
                "folio": logs_data["folio"],
                "entry_log": None,
                "out_log": None
            }

            if logs_data["entry_log"]:
                formatted_logs["entry_log"] = self._format_entry_log_response(
                    logs_data["entry_log"]
                )

            if logs_data["out_log"]:
                formatted_logs["out_log"] = self._format_out_log_response(
                    logs_data["out_log"]
                )

            return formatted_logs

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener logs: {str(e)}"
            )

    # ==================== HELPER METHODS (PRIVATE) ====================

    def _format_entry_log_response(self, entry_log) -> dict:
        """
        Formatea entry_log con nombres resueltos.

        Args:
            entry_log: EntryLog model instance

        Returns:
            Dict con campos del log + nombres
        """
        return {
            "id": entry_log.id,
            "voucher_id": entry_log.voucher_id,
            "entry_status": entry_log.entry_status.value,
            "received_by_id": entry_log.received_by_id,
            "received_by_name": (
                entry_log.received_by.full_name
                if entry_log.received_by else None
            ),
            "missing_items_description": entry_log.missing_items_description,
            "notes": entry_log.notes,
            "created_at": entry_log.created_at,
            "created_by": entry_log.created_by,
            "creator_name": (
                entry_log.creator.email
                if entry_log.creator else None
            )
        }

    def _format_out_log_response(self, out_log) -> dict:
        """
        Formatea out_log con nombres resueltos.

        Args:
            out_log: OutLog model instance

        Returns:
            Dict con campos del log + nombres
        """
        return {
            "id": out_log.id,
            "voucher_id": out_log.voucher_id,
            "validation_status": out_log.validation_status.value,
            "scanned_by_id": out_log.scanned_by_id,
            "scanned_by_name": (
                out_log.scanned_by.full_name
                if out_log.scanned_by else None
            ),
            "observations": out_log.observations,
            "created_at": out_log.created_at,
            "created_by": out_log.created_by,
            "creator_name": (
                out_log.creator.email
                if out_log.creator else None
            )
        }

    # ==================== BÚSQUEDA Y FILTROS ====================

    def search(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[int] = None,
        status: Optional[VoucherStatusEnum] = None,
        voucher_type: Optional[VoucherTypeEnum] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50
    ) -> VoucherSearchResponse:
        """
        Búsqueda avanzada de vouchers.

        Args:
            search_term: Término de búsqueda (folio, notas)
            company_id: Filtrar por empresa
            status: Filtrar por estado
            voucher_type: Filtrar por tipo
            from_date: Fecha desde
            to_date: Fecha hasta
            limit: Máximo de resultados

        Returns:
            Resultados de búsqueda

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            vouchers = self.service.search_vouchers(
                search_term=search_term,
                company_id=company_id,
                status=status,
                voucher_type=voucher_type,
                from_date=from_date,
                to_date=to_date,
                limit=limit
            )

            return VoucherSearchResponse(
                results=[VoucherResponse.model_validate(v) for v in vouchers],
                total=len(vouchers)
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en búsqueda: {str(e)}"
            )

    def find_by_company(
        self,
        company_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[VoucherResponse]:
        """
        Lista vouchers de una empresa.

        Args:
            company_id: ID de la empresa
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de vouchers

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            vouchers = self.service.find_by_company(company_id, skip, limit)
            return [VoucherResponse.model_validate(v) for v in vouchers]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar vouchers por empresa: {str(e)}"
            )

    def find_by_status(
        self,
        status: VoucherStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> list[VoucherResponse]:
        """
        Lista vouchers por estado.

        Args:
            status: Estado del voucher
            skip: Registros a saltar
            limit: Máximo de registros

        Returns:
            Lista de vouchers

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            vouchers = self.service.find_by_status(status, skip, limit)
            return [VoucherResponse.model_validate(v) for v in vouchers]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar vouchers por estado: {str(e)}"
            )

    # ==================== VALIDACIÓN QR ====================

    def validate_qr(
        self,
        voucher_id: int,
        token: str
    ) -> dict:
        """
        Valida token QR de un voucher.

        Args:
            voucher_id: ID del voucher
            token: Token a validar

        Returns:
            Resultado de validación

        Raises:
            HTTPException 404: Si voucher no existe
            HTTPException 500: Si error interno
        """
        try:
            # Verificar que voucher existe
            voucher = self.service.get_voucher(voucher_id)

            # Validar token
            is_valid = self.service.validate_qr_token(voucher_id, token)

            return {
                "voucher_id": voucher_id,
                "folio": voucher.folio,
                "is_valid": is_valid,
                "status": voucher.status.value,
                "message": "Token válido" if is_valid else "Token inválido o expirado"
            }

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al validar QR: {str(e)}"
            )

    # ==================== ESTADÍSTICAS ====================

    def get_statistics(
        self,
        company_id: Optional[int] = None
    ) -> VoucherStatistics:
        """
        Obtiene estadísticas de vouchers.

        Args:
            company_id: Filtrar por empresa (opcional)

        Returns:
            Estadísticas completas

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            stats = self.service.get_statistics(company_id)
            return VoucherStatistics(**stats)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener estadísticas: {str(e)}"
            )

    # ==================== UTILIDADES ====================

    def get_enums(self) -> dict:
        """
        Retorna los ENUMs disponibles para Voucher.

        Útil para formularios dinámicos en frontend.

        Returns:
            Diccionario con valores de ENUMs
        """
        return {
            "voucher_types": [t.value for t in VoucherTypeEnum],
            "voucher_statuses": [s.value for s in VoucherStatusEnum]
        }

    # ==================== PROCESO AUTOMÁTICO ====================

    def check_overdue_vouchers(
        self,
        system_user_id: Optional[int] = None
    ) -> dict:
        """
        Proceso automático: marca vouchers vencidos.

        Para ejecutar diariamente vía scheduler.

        Args:
            system_user_id: Usuario del sistema (opcional)

        Returns:
            Resumen de operación

        Raises:
            HTTPException 500: Si error interno
        """
        try:
            count = self.service.check_and_mark_overdue(system_user_id)

            return {
                "message": f"Proceso completado: {count} vouchers marcados como vencidos",
                "count": count
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en proceso automático: {str(e)}"
            )

    # ==================== GENERACIÓN PDF/QR (Phase 4) ====================

    def initiate_pdf_generation(
        self,
        voucher_id: int,
        current_user_id: int
    ) -> TaskInitiatedResponse:
        """
        Inicia la generación asíncrona de PDF para un voucher.

        Args:
            voucher_id: ID del voucher
            current_user_id: ID del usuario que solicita la operación

        Returns:
            TaskInitiatedResponse con task_id y status PENDING

        Raises:
            HTTPException 404: Si el voucher no existe
            HTTPException 500: Si error al iniciar tarea
        """
        try:
            result = self.service.initiate_pdf_generation(
                voucher_id=voucher_id,
                current_user_id=current_user_id
            )

            return TaskInitiatedResponse(
                task_id=result["task_id"],
                status=result["status"],
                message=result["message"],
                voucher_folio=None  # Se puede agregar si es necesario
            )

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al iniciar generación de PDF: {str(e)}"
            )

    def initiate_qr_generation(
        self,
        voucher_id: int,
        current_user_id: int
    ) -> TaskInitiatedResponse:
        """
        Inicia la generación asíncrona de imagen QR para un voucher.

        Args:
            voucher_id: ID del voucher
            current_user_id: ID del usuario que solicita la operación

        Returns:
            TaskInitiatedResponse con task_id y status PENDING

        Raises:
            HTTPException 404: Si el voucher no existe
            HTTPException 500: Si error al iniciar tarea
        """
        try:
            result = self.service.initiate_qr_generation(
                voucher_id=voucher_id,
                current_user_id=current_user_id
            )

            return TaskInitiatedResponse(
                task_id=result["task_id"],
                status=result["status"],
                message=result["message"],
                voucher_folio=None  # Se puede agregar si es necesario
            )

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al iniciar generación de QR: {str(e)}"
            )

    def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """
        Consulta el estado de una tarea de Celery (PDF o QR).

        Args:
            task_id: ID de la tarea de Celery

        Returns:
            TaskStatusResponse con información del estado actual

        Raises:
            HTTPException 500: Si error al consultar tarea
        """
        try:
            result = self.service.get_task_status(task_id)

            return TaskStatusResponse(
                task_id=result["task_id"],
                status=result["status"],
                message=result["message"],
                result=result.get("result"),
                error=result.get("error")
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al consultar estado de tarea: {str(e)}"
            )

    def get_generation_info(self, voucher_id: int) -> VoucherWithGenerationInfo:
        """
        Obtiene información de generación de PDF/QR de un voucher.

        Incluye timestamps de última generación y flags calculados.

        Args:
            voucher_id: ID del voucher

        Returns:
            VoucherWithGenerationInfo con información completa

        Raises:
            HTTPException 404: Si el voucher no existe
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.get_voucher(voucher_id)

            # Construir respuesta con flags calculados
            from datetime import datetime, timedelta

            pdf_available = voucher.pdf_last_generated_at is not None
            qr_available = voucher.qr_image_last_generated_at is not None
            qr_token_expired = False

            if voucher.qr_image_last_generated_at:
                expiration = voucher.qr_image_last_generated_at + timedelta(hours=24)
                qr_token_expired = datetime.utcnow() > expiration

            return VoucherWithGenerationInfo(
                **voucher.__dict__,
                pdf_available=pdf_available,
                qr_available=qr_available,
                qr_token_expired=qr_token_expired
            )

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener información de generación: {str(e)}"
            )

    def get_pdf_metadata(self, voucher_id: int) -> PDFDownloadMetadata:
        """
        Obtiene metadata del último PDF generado para un voucher.

        NOTA: Esta función requiere que el PDF exista en disco.
        Si el PDF temporal ya fue limpiado, devuelve 404.

        Args:
            voucher_id: ID del voucher

        Returns:
            PDFDownloadMetadata con información del archivo

        Raises:
            HTTPException 404: Si voucher no existe o PDF no disponible
            HTTPException 500: Si error interno
        """
        try:
            voucher = self.service.get_voucher(voucher_id)

            if not voucher.pdf_last_generated_at:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Este voucher no tiene PDF generado"
                )

            # Construir ruta esperada del PDF
            from pathlib import Path
            from app.config.settings import settings

            timestamp = voucher.pdf_last_generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"voucher_{voucher_id}_{timestamp}.pdf"
            pdf_path = Path(settings.pdf_temp_dir) / filename

            # Verificar si el archivo existe
            if not pdf_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="El archivo PDF temporal ya no está disponible. Genere uno nuevo."
                )

            # Obtener información del archivo
            file_size = pdf_path.stat().st_size

            # Calcular expiración
            from datetime import timedelta
            expires_at = voucher.pdf_last_generated_at + timedelta(minutes=settings.pdf_temp_file_cleanup_minutes)

            return PDFDownloadMetadata(
                voucher_id=voucher.id,
                voucher_folio=voucher.folio,
                file_path=str(pdf_path.absolute()),
                file_size_bytes=file_size,
                generated_at=voucher.pdf_last_generated_at,
                expires_at=expires_at,
                download_url=f"/api/vouchers/{voucher_id}/download-pdf"
            )

        except EntityNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener metadata del PDF: {str(e)}"
            )
