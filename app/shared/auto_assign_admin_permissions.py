"""
Auto-asignación de permisos al rol Admin.

Este módulo se ejecuta automáticamente al iniciar el servidor para asegurar
que el rol Admin tenga nivel 4 (acceso total) en todos los permisos existentes.

Se ejecuta DESPUÉS del autodiscovery de permisos para sincronizar nuevos endpoints.

Autor: E. Guzman
Fecha: 2025-11-14
"""

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.shared.models.permission import Permission
from app.shared.models.permission_template import PermissionTemplate
from app.shared.models.permission_template_item import PermissionTemplateItem


def auto_assign_admin_permissions(db: Session, verbose: bool = True):
    """
    Asigna automáticamente todos los permisos existentes al rol Admin con nivel 4.

    Esta función es idempotente: puede ejecutarse múltiples veces sin duplicar datos.
    Solo asigna permisos que aún no estén asignados al template Admin.

    Args:
        db: Sesión de base de datos
        verbose: Si True, imprime mensajes de progreso

    Returns:
        dict: Resumen de la operación
            - total_permissions: Total de permisos en el sistema
            - already_assigned: Permisos ya asignados
            - newly_assigned: Permisos recién asignados
    """
    if verbose:
        print("\n" + "=" * 70)
        print("AUTO-ASIGNACIÓN DE PERMISOS AL ROL ADMIN")
        print("=" * 70)

    # 1. Verificar que existe el template Admin
    admin_template = db.query(PermissionTemplate).filter(
        PermissionTemplate.role_name == "Admin",
        PermissionTemplate.is_active == True
    ).first()

    if not admin_template:
        if verbose:
            print("[ERROR] No se encontró el template 'Admin'")
            print("[INFO] Ejecutar: python scripts.py restart (para inicializar sistema)")
        return {
            "error": "Template Admin not found",
            "total_permissions": 0,
            "already_assigned": 0,
            "newly_assigned": 0
        }

    if verbose:
        print(f"[OK] Template Admin encontrado (ID: {admin_template.id})")

    # 2. Obtener TODOS los permisos existentes
    all_permissions = db.query(Permission).all()

    if not all_permissions:
        if verbose:
            print("[WARN] No hay permisos en la base de datos")
            print("[INFO] Ejecutar: python scripts.py restart (para autodiscovery)")
        return {
            "total_permissions": 0,
            "already_assigned": 0,
            "newly_assigned": 0
        }

    total_permissions = len(all_permissions)
    if verbose:
        print(f"[OK] Encontrados {total_permissions} permisos totales en el sistema")

    # 3. Obtener permisos ya asignados al Admin
    existing_items = db.query(PermissionTemplateItem).filter(
        PermissionTemplateItem.template_id == admin_template.id
    ).all()

    # Crear set de IDs de permisos ya asignados
    existing_permission_ids = {item.permission_id for item in existing_items}

    already_assigned = len(existing_permission_ids)
    if verbose:
        print(f"[INFO] Permisos ya asignados: {already_assigned}")
        print(f"[INFO] Permisos por asignar: {total_permissions - already_assigned}")
        print()

    # 4. Asignar permisos faltantes con nivel 4
    newly_assigned = 0

    for permission in all_permissions:
        if permission.id in existing_permission_ids:
            # Ya está asignado, skip
            continue

        # Crear nueva asignación con nivel 4 (acceso total)
        new_item = PermissionTemplateItem(
            template_id=admin_template.id,
            permission_id=permission.id,
            permission_level=4,  # Nivel 4 = Delete (acceso total)
            scope="all"          # Scope all = acceso a todos los registros
        )
        db.add(new_item)
        newly_assigned += 1

        if verbose:
            print(f"  [+] {permission.entity}:{permission.action:<25} → nivel 4 (Delete/Full Access)")

    # 5. Commit de cambios
    if newly_assigned > 0:
        db.commit()
        if verbose:
            print()
            print("=" * 70)
            print(f"[OK] Auto-asignación completada: {newly_assigned} permisos nuevos")
            print(f"[OK] Total permisos en Admin: {total_permissions}")
            print("=" * 70)
            print()
    else:
        if verbose:
            print("[OK] Todos los permisos ya estaban asignados al Admin")
            print()

    return {
        "total_permissions": total_permissions,
        "already_assigned": already_assigned,
        "newly_assigned": newly_assigned
    }


def verify_admin_permissions(db: Session, entity: str = None) -> dict:
    """
    Verifica los permisos asignados al rol Admin.

    Útil para debugging y verificación manual.

    Args:
        db: Sesión de base de datos
        entity: Si se especifica, filtra por entidad (ej: "branches")

    Returns:
        dict: Permisos del Admin organizados por entidad
    """
    admin_template = db.query(PermissionTemplate).filter(
        PermissionTemplate.role_name == "Admin"
    ).first()

    if not admin_template:
        return {"error": "Template Admin not found"}

    # Query con JOIN para obtener permisos
    query = db.query(
        Permission.entity,
        Permission.action,
        Permission.http_method,
        Permission.endpoint,
        PermissionTemplateItem.permission_level
    ).join(
        PermissionTemplateItem,
        Permission.id == PermissionTemplateItem.permission_id
    ).filter(
        PermissionTemplateItem.template_id == admin_template.id
    )

    if entity:
        query = query.filter(Permission.entity == entity)

    query = query.order_by(Permission.entity, Permission.action)

    results = query.all()

    # Organizar por entidad
    permissions_by_entity = {}
    for entity, action, http_method, endpoint, level in results:
        if entity not in permissions_by_entity:
            permissions_by_entity[entity] = []

        permissions_by_entity[entity].append({
            "action": action,
            "http_method": http_method,
            "endpoint": endpoint,
            "level": level,
            "level_name": ["None", "Read", "Update", "Create", "Delete"][level]
        })

    return permissions_by_entity


if __name__ == "__main__":
    """
    Permite ejecutar este script directamente para asignar permisos manualmente.

    Uso:
        python -m app.shared.auto_assign_admin_permissions
    """
    import sys
    sys.path.insert(0, '.')
    from database import get_db

    db = next(get_db())

    try:
        result = auto_assign_admin_permissions(db, verbose=True)

        print("\nRESUMEN:")
        print(f"  Total permisos: {result['total_permissions']}")
        print(f"  Ya asignados: {result['already_assigned']}")
        print(f"  Recién asignados: {result['newly_assigned']}")

        # Verificar asignación
        print("\n" + "=" * 70)
        print("VERIFICACIÓN DE PERMISOS DEL ADMIN")
        print("=" * 70)

        perms_by_entity = verify_admin_permissions(db)

        for entity, perms in sorted(perms_by_entity.items()):
            print(f"\n{entity.upper()}:")
            for perm in perms:
                print(f"  {perm['action']:<25} {perm['http_method']:<8} → nivel {perm['level']} ({perm['level_name']})")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
