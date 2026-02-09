# Guía de Configuración para Desarrollo

Esta guía te ayudará a iniciar todos los servicios necesarios para trabajar con el sistema de vales.

---

## Servicios Requeridos

El sistema necesita **3 servicios** funcionando simultáneamente:

1. **API FastAPI** - Servidor principal (Puerto 8001)
2. **Redis** - Base de datos en memoria para Celery (Puerto 6379)
3. **Celery Worker** - Procesamiento asíncrono de tareas (PDF, QR)

---

## Inicio Rápido

### 1. Iniciar Redis (Docker)

Redis debe correr en Docker con el nombre de contenedor `redis-vales`.

**Comando:**
```bash
docker run -d \
  --name redis-vales \
  -p 6379:6379 \
  redis:alpine
```

**Verificar que está corriendo:**
```bash
docker ps | grep redis-vales
```

**Detener Redis (cuando termines):**
```bash
docker stop redis-vales
```

**Reiniciar Redis (si ya existe el contenedor):**
```bash
docker start redis-vales
```

**Eliminar contenedor (si necesitas recrearlo):**
```bash
docker rm -f redis-vales
```

---

### 2. Iniciar Servidor FastAPI

El servidor API escucha en el puerto **8001** (o el primer puerto libre disponible).

**Opción A - Primera vez / Servidor limpio:**
```bash
python scripts.py start
```

**Opción B - Si el servidor ya está corriendo:**
```bash
python scripts.py restart
```

**Verificar que está corriendo:**
- Abre en tu navegador: **http://localhost:8001/docs**
- Deberías ver la documentación Swagger UI

**Logs del servidor:**
El servidor muestra logs en tiempo real en la terminal.

---

### 3. Iniciar Celery Worker

Celery procesa tareas asíncronas (generación de PDFs, códigos QR, etc.).

**IMPORTANTE:** Abre una **nueva terminal** (no cerrar la del servidor API).

**Comando (Windows):**
```bash
celery -A app.shared.tasks.celery_app worker --loglevel=info --pool=solo
```

**Comando (Linux/Mac):**
```bash
celery -A app.shared.tasks.celery_app worker --loglevel=info
```

**Verificar que está corriendo:**
Deberías ver logs de Celery mostrando:
```
 -------------- celery@HOSTNAME v5.x.x
---- **** -----
--- * ***  * -- Windows-10-... 2026-01-XX XX:XX:XX
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         celery_app:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- *** --- * --- .> results:     redis://localhost:6379/0
```

**Detener Celery:**
- Presiona `Ctrl+C` en la terminal de Celery

---

## Verificación Completa

Una vez que los 3 servicios estén corriendo, verifica que todo funciona:

### Test 1: Redis conectado
```bash
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); print('REDIS OK:', r.ping())"
```
**Resultado esperado:** `REDIS OK: True`

### Test 2: API respondiendo
```bash
curl http://localhost:8001/docs
```
**Resultado esperado:** HTML de Swagger UI

### Test 3: Celery procesando
1. Ir a Swagger: http://localhost:8001/docs
2. Login con credenciales (POST /login)
3. Generar PDF de un voucher (POST /vouchers/33/generate-pdf)
4. Consultar estado de la tarea (GET /vouchers/tasks/{task_id}/status)
5. Si devuelve `"status": "SUCCESS"`, Celery está funcionando

---

## Pruebas de Endpoints (PDF/QR)

Una vez que todos los servicios estén corriendo, puedes probar los endpoints de generación de PDFs.

### Opción 1: Usando Swagger UI (Recomendado)

#### Paso 1: Autenticación

1. Abre Swagger UI: http://localhost:8001/docs
2. Busca el endpoint **POST /login**
3. Click en "Try it out"
4. Ingresa las credenciales:
```json
{
  "email": "alonso.guzman@gpamex.com",
  "password": "root"
}
```
5. Click "Execute"
6. Copia el `access_token` de la respuesta
7. Click en el botón **"Authorize"** (candado verde, arriba a la derecha)
8. En el campo, escribe: `Bearer {tu_token_aqui}`
9. Click "Authorize" y luego "Close"

#### Paso 2: Listar Vouchers Disponibles

1. Busca el endpoint **GET /vouchers/**
2. Click "Try it out"
3. Deja los parámetros por defecto (o ajusta `limit` a 20)
4. Click "Execute"
5. Anota algunos IDs de vouchers para probar (ejemplo: 33, 28, 19)

#### Paso 3: Generar PDF (Asíncrono)

1. Busca el endpoint **POST /vouchers/{voucher_id}/generate-pdf**
2. Click "Try it out"
3. Ingresa un voucher_id (ejemplo: `33`)
4. Click "Execute"
5. **Copia el `task_id`** de la respuesta (ejemplo: `"3e205ae5-239a-4952-8b57-af4a82744cd1"`)

**Respuesta esperada:**
```json
{
  "task_id": "3e205ae5-239a-4952-8b57-af4a82744cd1",
  "status": "PENDING",
  "message": "Generación de PDF iniciada para voucher RFC-SAL-20260115-004",
  "voucher_folio": null
}
```

#### Paso 4: Consultar Estado de la Tarea

1. Busca el endpoint **GET /vouchers/tasks/{task_id}/status**
2. Click "Try it out"
3. Pega el `task_id` que copiaste
4. Click "Execute"
5. **Repite este paso hasta que `status` sea `"SUCCESS"`** (puede tardar 2-3 segundos)

**Respuesta esperada (cuando está listo):**
```json
{
  "task_id": "3e205ae5-239a-4952-8b57-af4a82744cd1",
  "status": "SUCCESS",
  "message": "Tarea completada exitosamente",
  "result": {
    "pdf_path": "C:\\...\\temp_files\\pdfs\\voucher_33_20260116_235555.pdf",
    "qr_path": "C:\\...\\temp_files\\qrcodes\\qr_33_20260116_235555.png",
    "file_size": 13773,
    "generated_at": "2026-01-16T23:55:55.127517"
  }
}
```

#### Paso 5: Descargar PDF

1. Busca el endpoint **GET /vouchers/{voucher_id}/download-pdf**
2. Click "Try it out"
3. Ingresa el mismo `voucher_id` (ejemplo: `33`)
4. Click "Execute"
5. Deberías ver un botón **"Download"** en la respuesta
6. Click "Download" para descargar el PDF

**Verificación:**
- Status: 200 OK
- Content-Type: application/pdf
- Archivo descargado: `vale_RFC-SAL-20260115-004.pdf`

#### Paso 6: Verificar Metadata (Opcional)

1. Busca el endpoint **GET /vouchers/{voucher_id}/pdf-metadata**
2. Click "Try it out"
3. Ingresa el voucher_id
4. Click "Execute"

**Respuesta esperada:**
```json
{
  "voucher_id": 33,
  "voucher_folio": "RFC-SAL-20260115-004",
  "file_path": "C:\\...\\voucher_33_20260116_235555.pdf",
  "file_size_bytes": 13773,
  "generated_at": "2026-01-16T23:55:55.122172",
  "expires_at": "2026-01-17T00:55:55.122172",
  "download_url": "/api/vouchers/33/download-pdf"
}
```

---

### Opción 2: Usando curl (Terminal)

#### Flujo Completo con curl

**1. Autenticación:**
```bash
# Login y obtener token
curl -X POST "http://localhost:8001/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alonso.guzman@gpamex.com","password":"root"}' \
  | jq -r '.access_token'

# Guardar token en variable
TOKEN=$(curl -s -X POST "http://localhost:8001/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alonso.guzman@gpamex.com","password":"root"}' \
  | jq -r '.access_token')
```

**2. Listar vouchers:**
```bash
curl -X GET "http://localhost:8001/vouchers/?limit=20" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.vouchers[] | {id, folio, voucher_type, status}'
```

**3. Generar PDF:**
```bash
# Iniciar generación
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8001/vouchers/33/generate-pdf" \
  -H "Authorization: Bearer $TOKEN")

# Extraer task_id
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"
```

**4. Consultar estado:**
```bash
# Consultar estado de la tarea
curl -X GET "http://localhost:8001/vouchers/tasks/$TASK_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{task_id, status, message}'

# Esperar hasta que status sea SUCCESS
# Repetir este comando cada 2-3 segundos
```

**5. Descargar PDF:**
```bash
# Descargar PDF (guarda en archivo local)
curl -X GET "http://localhost:8001/vouchers/33/download-pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -o "vale_33.pdf"

# Verificar que se descargó correctamente
file vale_33.pdf
# Resultado esperado: vale_33.pdf: PDF document, version 1.4
```

**6. Ver metadata:**
```bash
curl -X GET "http://localhost:8001/vouchers/33/pdf-metadata" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

### Script Completo de Prueba (Bash)

Crea un archivo `test_pdf.sh` con el siguiente contenido:

```bash
#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Test de Generación de PDF ===${NC}\n"

# 1. Login
echo -e "${GREEN}1. Autenticación...${NC}"
TOKEN=$(curl -s -X POST "http://localhost:8001/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alonso.guzman@gpamex.com","password":"root"}' \
  | jq -r '.access_token')
echo "Token obtenido: ${TOKEN:0:20}..."

# 2. Generar PDF
echo -e "\n${GREEN}2. Iniciando generación de PDF (voucher 33)...${NC}"
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8001/vouchers/33/generate-pdf" \
  -H "Authorization: Bearer $TOKEN")
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"

# 3. Esperar hasta que termine
echo -e "\n${GREEN}3. Esperando a que termine la generación...${NC}"
for i in {1..10}; do
  STATUS=$(curl -s -X GET "http://localhost:8001/vouchers/tasks/$TASK_ID/status" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.status')

  echo "Intento $i/10 - Status: $STATUS"

  if [ "$STATUS" == "SUCCESS" ]; then
    echo -e "${GREEN}PDF generado exitosamente!${NC}"
    break
  fi

  sleep 2
done

# 4. Descargar PDF
echo -e "\n${GREEN}4. Descargando PDF...${NC}"
curl -X GET "http://localhost:8001/vouchers/33/download-pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -o "vale_33.pdf"

echo -e "\n${GREEN}5. Verificando archivo...${NC}"
if [ -f "vale_33.pdf" ]; then
  SIZE=$(stat -f%z "vale_33.pdf" 2>/dev/null || stat -c%s "vale_33.pdf" 2>/dev/null)
  echo "Archivo descargado: vale_33.pdf ($SIZE bytes)"
else
  echo "Error: No se descargó el archivo"
fi

echo -e "\n${BLUE}=== Test Completado ===${NC}"
```

**Ejecutar:**
```bash
chmod +x test_pdf.sh
./test_pdf.sh
```

---

### Vouchers Recomendados para Prueba

Prueba con diferentes tipos de vouchers para ver los PDFs con diseños distintos:

| Voucher ID | Folio | Tipo | Retorno | Color PDF | Descripción |
|------------|-------|------|---------|-----------|-------------|
| **19** | TES-ENT-2026-0002 | ENTRY | No | VERDE | Entrada de material |
| **28** | RFC-SAL-20260113-001 | EXIT | No | AMARILLO | Salida sin retorno |
| **33** | RFC-SAL-20260115-004 | EXIT | Si | ROJO | Salida con retorno |

**Cada tipo genera un PDF con banda lateral de color diferente.**

---

### Endpoints Disponibles (Resumen)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/vouchers/{id}/generate-pdf` | Inicia generación asíncrona de PDF |
| POST | `/vouchers/{id}/generate-qr` | Inicia generación asíncrona de QR |
| GET | `/vouchers/tasks/{task_id}/status` | Consulta estado de tarea Celery |
| GET | `/vouchers/{id}/download-pdf` | Descarga PDF generado |
| GET | `/vouchers/{id}/pdf-metadata` | Obtiene metadata del PDF |
| GET | `/vouchers/{id}/generation-info` | Info de generación (timestamps) |

---

## Orden de Inicio Recomendado

**Secuencia correcta:**
```
1. Redis    (Docker)
2. API      (FastAPI)
3. Celery   (Worker)
```

**Nota:** El servidor API puede iniciar sin Redis/Celery, pero las funcionalidades de PDF/QR no funcionarán hasta que ambos servicios estén activos.

---

## Solución de Problemas

### Error: "redis.exceptions.ConnectionError"
**Causa:** Redis no está corriendo
**Solución:** Iniciar contenedor Docker de Redis (Paso 1)

### Error: "Address already in use (puerto 8001)"
**Causa:** Ya hay un servidor FastAPI corriendo
**Solución:**
```bash
python scripts.py restart
```

### Error: Celery no procesa tareas
**Causa:** Worker no está corriendo o no se conecta a Redis
**Solución:**
1. Verificar que Redis está corriendo
2. Reiniciar Celery Worker

### Error: "kombu.exceptions.OperationalError"
**Causa:** Celery no puede conectarse a Redis
**Solución:**
1. Verificar que Redis está en puerto 6379
2. Verificar configuración en `app/config/settings.py`:
```python
celery_broker_url = "redis://localhost:6379/0"
celery_result_backend = "redis://localhost:6379/0"
```

---

## URLs Importantes

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Swagger UI** | http://localhost:8001/docs | Documentación interactiva de la API |
| **ReDoc** | http://localhost:8001/redoc | Documentación alternativa |
| **API Health** | http://localhost:8001/ | Endpoint raíz (health check) |

---

## Credenciales de Prueba

**Usuario Admin:**
- **Email:** `admin@bapta.com.mx`
- **Password:** `root`

**Usuario Alonso (Admin):**
- **Email:** `alonso.guzman@gpamex.com`
- **Password:** `root`

---

## Comandos Útiles

### Scripts CLI (scripts.py)

```bash
# Generar claves de seguridad
python scripts.py genkey

# Crear base de datos
python scripts.py createdb

# Iniciar servidor
python scripts.py start

# Reiniciar servidor (mata procesos previos)
python scripts.py restart

# Limpiar base de datos
python scripts.py truncate

# Autodiscovery de permisos
python scripts.py autodiscover

# Ver ayuda
python scripts.py help
```

### Docker Commands (Redis)

```bash
# Ver logs de Redis
docker logs redis-vales

# Ver logs en tiempo real
docker logs -f redis-vales

# Entrar al contenedor (CLI de Redis)
docker exec -it redis-vales redis-cli

# Ver estadísticas de Redis
docker exec redis-vales redis-cli INFO
```

### Celery Commands

```bash
# Ver tareas activas
celery -A app.shared.tasks.celery_app inspect active

# Ver workers registrados
celery -A app.shared.tasks.celery_app inspect registered

# Limpiar todas las tareas pendientes
celery -A app.shared.tasks.celery_app purge
```

---

## Documentación Adicional

- **Patrón de Desarrollo:** `PATRON_DESARROLLO.md`
- **Agregar Entidades:** `ADDING_ENTITIES.md`
- **Implementación Scheduler:** `internal_docs/SCHEDULER_IMPLEMENTATION.md`
- **Casos de Uso:** `../common_use_cases.md`

---

## Ejemplo Completo - Primer Setup

```bash
# Terminal 1: Iniciar Redis
docker run -d --name redis-vales -p 6379:6379 redis:alpine

# Terminal 1: Iniciar API
python scripts.py start

# Terminal 2: Iniciar Celery (nueva terminal)
celery -A app.shared.tasks.celery_app worker --loglevel=info --pool=solo

# Verificar en navegador:
# http://localhost:8001/docs
```

---

**Última actualización:** 2026-01-16
**Autor:** E. Guzman
