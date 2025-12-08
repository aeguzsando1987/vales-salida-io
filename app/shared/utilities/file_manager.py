"""
File Manager Utility (Phase 4)

Gestiona el ciclo de vida de archivos temporales (PDFs y QR codes).
Incluye limpieza automática de archivos antiguos.
"""

from pathlib import Path
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class FileManager:
    """
    Gestor de archivos temporales.

    Proporciona métodos estáticos para crear directorios, eliminar archivos
    y limpiar archivos antiguos automáticamente.

    Ejemplo:
        >>> FileManager.ensure_directory_exists("temp_files/pdfs")
        >>> FileManager.cleanup_old_files("temp_files/pdfs", max_age_minutes=60)
        >>> size = FileManager.get_file_size("temp_files/pdfs/voucher_123.pdf")
    """

    @staticmethod
    def ensure_directory_exists(path: str) -> None:
        """
        Crea un directorio si no existe (incluyendo directorios padre).

        Args:
            path: Ruta del directorio a crear

        Example:
            >>> FileManager.ensure_directory_exists("temp_files/pdfs/2025/01")
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directorio asegurado: {path}")
        except Exception as e:
            logger.error(f"Error al crear directorio {path}: {e}")
            raise

    @staticmethod
    def delete_file(filepath: str) -> bool:
        """
        Elimina un archivo de forma segura.

        Args:
            filepath: Ruta del archivo a eliminar

        Returns:
            True si se eliminó exitosamente o no existía, False si hubo error

        Example:
            >>> success = FileManager.delete_file("temp_files/pdfs/voucher_old.pdf")
        """
        try:
            Path(filepath).unlink(missing_ok=True)
            logger.debug(f"Archivo eliminado: {filepath}")
            return True
        except Exception as e:
            logger.warning(f"Error al eliminar archivo {filepath}: {e}")
            return False

    @staticmethod
    def cleanup_old_files(directory: str, max_age_minutes: int) -> int:
        """
        Elimina archivos más antiguos que max_age_minutes en el directorio dado.

        Esta función es útil para limpieza automática de archivos temporales.
        Se ejecuta típicamente desde un scheduler job.

        Args:
            directory: Directorio a limpiar
            max_age_minutes: Edad máxima de archivos en minutos

        Returns:
            Número de archivos eliminados

        Example:
            >>> # Eliminar PDFs mayores a 1 hora
            >>> count = FileManager.cleanup_old_files("temp_files/pdfs", max_age_minutes=60)
            >>> print(f"Eliminados {count} archivos")
        """
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.debug(f"Directorio no existe para limpieza: {directory}")
            return 0

        deleted_count = 0

        try:
            for file in directory_path.iterdir():
                if file.is_file():
                    # Obtener tiempo de modificación del archivo
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)

                    if file_time < cutoff:
                        try:
                            file.unlink()
                            deleted_count += 1
                            logger.debug(f"Archivo antiguo eliminado: {file}")
                        except Exception as e:
                            logger.warning(f"No se pudo eliminar archivo {file}: {e}")

            if deleted_count > 0:
                logger.info(f"Limpieza completada: {deleted_count} archivos eliminados de {directory}")
            else:
                logger.debug(f"Sin archivos antiguos para limpiar en {directory}")

        except Exception as e:
            logger.error(f"Error durante limpieza de {directory}: {e}")

        return deleted_count

    @staticmethod
    def get_file_size(filepath: str) -> int:
        """
        Obtiene el tamaño de un archivo en bytes.

        Args:
            filepath: Ruta del archivo

        Returns:
            Tamaño del archivo en bytes

        Raises:
            FileNotFoundError: Si el archivo no existe

        Example:
            >>> size = FileManager.get_file_size("temp_files/pdfs/voucher_123.pdf")
            >>> print(f"Tamaño: {size / 1024:.2f} KB")
        """
        filepath_obj = Path(filepath)

        if not filepath_obj.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        return filepath_obj.stat().st_size

    @staticmethod
    def get_file_age_minutes(filepath: str) -> int:
        """
        Obtiene la edad de un archivo en minutos desde su última modificación.

        Args:
            filepath: Ruta del archivo

        Returns:
            Edad del archivo en minutos

        Raises:
            FileNotFoundError: Si el archivo no existe

        Example:
            >>> age = FileManager.get_file_age_minutes("temp_files/pdfs/voucher_123.pdf")
            >>> print(f"Archivo creado hace {age} minutos")
        """
        filepath_obj = Path(filepath)

        if not filepath_obj.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        file_time = datetime.fromtimestamp(filepath_obj.stat().st_mtime)
        age = datetime.utcnow() - file_time

        return int(age.total_seconds() / 60)

    @staticmethod
    def cleanup_empty_directories(root_dir: str) -> int:
        """
        Elimina directorios vacíos recursivamente.

        Args:
            root_dir: Directorio raíz donde buscar directorios vacíos

        Returns:
            Número de directorios eliminados

        Example:
            >>> count = FileManager.cleanup_empty_directories("temp_files")
            >>> print(f"Eliminados {count} directorios vacíos")
        """
        root_path = Path(root_dir)

        if not root_path.exists():
            return 0

        deleted_count = 0

        try:
            for dirpath in sorted(root_path.rglob('*'), reverse=True):
                if dirpath.is_dir():
                    try:
                        # Intentar eliminar si está vacío
                        dirpath.rmdir()
                        deleted_count += 1
                        logger.debug(f"Directorio vacío eliminado: {dirpath}")
                    except OSError:
                        # No está vacío o no se puede eliminar, continuar
                        pass

            if deleted_count > 0:
                logger.info(f"Eliminados {deleted_count} directorios vacíos de {root_dir}")

        except Exception as e:
            logger.error(f"Error durante limpieza de directorios vacíos en {root_dir}: {e}")

        return deleted_count
