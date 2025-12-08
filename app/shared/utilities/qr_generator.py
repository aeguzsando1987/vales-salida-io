"""
Generador de Códigos QR (Phase 4)

Genera imágenes de códigos QR para validación de vouchers.
Usa la librería qrcode con backend PIL (Pillow).
"""

import qrcode
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class QRGenerator:
    """
    Generador de códigos QR para tokens de vouchers.

    Genera imágenes de códigos QR que pueden ser escaneadas por el rol Checker
    para validar salidas de vouchers.

    Ejemplo:
        >>> generator = QRGenerator("temp_files/qrcodes", box_size=10, border=4)
        >>> path = generator.generate_qr_image(voucher_id=1, token="abc123...")
        >>> print(path)
        /ruta/absoluta/a/temp_files/qrcodes/qr_1_20250101_120000.png
    """

    def __init__(self, output_dir: str, box_size: int = 10, border: int = 4):
        """
        Inicializa el generador de QR.

        Args:
            output_dir: Directorio donde guardar las imágenes QR
            box_size: Tamaño de cada caja del código QR (pixeles)
            border: Tamaño del borde en cajas
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.box_size = box_size
        self.border = border

        logger.info(f"QRGenerator inicializado: output_dir={self.output_dir}")

    def generate_qr_image(self, voucher_id: int, token: str) -> str:
        """
        Genera imagen de código QR para un voucher.

        Args:
            voucher_id: ID del voucher
            token: Token de seguridad a embeber en el QR

        Returns:
            Ruta absoluta al archivo de imagen QR generado

        Raises:
            ValueError: Si voucher_id o token son inválidos
            IOError: Si el archivo no puede ser escrito
        """
        if not voucher_id or voucher_id <= 0:
            raise ValueError(f"voucher_id inválido: {voucher_id}")

        if not token or len(token.strip()) == 0:
            raise ValueError("El token no puede estar vacío")

        # Crear instancia de QR
        qr = qrcode.QRCode(
            version=1,  # Auto-ajustar versión
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=self.box_size,
            border=self.border,
        )

        # Codificar datos del voucher
        data = self.encode_qr_data(voucher_id, token)
        qr.add_data(data)
        qr.make(fit=True)

        # Generar imagen
        img = qr.make_image(fill_color="black", back_color="white")

        # Generar nombre de archivo con timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"qr_{voucher_id}_{timestamp}.png"
        filepath = self.output_dir / filename

        # Guardar imagen
        try:
            img.save(filepath)
            logger.info(f"Imagen QR generada exitosamente: {filepath}")
        except Exception as e:
            logger.error(f"Error al guardar imagen QR: {e}")
            raise IOError(f"No se puede escribir imagen QR en {filepath}: {e}")

        return str(filepath.absolute())

    def encode_qr_data(self, voucher_id: int, token: str) -> str:
        """
        Codifica datos del voucher en formato legible por QR.

        Formato: voucher:{id}:token:{token}

        Args:
            voucher_id: ID del voucher
            token: Token de seguridad

        Returns:
            String codificado para QR
        """
        return f"voucher:{voucher_id}:token:{token}"

    def decode_qr_data(self, qr_data: str) -> Optional[dict]:
        """
        Decodifica datos de QR de vuelta a información del voucher.

        Args:
            qr_data: Contenido del código QR

        Returns:
            Dict con 'voucher_id' y 'token', o None si el formato es inválido

        Ejemplo:
            >>> decoded = generator.decode_qr_data("voucher:1:token:abc123")
            >>> print(decoded)
            {'voucher_id': 1, 'token': 'abc123'}
        """
        try:
            parts = qr_data.split(":")
            if len(parts) != 4:
                return None

            if parts[0] != "voucher" or parts[2] != "token":
                return None

            return {
                'voucher_id': int(parts[1]),
                'token': parts[3]
            }
        except (ValueError, IndexError):
            return None
