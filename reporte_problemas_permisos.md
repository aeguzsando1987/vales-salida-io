# Reporte de Problemas de Permisos - Pruebas Manuales
**Fecha:** 2025-12-22
**Fuente:** Pruebas manuales basadas en common_use_cases.md

---

## IMPORTANTE: Mapeo de Roles

Según CLAUDE.md sección 3.4:

| Especificación | Plantilla Base | Role ID | Descripción |
|----------------|----------------|---------|-------------|
| SUPER_ADMIN | **Admin** | **1** | Acceso total |
| GERENTE | **Manager** | **2** | CRUD completo, gestiona usuarios |
| SUPERVISOR | **Collaborator** | **3** | CRUD vales, aprueba, registra entradas |
| COLABORADOR | **Reader** | **4** | Crea vales propios, lectura general |
| CHECKER | **Checker** | **6** | Solo escaneo QR y lectura vales |

**NOTA CRÍTICA:** En las plantillas de permisos:
- `Collaborator` = SUPERVISOR (no trabajador)
- `Reader` = COLABORADOR (Roberto, Paula, Valerie, Richi)

---

## Resumen Ejecutivo

**Total de pruebas:** 17
**Exitosas:** 13 (76.5%)
**Fallidas:** 4 (23.5%)

### Problemas Críticos Encontrados

| # | Problema | Severidad | Impacto |
|---|----------|-----------|---------|
| 1 | Checker NO tiene permiso `validate_exit` | 🔴 CRÍTICO | Bloquea flujo de validación de salidas |
| 2 | Voucher-details devuelve respuesta incorrecta | 🟡 MEDIO | Afecta creación de detalles en algunos casos |
| 3 | Individual ID 4 no existe | 🟡 MEDIO | Bloquea Caso 4 (Solo Entrada) |
| 4 | Usuario "collaborator@test.com" tiene role=4 (Reader) | 🟡 MEDIO | Se está usando como Colaborador, debería ser Supervisor |

---

## Problema #1: Checker SIN Permisos para validate_exit 🔴 CRÍTICO

### Error Encontrado
```json
POST /vouchers/8/validate-exit - Status 403
{
  "detail": "Permiso insuficiente para vouchers:validate_exit.
  Requiere nivel 3, tienes nivel 0"
}
```

### Impacto
- **Flujo bloqueado:** Caso 1 (Salida con Retorno) - Paso 4
- **Flujo bloqueado:** Caso 2 (Salida sin Retorno) - Paso 4
- **Usuario afectado:** Checker/Vigilancia (checker@gpamex.com)

### Quiénes DEBEN poder hacer validate_exit

Según el usuario:
- ✅ **Admin (role=1)** - Puede todo
- ✅ **Manager (role=2)** - Gerente puede validar salidas
- ✅ **Collaborator (role=3 = SUPERVISOR)** - Supervisor puede validar salidas
- ❌ **Reader (role=4 = COLABORADOR)** - NO puede validar salidas
- ✅ **Checker (role=6)** - DEBE poder validar salidas (es su función principal)

### Causa Raíz
Template de permisos de Checker tiene nivel 0 en `vouchers:validate_exit`.

**Nivel actual:** 0 (Sin acceso)
**Nivel requerido:** 3 (Create)

### Solución
Actualizar plantilla de permisos para rol Checker:

```sql
UPDATE permission_template_items
SET permission_level = 3
WHERE template_id = (SELECT id FROM permission_templates WHERE role_name = 'Checker')
  AND permission_id = (SELECT id FROM permissions WHERE entity = 'vouchers' AND action = 'validate_exit');
```

---

## Problema #2: Voucher-Details Devuelve Respuesta Incorrecta 🟡 MEDIO

### Error Encontrado
```
POST /voucher-details/ - Status 201 (OK)
Pero respuesta NO contiene campo 'id'
```

### Impacto
- **Flujo afectado:** Caso 1 (Salida con Retorno) - Paso 2
- **Consecuencia:** No se pueden crear validaciones línea por línea (no hay detail_id)

### Causa Probable
1. Backend devuelve objeto sin campo `id` después de crear
2. Schema de respuesta (VoucherDetailResponse) no incluye `id`
3. Serialización incorrecta en controller

### Solución
Investigar en:
- `app/entities/voucher_details/schemas/voucher_detail_schemas.py` - Verificar VoucherDetailResponse
- `app/entities/voucher_details/controllers/voucher_detail_controller.py` - Verificar return del método create
- `app/entities/voucher_details/routers/voucher_detail_router.py` - Verificar response_model

**NOTA:** Este problema NO es de permisos, es de implementación del backend.

---

## Problema #3: Individual ID 4 No Existe 🟡 MEDIO

### Error Encontrado
```json
POST /vouchers/ - Status 404
{
  "detail": "Individual con ID 4 no encontrado"
}
```

### Impacto
- **Flujo bloqueado:** Caso 4 (Solo Entrada) - Paso 1
- **Usuario afectado:** Richi (Collaborator que entrega equipo de home office)

### Solución Recomendada
Crear 4 Individuals de prueba para los 4 casos de uso:
- ID 1: Roberto (Reader=Colaborador - Salida con retorno)
- ID 2: Paula (Reader=Colaborador - Salida sin retorno)
- ID 3: Valerie (Reader=Colaborador - Translado intercompañías)
- ID 4: Richi (Reader=Colaborador - Solo entrada)

**NOTA:** Este problema NO es de permisos, es de datos de prueba faltantes.

---

## Problema #4: Confusión de Roles en Usuarios de Prueba 🟡 MEDIO

### Problema
El usuario `collaborator@test.com` tiene role=4 (Reader = COLABORADOR en especificación).

Pero en los casos de uso, el flujo completo requiere:
1. **Colaborador (Reader)** - Crea vale
2. **Gerente/Supervisor (Manager/Collaborator)** - Aprueba vale
3. **Checker (Checker)** - Valida salida
4. **Gerente/Supervisor (Manager/Collaborator)** - Confirma entrada

### Usuarios de Prueba Correctos

| Email | Role ID | Nombre Plantilla | Rol Especificación | Uso en Pruebas |
|-------|---------|------------------|---------------------|----------------|
| admin@test.com | 1 | Admin | SUPER_ADMIN | Todo |
| manager@test.com | 2 | Manager | GERENTE | Aprobar, confirmar entrada |
| supervisor@test.com | 3 | Collaborator | SUPERVISOR | Aprobar, confirmar entrada |
| collaborator@test.com | 4 | Reader | COLABORADOR | Crear vales (Roberto, Paula, etc.) |
| checker@gpamex.com | 6 | Checker | CHECKER | Validar salidas |

**Conclusión:** Los usuarios de prueba están correctos. El problema es solo que Checker no tiene permisos.

---

## Análisis de Permisos Correctos vs Actuales

### Vouchers - Acción: validate_exit

| Rol | Nombre Plantilla | Nivel Correcto | Nivel Actual | Estado |
|-----|------------------|----------------|--------------|--------|
| Admin (1) | Admin | 4 | 4 | ✅ OK |
| Manager (2) | Manager | 3 | 4 | ⚠️ MAYOR (funciona pero innecesario) |
| Supervisor (3) | Collaborator | 3 | ? | ❓ Falta verificar |
| Colaborador (4) | Reader | 0 | ? | ❓ Falta verificar |
| Checker (6) | Checker | **3** | **0** | ❌ BLOQUEADOR |

### Vouchers - Acción: confirm_entry

| Rol | Nombre Plantilla | Nivel Correcto | Nivel Actual | Estado |
|-----|------------------|----------------|--------------|--------|
| Admin (1) | Admin | 4 | 4 | ✅ OK |
| Manager (2) | Manager | 3 | 4 | ⚠️ MAYOR (funciona) |
| Supervisor (3) | Collaborator | 3 | ? | ❓ Falta verificar |
| Colaborador (4) | Reader | 0 | ? | ❓ Falta verificar |
| Checker (6) | Checker | **3** | ? | ❓ Falta verificar |

### Vouchers - Acción: approve

| Rol | Nombre Plantilla | Nivel Correcto | Nivel Actual | Estado |
|-----|------------------|----------------|--------------|--------|
| Admin (1) | Admin | 4 | 4 | ✅ OK |
| Manager (2) | Manager | 3 | 4 | ✅ OK (funciona) |
| Supervisor (3) | Collaborator | 3 | ? | ❓ Falta verificar |
| Colaborador (4) | Reader | 0 | ? | ❓ Falta verificar |
| Checker (6) | Checker | 0 | ? | ❓ Falta verificar |

---

## Flujos Validados

### Caso 1: Salida con Retorno
- [x] Paso 1: Crear vale EXIT (Colaborador/Reader) ✅
- [ ] Paso 2: Agregar detalles ❌ (Problema #2 - no de permisos)
- [x] Paso 3: Aprobar vale (Gerente/Manager) ✅
- [ ] Paso 4: Validar salida (Checker) ❌ (Problema #1 - SIN PERMISOS)
- [x] Paso 5: Confirmar entrada (Gerente/Manager) ✅

### Caso 2: Salida sin Retorno
- [x] Paso 1: Crear vale EXIT sin retorno (Colaborador/Reader) ✅
- [x] Paso 2: Agregar detalle ✅
- [x] Paso 3: Aprobar vale (Gerente/Manager) ✅
- [ ] Paso 4: Validar salida → CLOSED (Checker) ❌ (Problema #1 - SIN PERMISOS)

### Caso 4: Solo Entrada
- [ ] Paso 1: Crear vale ENTRY ❌ (Problema #3 - Individual no existe)

---

## Matriz de Permisos Completa - VOUCHERS

Según `analisis_permisos_por_caso_uso.md` y corrección del usuario:

| Acción | Admin (1) | Manager (2) | Supervisor (3) | Colaborador (4) | Checker (6) |
|--------|-----------|-------------|----------------|-----------------|-------------|
| | **Admin** | **Manager** | **Collaborator** | **Reader** | **Checker** |
| create | 4 | 3 | 3 | 3 | 0 |
| list | 4 | 1 | 1 | 1 | 1 |
| get | 4 | 1 | 1 | 1 | 1 |
| update | 4 | 2 | 2 | 2 | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |
| approve | 4 | 3 | 3 | 0 | 0 |
| cancel | 4 | 3 | 3 | 0 | 0 |
| **validate_exit** | 4 | 3 | **3** | 0 | **3** |
| **confirm_entry** | 4 | 3 | **3** | 0 | **3** |
| view_logs | 4 | 1 | 1 | 0 | 0 |
| search | 4 | 1 | 1 | 1 | 1 |
| generate_pdf | 4 | 1 | 1 | 1 | 0 |
| generate_qr | 4 | 1 | 1 | 1 | 0 |

**Roles que PUEDEN validar salidas y confirmar entradas:**
- ✅ Admin (todo)
- ✅ Manager (Gerente)
- ✅ Collaborator = Supervisor (role=3)
- ✅ Checker (Vigilancia)

**Roles que NO pueden:**
- ❌ Reader = Colaborador (role=4) - Solo crean vales

---

## Acciones Requeridas

### Prioridad 1 - CRÍTICO 🔴
1. **Arreglar permisos de Checker**
   - `validate_exit`: Cambiar nivel de 0 a 3
   - `confirm_entry`: Cambiar nivel de 0 a 3

   **SQL:**
   ```sql
   UPDATE permission_template_items pti
   SET permission_level = 3
   WHERE template_id = (SELECT id FROM permission_templates WHERE role_name = 'Checker')
     AND permission_id IN (
       SELECT id FROM permissions
       WHERE entity = 'vouchers'
       AND action IN ('validate_exit', 'confirm_entry')
     );
   ```

### Prioridad 2 - IMPORTANTE 🟡
2. **Crear Individuals de prueba**
   - Crear IDs 1-4 para Roberto, Paula, Valerie, Richi

3. **Investigar respuesta de voucher-details**
   - Verificar que devuelva objeto completo con `id`

### Prioridad 3 - VALIDACIÓN 🟢
4. **Ejecutar seed script de permisos (RECOMENDADO)**
   - Recrear TODAS las plantillas de permisos
   - Garantizar consistencia total

5. **Re-ejecutar pruebas manuales**
   ```bash
   python test_manual_use_cases.py
   ```

---

## Recomendación Final

**Opción 1 (RÁPIDA):** Ejecutar SQL para arreglar solo Checker:
```bash
python -c "from database import SessionLocal; from app.shared.models.permission import *; db = SessionLocal(); # ejecutar UPDATE de arriba"
```

**Opción 2 (COMPLETA - RECOMENDADA):** Ejecutar seed script:
```bash
python seed_permissions_from_use_cases.py --force
```

**Luego:**
```bash
python test_manual_use_cases.py
```

**Resultado esperado:** 100% de pruebas exitosas (excepto Problema #2 y #3 que no son de permisos).
