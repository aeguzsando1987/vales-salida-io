# Análisis de Permisos Basado en Casos de Uso

## Roles del Sistema

1. **Admin (role=1)** - Super Admin, acceso total
2. **Manager (role=2)** - Gerente, gestión completa
3. **Supervisor (role=3)** - Supervisor, gestión operativa
4. **Collaborator (role=4)** - Trabajador (Roberto, Paula, Valerie, Richi)
5. **Guest (role=5)** - Sin uso en casos de uso
6. **Checker (role=6)** - Vigilancia (Enrique), validación QR

---

## Análisis por Caso de Uso

### CASO 1: Salida con Retorno (Roberto - Collaborator)

**Actores:**
- Roberto (Collaborator) - Crea vale
- Gerente/Supervisor (Manager/Supervisor) - Aprueba vale
- Vigilancia (Checker) - Valida salida y retorno

**Endpoints y permisos:**

1. **POST /vouchers/** - Crear vale
   - Collaborator: ✅ nivel 3 (Create)
   - Manager: ✅ nivel 3 (Create)
   - Supervisor: ✅ nivel 3 (Create)
   - Checker: ❌ nivel 0 (No crea vales)

2. **POST /voucher-details/** - Agregar líneas
   - Collaborator: ✅ nivel 3 (Create)
   - Manager: ✅ nivel 3 (Create)
   - Supervisor: ✅ nivel 3 (Create)
   - Checker: ❌ nivel 0

3. **POST /vouchers/{id}/approve** - Aprobar vale
   - Collaborator: ❌ nivel 0 (No aprueba)
   - Manager: ✅ nivel 3 (Approve)
   - Supervisor: ✅ nivel 3 (Approve)
   - Checker: ❌ nivel 0

4. **POST /vouchers/{id}/validate-exit** - Validar salida
   - Collaborator: ❌ nivel 0
   - Manager: ✅ nivel 3 (Puede validar)
   - Supervisor: ✅ nivel 3 (Puede validar)
   - Checker: ✅ nivel 3 (Función principal)

5. **POST /vouchers/{id}/confirm-entry** - Confirmar entrada
   - Collaborator: ❌ nivel 0
   - Manager: ✅ nivel 3 (Confirma entrada)
   - Supervisor: ✅ nivel 3 (Confirma entrada)
   - Checker: ✅ nivel 3 (Puede confirmar)

6. **GET /vouchers/** - Listar vales
   - Collaborator: ✅ nivel 1 (Solo propios)
   - Manager: ✅ nivel 1 (Todos)
   - Supervisor: ✅ nivel 1 (Todos)
   - Checker: ✅ nivel 1 (Aprobados y pendientes)

7. **GET /vouchers/{id}/logs** - Ver bitácora
   - Collaborator: ❌ nivel 0 (Privado)
   - Manager: ✅ nivel 1 (Ver logs)
   - Supervisor: ✅ nivel 1 (Ver logs)
   - Checker: ❌ nivel 0

---

### CASO 2: Salida sin Retorno (Paula - Collaborator)

**Mismo flujo que Caso 1**, Paula usa los mismos permisos que Roberto.

---

### CASO 3: Translado Intercompañías (Valerie - Collaborator)

**Mismo flujo que Caso 1**, con campos adicionales (origin_branch, destination_branch).

---

### CASO 4: Solo Entrada (Richi - Collaborator)

**Actores:**
- Richi (Collaborator) - Crea vale ENTRY
- Gerente/Supervisor (Manager/Supervisor) - Confirma entrada (NO aprueba)

**Endpoints:**

1. **POST /vouchers/** - Crear vale ENTRY
   - Collaborator: ✅ nivel 3

2. **POST /vouchers/{id}/confirm-entry** - Confirmar entrada
   - Manager: ✅ nivel 3
   - Supervisor: ✅ nivel 3

**Nota:** ENTRY no pasa por aprobación explícita (línea 72 del archivo)

---

### CASO 5: Consultas (Sección "Consultas y manejo de datos")

**Roberto (Collaborator):**
- Ver solo sus vales actuales y históricos ✅
- Ver si fueron aprobados o cancelados ✅
- NO puede ver vales de otros ❌

**Gerente (Manager):**
- Ver todos los vales ✅
- Aprobar, cancelar, analizar ✅
- Eliminar (softdelete) ✅
- Actualizar ✅
- Crear empresas y sucursales ✅
- Eliminar empresas y sucursales ✅

**Supervisor:**
- Ver todos los vales ✅
- Aprobar, cancelar, analizar ✅
- Actualizar ✅
- Crear sucursales (NO empresas) ✅
- NO eliminar empresas ni sucursales ❌

**Vigilante (Checker):**
- Consultar vales aprobados ✅
- Consultar vales pendientes ✅
- Tareas de validación (QR) ✅
- NO crear vales ❌

**Super Admin:**
- Todo (CRUD completo) ✅

---

## Matriz de Permisos por Entidad

### VOUCHERS

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 3 | 3 | 0 |
| list | 4 | 1 | 1 | 1 (own) | 1 |
| get | 4 | 1 | 1 | 1 (own) | 1 |
| update | 4 | 2 | 2 | 2 (own) | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |
| approve | 4 | 3 | 3 | 0 | 0 |
| cancel | 4 | 3 | 3 | 0 | 0 |
| validate_exit | 4 | 3 | 3 | 0 | 3 |
| confirm_entry | 4 | 3 | 3 | 0 | 3 |
| view_logs | 4 | 1 | 1 | 0 | 0 |
| search | 4 | 1 | 1 | 1 | 1 |
| generate_pdf | 4 | 1 | 1 | 1 (own) | 0 |
| generate_qr | 4 | 1 | 1 | 1 (own) | 0 |

### VOUCHER-DETAILS

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 3 | 3 | 0 |
| get | 4 | 1 | 1 | 1 | 1 |
| update | 4 | 2 | 2 | 2 (own) | 0 |
| delete | 4 | 4 | 2 | 2 (own) | 0 |
| products | 4 | 1 | 1 | 1 | 1 |

### COMPANIES

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 0 | 0 | 0 |
| list | 4 | 1 | 1 | 1 | 1 |
| get | 4 | 1 | 1 | 1 | 1 |
| update | 4 | 2 | 2 | 0 | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |

### BRANCHES

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 3 | 0 | 0 |
| list | 4 | 1 | 1 | 1 | 1 |
| get | 4 | 1 | 1 | 1 | 1 |
| update | 4 | 2 | 2 | 0 | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |

### PRODUCTS

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 3 | 3 | 0 |
| list | 4 | 1 | 1 | 1 | 1 |
| get | 4 | 1 | 1 | 1 | 1 |
| update | 4 | 2 | 2 | 0 | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |

### INDIVIDUALS

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 3 | 0 | 0 |
| list | 4 | 1 | 1 | 1 | 1 |
| get | 4 | 1 | 1 | 1 | 1 |
| update | 4 | 2 | 2 | 0 | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |

### USERS (Creación de usuarios - línea 62)

| Acción | Admin | Manager | Supervisor | Collaborator | Checker |
|--------|-------|---------|------------|--------------|---------|
| create | 4 | 3 | 3 | 0 | 0 |
| list | 4 | 1 | 1 | 0 | 0 |
| get | 4 | 1 | 1 | 0 | 0 |
| update | 4 | 2 | 2 | 0 | 0 |
| delete | 4 | 4 | 0 | 0 | 0 |

**Nota:** Manager puede crear Collaborators, Supervisors, Checkers. Supervisor puede crear Collaborators y Checkers.

---

## Scope (all vs own)

- **Collaborators** solo ven/modifican sus propios vales (scope=own)
- **Manager/Supervisor** ven/modifican todos los vales (scope=all)
- **Checker** ve todos los vales pero solo para validación (scope=all, pero read-only en mayoría)

---

## Permisos que NO deben existir

- **Collaborator** NO puede:
  - Aprobar vales
  - Cancelar vales
  - Ver logs de bitácora
  - Eliminar empresas/sucursales/productos
  - Ver/gestionar usuarios
  - Validar salidas/entradas (es trabajo de Checker/Manager/Supervisor)

- **Checker** NO puede:
  - Crear vales
  - Aprobar/cancelar vales
  - Crear/modificar empresas/sucursales/productos
  - Ver logs de bitácora
  - Gestionar usuarios

- **Supervisor** NO puede:
  - Crear empresas (solo Manager)
  - Eliminar empresas/sucursales (solo Manager/Admin)
  - Gestionar permisos de usuarios (solo Admin)

---

## Endpoints Admin (solo Admin)

Toda la entidad `/admin/user-permissions/*` es SOLO para Admin:
- grant
- delete
- list
- extend
- cleanup
- levels

---

## Resumen de Cambios Necesarios

1. **Checker debe tener role=6** (actualmente tiene role=5 Guest)
2. **Voucher-details:products** debe ser accesible para todos (nivel 1)
3. **Supervisor NO debe poder eliminar** companies, branches, products
4. **Collaborator NO debe poder** crear/modificar companies, branches, individuals (solo productos y vales)
5. **Admin permissions** deben ser SOLO para Admin (nivel 4), Manager/Supervisor/Collaborator nivel 0
