"""
Voucher Schemas
"""
from .voucher_schemas import (
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
    EntryLogResponse,
    OutLogResponse,
    # Schemas de validacion linea por linea
    LineValidation,
    ValidateExitRequest,
    ConfirmEntryRequest,
    # Schemas de PDF/QR (Phase 4)
    TaskInitiatedResponse,
    TaskStatusResponse,
    VoucherWithGenerationInfo,
    PDFDownloadMetadata
)

__all__ = [
    "VoucherCreate",
    "VoucherUpdate",
    "VoucherApprove",
    "VoucherCancel",
    "VoucherResponse",
    "VoucherDetailedResponse",
    "VoucherWithDetailsResponse",
    "VoucherListResponse",
    "VoucherSearchResponse",
    "VoucherStatistics",
    # Schemas de logs
    "EntryLogResponse",
    "OutLogResponse",
    # Schemas de validacion linea por linea
    "LineValidation",
    "ValidateExitRequest",
    "ConfirmEntryRequest",
    # Schemas de PDF/QR
    "TaskInitiatedResponse",
    "TaskStatusResponse",
    "VoucherWithGenerationInfo",
    "PDFDownloadMetadata"
]