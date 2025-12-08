"""
Utility Modules for Phase 4: PDF/QR Generation

This package contains utility classes for generating PDFs and QR codes:
- PDFGenerator: HTML to PDF conversion using WeasyPrint
- QRGenerator: QR code image generation
- FileManager: Temporary file management and cleanup
"""

from .pdf_generator import PDFGenerator
from .qr_generator import QRGenerator
from .file_manager import FileManager

__all__ = ["PDFGenerator", "QRGenerator", "FileManager"]
