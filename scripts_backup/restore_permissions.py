"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🚨 RESTORE DE EMERGENCIA - PERMISOS 🚨                         ║
║                                                                   ║
║   ⚠️  SOLO USAR EN CASO DE EMERGENCIA ⚠️                         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
    Restaura las plantillas de permisos desde el seed fijo al estado
    "conocido como bueno" del sistema.

CUÁNDO USAR:
    ✅ Después de truncate que borró permission_template_items
    ✅ Corrupción de tabla de asignaciones de permisos
    ✅ Resetear permisos a estado base validado
    ✅ Migración fallida de permisos

CUÁNDO NO USAR:
    ❌ Operación normal (python scripts.py start lo maneja)
    ❌ Solo faltan algunos permisos (autodiscovery lo resuelve)
    ❌ Servidor funcionando correctamente

QUÉ HACE:
    1. Limpia tabla permission_template_items
    2. Restaura asignaciones desde permissions_seed.py
    3. Asigna permisos a los 6 roles del sistema
    4. Usa niveles validados contra casos de uso reales

QUÉ NO HACE:
    ✗ No crea permisos nuevos (usa autodiscovery para eso)
    ✗ No crea templates (deben existir en BD)
    ✗ No modifica user_permissions (overrides se preservan)

USO:
    python scripts_backup/restore_permissions.py

REQUISITOS:
    - Base de datos ya debe tener:
      * permission_templates (6 roles)
      * permissions (autodiscovery los crea)
    - Si no existen, ejecutar primero: python scripts.py start
"""

import sys
import os

# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from app.shared.models.permission_template import PermissionTemplate
from app.shared.models.permission_template_item import PermissionTemplateItem
from app.shared.models.permission import Permission

# Importar seed FIJO
from permissions_seed import (
    PERMISSION_TEMPLATES,
    PERMISSION_MATRIX,
    DEFAULT_SCOPE,
    DEFAULT_PERMISSION_LEVELS
)


def restore_from_seed():
    """
    Restaura permission_template_items desde seed fijo.

    IMPORTANTE: Este proceso es destructivo - elimina todas las asignaciones
    existentes y las recrea desde el seed.
    """
    db = SessionLocal()

    try:
        print()
        print("=" * 70)
        print("🚨 RESTAURACIÓN DE EMERGENCIA - PERMISOS")
        print("=" * 70)
        print()

        # ==================== PASO 1: VALIDAR PREREQUISITOS ====================
        print("PASO 1: Validando prerequisitos...")
        print()

        # Verificar templates
        templates = db.query(PermissionTemplate).filter(
            PermissionTemplate.is_active == True
        ).all()

        if not templates:
            print("❌ ERROR: No hay permission_templates en la base de datos")
            print()
            print("SOLUCIÓN:")
            print("  1. Ejecutar: python scripts.py start")
            print("  2. Esperar a que complete la inicialización")
            print("  3. Volver a ejecutar este script")
            print()
            return False

        templates_dict = {t.role_name: t for t in templates}
        print(f"✓ {len(templates)} templates encontrados:")
        for t in templates:
            print(f"    - {t.role_name} (ID: {t.id})")
        print()

        # Verificar permisos
        permissions = db.query(Permission).all()
        if not permissions:
            print("❌ ERROR: No hay permissions en la base de datos")
            print()
            print("SOLUCIÓN:")
            print("  1. Ejecutar: python scripts.py start")
            print("  2. Esperar a que autodiscovery complete")
            print("  3. Volver a ejecutar este script")
            print()
            return False

        perms_dict = {(p.entity, p.action): p for p in permissions}
        print(f"✓ {len(permissions)} permisos encontrados en BD")
        print()

        # ==================== PASO 2: LIMPIAR ASIGNACIONES ====================
        print("PASO 2: Limpiando asignaciones existentes...")
        print()

        existing_count = db.query(PermissionTemplateItem).count()
        print(f"  Asignaciones actuales: {existing_count}")

        deleted = db.query(PermissionTemplateItem).delete()
        db.commit()

        print(f"  ✓ Eliminadas {deleted} asignaciones")
        print()

        # ==================== PASO 3: RESTAURAR DESDE SEED ====================
        print("PASO 3: Restaurando desde seed fijo...")
        print()

        created = 0
        not_found = []
        stats_by_role = {}

        for (role_name, entity, action, level) in PERMISSION_MATRIX:
            # Buscar template
            template = templates_dict.get(role_name)
            if not template:
                print(f"  [WARN] Template '{role_name}' no encontrado, omitiendo")
                continue

            # Buscar permiso
            perm = perms_dict.get((entity, action))
            if not perm:
                not_found.append(f"{entity}:{action}")
                continue

            # Crear asignación
            item = PermissionTemplateItem(
                template_id=template.id,
                permission_id=perm.id,
                permission_level=level,
                scope=DEFAULT_SCOPE
            )
            db.add(item)
            created += 1

            # Estadísticas por rol
            if role_name not in stats_by_role:
                stats_by_role[role_name] = 0
            stats_by_role[role_name] += 1

        db.commit()

        # Mostrar estadísticas
        print("  Asignaciones creadas por rol:")
        for role_name in sorted(stats_by_role.keys()):
            count = stats_by_role[role_name]
            print(f"    - {role_name:15s}: {count:3d} permisos")
        print()

        # ==================== PASO 4: ASIGNAR PERMISOS NO EN MATRIZ ====================
        print("PASO 4: Asignando permisos adicionales (no en matriz)...")
        print()

        # Permisos que están en BD pero no en la matriz
        matrix_perms = {(entity, action) for (_, entity, action, _) in PERMISSION_MATRIX}
        additional_perms = []

        for perm in permissions:
            if (perm.entity, perm.action) not in matrix_perms:
                additional_perms.append(perm)

        if additional_perms:
            print(f"  Encontrados {len(additional_perms)} permisos adicionales")
            print("  Asignando usando niveles por defecto...")

            additional_created = 0
            for perm in additional_perms:
                for template in templates:
                    # Usar nivel por defecto según rol
                    level = DEFAULT_PERMISSION_LEVELS.get(template.role_name, 0)

                    item = PermissionTemplateItem(
                        template_id=template.id,
                        permission_id=perm.id,
                        permission_level=level,
                        scope=DEFAULT_SCOPE
                    )
                    db.add(item)
                    additional_created += 1

            db.commit()
            print(f"  ✓ {additional_created} asignaciones adicionales creadas")
        else:
            print("  ✓ No hay permisos adicionales")
        print()

        # ==================== PASO 5: REPORTE FINAL ====================
        print("=" * 70)
        print("✅ RESTAURACIÓN COMPLETA")
        print("=" * 70)
        print()
        print(f"  📊 RESUMEN:")
        print(f"    - Asignaciones desde seed: {created}")
        if additional_perms:
            print(f"    - Asignaciones adicionales: {additional_created}")
        print(f"    - Total asignaciones:       {created + (additional_created if additional_perms else 0)}")
        print()

        if not_found:
            print(f"  ⚠️  ADVERTENCIAS:")
            print(f"    - {len(not_found)} permisos del seed no encontrados en BD")
            print(f"    - Esto es normal si son permisos nuevos")
            print()
            print(f"  💡 RECOMENDACIÓN:")
            print(f"    - Ejecutar: python scripts.py autodiscover")
            print(f"    - Luego ejecutar este script nuevamente")
            print()

        print("  ✅ Sistema de permisos restaurado exitosamente")
        print()
        print("=" * 70)
        print()

        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR DURANTE LA RESTAURACIÓN")
        print("=" * 70)
        print()
        print(f"  Error: {str(e)}")
        print()
        print("  La base de datos NO fue modificada (rollback automático)")
        print()
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """Función principal con confirmación de seguridad."""
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║   ⚠️  ADVERTENCIA: OPERACIÓN DESTRUCTIVA ⚠️                       ║")
    print("║                                                                   ║")
    print("║   Este script eliminará TODAS las asignaciones de permisos       ║")
    print("║   existentes y las recreará desde el seed fijo.                  ║")
    print("║                                                                   ║")
    print("║   Datos que se PERDERÁN:                                         ║")
    print("║   - Todas las asignaciones actuales de permission_template_items ║")
    print("║                                                                   ║")
    print("║   Datos que se PRESERVAN:                                        ║")
    print("║   - permission_templates (roles)                                 ║")
    print("║   - permissions (permisos base)                                  ║")
    print("║   - user_permissions (overrides por usuario)                     ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    print("¿Deseas continuar con la restauración?")
    print()
    confirm = input("Escribe 'SI' (en mayúsculas) para confirmar: ")
    print()

    if confirm.strip() != "SI":
        print("❌ Operación cancelada por el usuario")
        print()
        return

    # Ejecutar restauración
    success = restore_from_seed()

    if success:
        print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print()
        print("PRÓXIMOS PASOS:")
        print("  1. Verificar permisos en Swagger UI")
        print("  2. Probar login con diferentes roles")
        print("  3. Si hay permisos faltantes: python scripts.py autodiscover")
        print()
    else:
        print("❌ PROCESO ABORTADO")
        print()


if __name__ == "__main__":
    main()
