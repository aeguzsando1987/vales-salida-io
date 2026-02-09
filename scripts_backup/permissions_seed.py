"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🚨 BACKUP DE EMERGENCIA - SEED DE PERMISOS 🚨                  ║
║                                                                   ║
║   ⚠️  SOLO USAR EN CASO DE EMERGENCIA ⚠️                         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

Versión: 2.0.0
Fecha: 2025-01-06
Última actualización: 2025-01-06

DESCRIPCIÓN:
    Este archivo contiene el estado "conocido como bueno" del sistema
    de permisos. Incluye la configuración completa validada contra
    los casos de uso reales del sistema de vales.

CUÁNDO USAR:
    ✅ Después de truncate que borró plantillas
    ✅ Corrupción de tabla permission_template_items
    ✅ Resetear permisos a estado base
    ✅ Migración a servidor nuevo (si startup falla)

CUÁNDO NO USAR:
    ❌ Operación normal (startup automático lo maneja)
    ❌ Solo faltan algunos permisos (autodiscovery lo resuelve)
    ❌ Cambios menores en matriz (editar init_db.py mejor)

USO:
    python scripts_backup/restore_permissions.py

IMPORTANTE:
    - Este archivo es ESTÁTICO - contiene estado fijo
    - NO se genera dinámicamente
    - Cambios aquí NO afectan init_db.py
    - Es un backup independiente

MAPEO DE ROLES:
    Role 1 (Admin)        = SUPER_ADMIN
    Role 2 (Manager)      = GERENTE
    Role 3 (Collaborator) = SUPERVISOR
    Role 4 (Reader)       = COLABORADOR (Roberto, Paula, Richi)
    Role 5 (Guest)        = INVITADO (deprecated)
    Role 6 (Checker)      = VIGILANCIA (Enrique - escaneo QR)
"""

# ============================================================
# TEMPLATES DE ROLES (6 roles del sistema)
# ============================================================

PERMISSION_TEMPLATES = [
    {
        "role_name": "Admin",
        "description": "Full access - All operations on all entities",
        "is_active": True
    },
    {
        "role_name": "Manager",
        "description": "CRUD on users and entities - Management level access",
        "is_active": True
    },
    {
        "role_name": "Collaborator",
        "description": "CRUD on entities only - No user management",
        "is_active": True
    },
    {
        "role_name": "Reader",
        "description": "Read-only access to all entities",
        "is_active": True
    },
    {
        "role_name": "Guest",
        "description": "Limited read access - Countries and states only",
        "is_active": True
    },
    {
        "role_name": "Checker",
        "description": "Security guard - QR validation and limited read access",
        "is_active": True
    }
]

# ============================================================
# MATRIZ DE PERMISOS POR ROL
# ============================================================
# Formato: (role_name, entity, action, level)
# Niveles: 0=None, 1=Read, 2=Update, 3=Create, 4=Delete
# Scope: "all" (por defecto en todas las asignaciones)
# ============================================================

PERMISSION_MATRIX = [
    # ========== ADMIN (Nivel 4 en todo) ==========
    ("Admin", "vouchers", "create", 4),
    ("Admin", "vouchers", "list", 4),
    ("Admin", "vouchers", "get", 4),
    ("Admin", "vouchers", "update", 4),
    ("Admin", "vouchers", "delete", 4),
    ("Admin", "vouchers", "approve", 4),
    ("Admin", "vouchers", "cancel", 4),
    ("Admin", "vouchers", "validate_exit", 4),
    ("Admin", "vouchers", "confirm_entry", 4),
    ("Admin", "vouchers", "view_logs", 4),
    ("Admin", "vouchers", "search", 4),
    ("Admin", "vouchers", "advanced", 4),
    ("Admin", "vouchers", "generate_pdf", 4),
    ("Admin", "vouchers", "generate_qr", 4),
    ("Admin", "vouchers", "view_statistics", 4),
    ("Admin", "vouchers", "view_tasks", 4),
    ("Admin", "vouchers", "view_generation_info", 4),
    ("Admin", "vouchers", "view_pdf_metadata", 4),
    ("Admin", "vouchers", "validate_qr", 4),
    ("Admin", "vouchers", "scan_qr", 4),
    ("Admin", "vouchers", "maintenance", 4),

    ("Admin", "voucher-details", "create", 4),
    ("Admin", "voucher-details", "get", 4),
    ("Admin", "voucher-details", "list", 4),
    ("Admin", "voucher-details", "update", 4),
    ("Admin", "voucher-details", "delete", 4),
    ("Admin", "voucher-details", "products", 4),
    ("Admin", "voucher-details", "search_products", 4),

    ("Admin", "companies", "create", 4),
    ("Admin", "companies", "list", 4),
    ("Admin", "companies", "get", 4),
    ("Admin", "companies", "update", 4),
    ("Admin", "companies", "delete", 4),

    ("Admin", "branches", "create", 4),
    ("Admin", "branches", "list", 4),
    ("Admin", "branches", "get", 4),
    ("Admin", "branches", "update", 4),
    ("Admin", "branches", "delete", 4),

    ("Admin", "products", "create", 4),
    ("Admin", "products", "list", 4),
    ("Admin", "products", "get", 4),
    ("Admin", "products", "update", 4),
    ("Admin", "products", "delete", 4),

    ("Admin", "individuals", "create", 4),
    ("Admin", "individuals", "list", 4),
    ("Admin", "individuals", "get", 4),
    ("Admin", "individuals", "update", 4),
    ("Admin", "individuals", "delete", 4),

    ("Admin", "users", "create", 4),
    ("Admin", "users", "list", 4),
    ("Admin", "users", "get", 4),
    ("Admin", "users", "update", 4),
    ("Admin", "users", "delete", 4),

    ("Admin", "countries", "list", 4),
    ("Admin", "countries", "get", 4),

    ("Admin", "states", "list", 4),
    ("Admin", "states", "get", 4),

    # ========== MANAGER (Gerente) ==========
    ("Manager", "vouchers", "create", 3),
    ("Manager", "vouchers", "list", 1),
    ("Manager", "vouchers", "get", 1),
    ("Manager", "vouchers", "update", 2),
    ("Manager", "vouchers", "delete", 4),
    ("Manager", "vouchers", "approve", 3),
    ("Manager", "vouchers", "cancel", 3),
    ("Manager", "vouchers", "validate_exit", 3),
    ("Manager", "vouchers", "confirm_entry", 3),
    ("Manager", "vouchers", "view_logs", 1),
    ("Manager", "vouchers", "search", 1),
    ("Manager", "vouchers", "advanced", 1),
    ("Manager", "vouchers", "generate_pdf", 1),
    ("Manager", "vouchers", "generate_qr", 1),
    ("Manager", "vouchers", "view_statistics", 1),
    ("Manager", "vouchers", "view_tasks", 1),
    ("Manager", "vouchers", "view_generation_info", 1),
    ("Manager", "vouchers", "view_pdf_metadata", 1),
    ("Manager", "vouchers", "validate_qr", 4),
    ("Manager", "vouchers", "scan_qr", 3),
    ("Manager", "vouchers", "maintenance", 4),

    ("Manager", "voucher-details", "create", 3),
    ("Manager", "voucher-details", "get", 1),
    ("Manager", "voucher-details", "list", 1),
    ("Manager", "voucher-details", "update", 2),
    ("Manager", "voucher-details", "delete", 4),
    ("Manager", "voucher-details", "products", 1),
    ("Manager", "voucher-details", "search_products", 1),

    ("Manager", "companies", "create", 3),
    ("Manager", "companies", "list", 1),
    ("Manager", "companies", "get", 1),
    ("Manager", "companies", "update", 2),
    ("Manager", "companies", "delete", 4),

    ("Manager", "branches", "create", 3),
    ("Manager", "branches", "list", 1),
    ("Manager", "branches", "get", 1),
    ("Manager", "branches", "update", 2),
    ("Manager", "branches", "delete", 4),

    ("Manager", "products", "create", 3),
    ("Manager", "products", "list", 1),
    ("Manager", "products", "get", 1),
    ("Manager", "products", "update", 2),
    ("Manager", "products", "delete", 4),

    ("Manager", "individuals", "create", 3),
    ("Manager", "individuals", "list", 1),
    ("Manager", "individuals", "get", 1),
    ("Manager", "individuals", "update", 2),
    ("Manager", "individuals", "delete", 4),

    ("Manager", "users", "create", 3),
    ("Manager", "users", "list", 1),
    ("Manager", "users", "get", 1),
    ("Manager", "users", "update", 2),
    ("Manager", "users", "delete", 4),

    ("Manager", "countries", "list", 1),
    ("Manager", "countries", "get", 1),

    ("Manager", "states", "list", 1),
    ("Manager", "states", "get", 1),

    # ========== COLLABORATOR (Supervisor) ==========
    ("Collaborator", "vouchers", "create", 3),
    ("Collaborator", "vouchers", "list", 1),
    ("Collaborator", "vouchers", "get", 1),
    ("Collaborator", "vouchers", "update", 2),
    ("Collaborator", "vouchers", "delete", 0),
    ("Collaborator", "vouchers", "approve", 3),
    ("Collaborator", "vouchers", "cancel", 3),
    ("Collaborator", "vouchers", "validate_exit", 3),
    ("Collaborator", "vouchers", "confirm_entry", 3),
    ("Collaborator", "vouchers", "view_logs", 1),
    ("Collaborator", "vouchers", "search", 1),
    ("Collaborator", "vouchers", "advanced", 1),
    ("Collaborator", "vouchers", "generate_pdf", 1),
    ("Collaborator", "vouchers", "generate_qr", 1),
    ("Collaborator", "vouchers", "view_statistics", 1),
    ("Collaborator", "vouchers", "view_tasks", 1),
    ("Collaborator", "vouchers", "view_generation_info", 1),
    ("Collaborator", "vouchers", "view_pdf_metadata", 1),
    ("Collaborator", "vouchers", "validate_qr", 4),
    ("Collaborator", "vouchers", "scan_qr", 3),
    ("Collaborator", "vouchers", "maintenance", 0),

    ("Collaborator", "voucher-details", "create", 3),
    ("Collaborator", "voucher-details", "get", 1),
    ("Collaborator", "voucher-details", "list", 1),
    ("Collaborator", "voucher-details", "update", 2),
    ("Collaborator", "voucher-details", "delete", 2),
    ("Collaborator", "voucher-details", "products", 1),
    ("Collaborator", "voucher-details", "search_products", 1),

    ("Collaborator", "companies", "create", 0),
    ("Collaborator", "companies", "list", 1),
    ("Collaborator", "companies", "get", 1),
    ("Collaborator", "companies", "update", 2),
    ("Collaborator", "companies", "delete", 0),

    ("Collaborator", "branches", "create", 3),
    ("Collaborator", "branches", "list", 1),
    ("Collaborator", "branches", "get", 1),
    ("Collaborator", "branches", "update", 2),
    ("Collaborator", "branches", "delete", 0),

    ("Collaborator", "products", "create", 3),
    ("Collaborator", "products", "list", 1),
    ("Collaborator", "products", "get", 1),
    ("Collaborator", "products", "update", 2),
    ("Collaborator", "products", "delete", 0),

    ("Collaborator", "individuals", "create", 3),
    ("Collaborator", "individuals", "list", 1),
    ("Collaborator", "individuals", "get", 1),
    ("Collaborator", "individuals", "update", 2),
    ("Collaborator", "individuals", "delete", 0),

    ("Collaborator", "users", "create", 3),
    ("Collaborator", "users", "list", 1),
    ("Collaborator", "users", "get", 1),
    ("Collaborator", "users", "update", 2),
    ("Collaborator", "users", "delete", 0),

    ("Collaborator", "countries", "list", 1),
    ("Collaborator", "countries", "get", 1),

    ("Collaborator", "states", "list", 1),
    ("Collaborator", "states", "get", 1),

    # ========== READER (Colaborador - Roberto, Paula, Richi) ==========
    ("Reader", "vouchers", "create", 3),
    ("Reader", "vouchers", "list", 1),
    ("Reader", "vouchers", "get", 1),
    ("Reader", "vouchers", "update", 2),
    ("Reader", "vouchers", "delete", 0),
    ("Reader", "vouchers", "approve", 0),
    ("Reader", "vouchers", "cancel", 0),
    ("Reader", "vouchers", "validate_exit", 0),
    ("Reader", "vouchers", "confirm_entry", 0),
    ("Reader", "vouchers", "view_logs", 0),
    ("Reader", "vouchers", "search", 1),
    ("Reader", "vouchers", "advanced", 1),
    ("Reader", "vouchers", "generate_pdf", 1),
    ("Reader", "vouchers", "generate_qr", 1),
    ("Reader", "vouchers", "view_statistics", 1),
    ("Reader", "vouchers", "view_tasks", 1),
    ("Reader", "vouchers", "view_generation_info", 1),
    ("Reader", "vouchers", "view_pdf_metadata", 1),
    ("Reader", "vouchers", "validate_qr", 4),
    ("Reader", "vouchers", "scan_qr", 0),
    ("Reader", "vouchers", "maintenance", 0),

    ("Reader", "voucher-details", "create", 3),
    ("Reader", "voucher-details", "get", 1),
    ("Reader", "voucher-details", "list", 1),
    ("Reader", "voucher-details", "update", 2),
    ("Reader", "voucher-details", "delete", 2),
    ("Reader", "voucher-details", "products", 1),
    ("Reader", "voucher-details", "search_products", 1),

    ("Reader", "companies", "create", 0),
    ("Reader", "companies", "list", 1),
    ("Reader", "companies", "get", 1),
    ("Reader", "companies", "update", 0),
    ("Reader", "companies", "delete", 0),

    ("Reader", "branches", "create", 0),
    ("Reader", "branches", "list", 1),
    ("Reader", "branches", "get", 1),
    ("Reader", "branches", "update", 0),
    ("Reader", "branches", "delete", 0),

    ("Reader", "products", "create", 3),
    ("Reader", "products", "list", 1),
    ("Reader", "products", "get", 1),
    ("Reader", "products", "update", 0),
    ("Reader", "products", "delete", 0),

    ("Reader", "individuals", "create", 0),
    ("Reader", "individuals", "list", 1),
    ("Reader", "individuals", "get", 1),
    ("Reader", "individuals", "update", 0),
    ("Reader", "individuals", "delete", 0),

    ("Reader", "users", "create", 0),
    ("Reader", "users", "list", 0),
    ("Reader", "users", "get", 0),
    ("Reader", "users", "update", 0),
    ("Reader", "users", "delete", 0),

    ("Reader", "countries", "list", 1),
    ("Reader", "countries", "get", 1),

    ("Reader", "states", "list", 1),
    ("Reader", "states", "get", 1),

    # ========== GUEST (Acceso mínimo - Deprecated) ==========
    ("Guest", "countries", "list", 0),
    ("Guest", "countries", "get", 0),

    ("Guest", "states", "list", 0),
    ("Guest", "states", "get", 0),

    # ========== CHECKER (Vigilancia - Enrique) ==========
    # CRÍTICO: Checker DEBE tener nivel 3 en validate_exit y confirm_entry
    ("Checker", "vouchers", "create", 0),
    ("Checker", "vouchers", "list", 1),
    ("Checker", "vouchers", "get", 1),
    ("Checker", "vouchers", "update", 0),
    ("Checker", "vouchers", "delete", 0),
    ("Checker", "vouchers", "approve", 0),
    ("Checker", "vouchers", "cancel", 0),
    ("Checker", "vouchers", "validate_exit", 3),  # ← CRÍTICO
    ("Checker", "vouchers", "confirm_entry", 3),  # ← CRÍTICO
    ("Checker", "vouchers", "view_logs", 0),
    ("Checker", "vouchers", "search", 1),
    ("Checker", "vouchers", "advanced", 1),
    ("Checker", "vouchers", "generate_pdf", 0),
    ("Checker", "vouchers", "generate_qr", 0),
    ("Checker", "vouchers", "view_statistics", 0),
    ("Checker", "vouchers", "view_tasks", 0),
    ("Checker", "vouchers", "view_generation_info", 0),
    ("Checker", "vouchers", "view_pdf_metadata", 0),
    ("Checker", "vouchers", "validate_qr", 4),
    ("Checker", "vouchers", "scan_qr", 3),
    ("Checker", "vouchers", "maintenance", 0),

    ("Checker", "voucher-details", "create", 0),
    ("Checker", "voucher-details", "get", 1),
    ("Checker", "voucher-details", "list", 1),
    ("Checker", "voucher-details", "update", 0),
    ("Checker", "voucher-details", "delete", 0),
    ("Checker", "voucher-details", "products", 1),
    ("Checker", "voucher-details", "search_products", 1),

    ("Checker", "companies", "create", 0),
    ("Checker", "companies", "list", 1),
    ("Checker", "companies", "get", 1),
    ("Checker", "companies", "update", 0),
    ("Checker", "companies", "delete", 0),

    ("Checker", "branches", "create", 0),
    ("Checker", "branches", "list", 1),
    ("Checker", "branches", "get", 1),
    ("Checker", "branches", "update", 0),
    ("Checker", "branches", "delete", 0),

    ("Checker", "products", "create", 0),
    ("Checker", "products", "list", 1),
    ("Checker", "products", "get", 1),
    ("Checker", "products", "update", 0),
    ("Checker", "products", "delete", 0),

    ("Checker", "individuals", "create", 0),
    ("Checker", "individuals", "list", 1),
    ("Checker", "individuals", "get", 1),
    ("Checker", "individuals", "update", 0),
    ("Checker", "individuals", "delete", 0),

    ("Checker", "users", "create", 0),
    ("Checker", "users", "list", 0),
    ("Checker", "users", "get", 0),
    ("Checker", "users", "update", 0),
    ("Checker", "users", "delete", 0),

    ("Checker", "countries", "list", 1),
    ("Checker", "countries", "get", 1),

    ("Checker", "states", "list", 1),
    ("Checker", "states", "get", 1),
]

# Scope por defecto para todas las asignaciones
DEFAULT_SCOPE = "all"

# Niveles por defecto si permiso no está en matriz
DEFAULT_PERMISSION_LEVELS = {
    "Admin": 4,
    "Manager": 3,
    "Collaborator": 2,
    "Reader": 1,
    "Guest": 0,
    "Checker": 1
}
