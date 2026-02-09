# =============================================================
# Dockerfile para FastAPI + Celery Worker
# =============================================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="Sistema de Vales"
LABEL description="FastAPI Backend + Celery Worker"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo requirements primero (para cachear layer)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p temp_files/pdfs temp_files/qrcodes && \
    chmod -R 755 temp_files

# Exponer puerto
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health', timeout=5)" || exit 1

# Comando por defecto (se sobrescribe en docker-compose para cada servicio)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
