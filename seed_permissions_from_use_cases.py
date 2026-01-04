"""
Seed de Permisos Basado en Casos de Uso
=========================================

Este script recrea las plantillas de permisos basandose en el analisis
de common_use_cases.md documentado en analisis_permisos_por_caso_uso.md

IMPORTANTE: Mapeo de Roles
- Admin (role=1) = SUPER_ADMIN
- Manager (role=2) = GERENTE
- Collaborator (role=3) = SUPERVISOR (NO trabajador)
- Reader (role=4) = COLABORADOR (Roberto, Paula, Valerie, Richi)
- Checker (role=6) = VIGILANCIA (Enrique)

Uso:
    python seed_permissions_from_use_cases.py [--dry-run] [--force]

Flags:
    --dry-run: Muestra cambios sin aplicarlos
    --force: Elimina y recrea todas las asignaciones de permisos
"""

import sys
import os
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal
from app.shared.models.permission import Permission
from app.shared.models.permission_template import PermissionTemplate
from app.shared.models.permission_template_item import PermissionTemplateItem

# ========================================================================
# MATRIZ DE PERMISOS EXTRAIDA DE CASOS DE USO
# ========================================================================

# NOMBRES DE ROLES EN PLANTILLA BASE
#   Admin = SUPER_ADMIN (role=1)
#   Manager = GERENTE (role=2)
#   Collaborator = SUPERVISOR (role=3) ← NO trabajador!
#   Reader = COLABORADOR (role=4) ← Roberto, Paula, Valerie, Richi
#   Checker = VIGILANCIA (role=6)

PERMISSION_MATRIX = {
    # === VOUCHERS ===
    'vouchers': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 3, 'Guest': 0, 'Checker': 0},
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 2, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        # Acciones de workflow
        'approve': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'cancel': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'validate_exit': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 3},  # ← Checker DEBE tener 3
        'confirm_entry': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 3},  # ← Checker DEBE tener 3
        'view_logs': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        # Búsqueda
        'search': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'advanced': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        # Generación de documentos
        'generate_pdf': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
        'generate_qr': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
        'view_statistics': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
        'view_tasks': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
        'view_generation_info': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
        'view_pdf_metadata': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
        'scan_qr': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 3},
        'maintenance': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
    },

    # === VOUCHER-DETAILS ===
    'voucher-details': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 3, 'Guest': 0, 'Checker': 0},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 2, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 2, 'Reader': 2, 'Guest': 0, 'Checker': 0},
        'products': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'search_products': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
    },

    # === COMPANIES ===
    'companies': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},  # Solo Admin/Manager
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},  # Solo Admin/Manager
    },

    # === BRANCHES ===
    'branches': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},  # Admin/Manager/Supervisor
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},  # Solo Admin/Manager
    },

    # === PRODUCTS ===
    'products': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 3, 'Guest': 0, 'Checker': 0},
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
    },

    # === INDIVIDUALS ===
    'individuals': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
    },

    # === USERS ===
    'users': {
        'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
    },

    # === COUNTRIES (solo lectura) ===
    'countries': {
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
    },

    # === STATES (solo lectura) ===
    'states': {
        'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
    },
}

# ========================================================================
# FUNCIONES DE SEED
# ========================================================================

def get_or_create_permission(db: Session, entity: str, action: str) -> Permission:
    """Busca o crea un permiso."""
    perm = db.query(Permission).filter(
        Permission.entity == entity,
        Permission.action == action
    ).first()

    if not perm:
        perm = Permission(
            entity=entity,
            action=action,
            endpoint=f"/{entity}/{action}",
            http_method="*",
            description=f"{action.capitalize()} {entity}",
            is_active=True
        )
        db.add(perm)
        db.flush()
        print(f"  [+] Permiso creado: {entity}:{action}")

    return perm


def seed_permissions_from_matrix(db: Session, dry_run: bool = False, force: bool = False):
    """
    Aplica la matriz de permisos a las plantillas.

    Args:
        db: Session de base de datos
        dry_run: Solo muestra cambios sin aplicarlos
        force: Elimina y recrea todas las asignaciones
    """

    print("="*70)
    print("SEED DE PERMISOS BASADO EN CASOS DE USO")
    print("="*70)
    print()
    print("MAPEO DE ROLES:")
    print("  Admin (role=1) = SUPER_ADMIN")
    print("  Manager (role=2) = GERENTE")
    print("  Collaborator (role=3) = SUPERVISOR (NO trabajador)")
    print("  Reader (role=4) = COLABORADOR (Roberto, Paula, Valerie, Richi)")
    print("  Checker (role=6) = VIGILANCIA (Enrique)")
    print()

    if dry_run:
        print("[INFO] MODO DRY RUN - No se aplicaran cambios")
        print()

    if force and not dry_run:
        print("[WARN] MODO FORCE - Eliminando asignaciones existentes...")
        db.query(PermissionTemplateItem).delete()
        db.commit()
        print("[OK] Asignaciones eliminadas")
        print()

    # Obtener templates
    templates = {t.role_name: t for t in db.query(PermissionTemplate).all()}

    if not templates:
        print("[ERROR] No hay templates de roles en la base de datos")
        print("[INFO] Ejecuta primero: python scripts.py start (para crear templates)")
        return

    print(f"[INFO] Templates encontrados: {list(templates.keys())}")
    print()

    stats = {
        'permisos_procesados': 0,
        'asignaciones_creadas': 0,
        'asignaciones_actualizadas': 0,
        'asignaciones_sin_cambios': 0,
    }

    # Procesar matriz
    for entity, actions in PERMISSION_MATRIX.items():
        print(f"[*] Procesando entidad: {entity}")

        for action, role_levels in actions.items():
            # Obtener o crear permiso
            if not dry_run:
                perm = get_or_create_permission(db, entity, action)
                stats['permisos_procesados'] += 1
            else:
                # En dry-run, buscar si existe
                perm = db.query(Permission).filter(
                    Permission.entity == entity,
                    Permission.action == action
                ).first()

                if not perm:
                    print(f"  [DRY] Permiso a crear: {entity}:{action}")
                    stats['permisos_procesados'] += 1
                    continue

            # Asignar a cada rol
            for role_name, level in role_levels.items():
                if role_name not in templates:
                    print(f"  [WARN] Template no encontrado: {role_name}")
                    continue

                template = templates[role_name]

                if not dry_run:
                    # Buscar asignacion existente
                    existing = db.query(PermissionTemplateItem).filter(
                        PermissionTemplateItem.template_id == template.id,
                        PermissionTemplateItem.permission_id == perm.id
                    ).first()

                    if existing:
                        if existing.permission_level != level:
                            print(f"  [U] {entity}:{action} -> {role_name}: {existing.permission_level} => {level}")
                            existing.permission_level = level
                            stats['asignaciones_actualizadas'] += 1
                        else:
                            stats['asignaciones_sin_cambios'] += 1
                    else:
                        item = PermissionTemplateItem(
                            template_id=template.id,
                            permission_id=perm.id,
                            permission_level=level
                        )
                        db.add(item)
                        print(f"  [+] {entity}:{action} -> {role_name}: nivel {level}")
                        stats['asignaciones_creadas'] += 1
                else:
                    print(f"  [DRY] {entity}:{action} -> {role_name}: nivel {level}")

        print()

    # Commit
    if not dry_run:
        db.commit()
        print("[OK] Cambios guardados en base de datos")
    else:
        print("[INFO] Modo dry-run - No se guardaron cambios")

    # Resumen
    print()
    print("="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Permisos procesados: {stats['permisos_procesados']}")

    if not dry_run:
        print(f"Asignaciones creadas: {stats['asignaciones_creadas']}")
        print(f"Asignaciones actualizadas: {stats['asignaciones_actualizadas']}")
        print(f"Asignaciones sin cambios: {stats['asignaciones_sin_cambios']}")
        print(f"TOTAL: {stats['asignaciones_creadas'] + stats['asignaciones_actualizadas'] + stats['asignaciones_sin_cambios']}")
    print()


def main():
    """Punto de entrada del script."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed de permisos basado en casos de uso")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar cambios sin aplicarlos")
    parser.add_argument("--force", action="store_true", help="Eliminar y recrear todas las asignaciones")
    args = parser.parse_args()

    if args.force and args.dry_run:
        print("[ERROR] No puedes usar --force con --dry-run")
        sys.exit(1)

    if args.force:
        confirm = input("ADVERTENCIA: Esto eliminara TODAS las asignaciones de permisos. Escribe 'CONFIRMAR' para continuar: ")
        if confirm != "CONFIRMAR":
            print("[INFO] Operacion cancelada")
            sys.exit(0)

    db = SessionLocal()
    try:
        seed_permissions_from_matrix(db, dry_run=args.dry_run, force=args.force)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
