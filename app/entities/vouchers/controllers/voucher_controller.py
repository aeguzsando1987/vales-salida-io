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
    VoucherStatistics
)
from app.entities.vouchers.models.voucher import VoucherStatusEnum, VoucherTypeEnum

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

            return VoucherListResponse(
                vouchers=[VoucherResponse.model_validate(v) for v in vouchers],
                total=total,
                page=1,
                per_page=limit
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
