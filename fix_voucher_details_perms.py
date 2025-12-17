"""
Script para diagnosticar y corregir permisos de voucher-details
"""
from database import SessionLocal, Permission
from app.shared.models.permission_template import PermissionTemplate
from app.shared.models.permission_template_item import PermissionTemplateItem

db = SessionLocal()

print("\n" + "="*70)
print("DIAGNOSTICO DE PERMISOS VOUCHER-DETAILS")
print("="*70)

# 1. Buscar permisos de voucher-details
perms = db.query(Permission).filter(Permission.entity == 'voucher-details').all()
print(f"\n1. PERMISOS EN TABLA permissions: {len(perms)}")
for p in perms:
    print(f"   - ID {p.id}: {p.entity}:{p.action} ({p.http_method} {p.endpoint})")

# 2. Buscar template de Admin
admin_template = db.query(PermissionTemplate).filter(
    PermissionTemplate.role_name == 'Admin',
    PermissionTemplate.is_active == True
).first()

if admin_template:
    print(f"\n2. TEMPLATE ADMIN: ID {admin_template.id}")
else:
    print("\n2. ERROR: NO EXISTE TEMPLATE ADMIN")
    db.close()
    exit(1)

# 3. Buscar asignaciones existentes
perm_ids = [p.id for p in perms]
existing_items = db.query(PermissionTemplateItem).filter(
    PermissionTemplateItem.template_id == admin_template.id,
    PermissionTemplateItem.permission_id.in_(perm_ids)
).all()

print(f"\n3. ASIGNACIONES EXISTENTES: {len(existing_items)}")
if existing_items:
    for item in existing_items:
        perm = next((p for p in perms if p.id == item.permission_id), None)
        if perm:
            print(f"   - {perm.action}: nivel {item.permission_level}")
else:
    print("   (NINGUNA)")

# 4. Crear asignaciones faltantes
print("\n4. CREANDO ASIGNACIONES FALTANTES...")

# Niveles para Admin (según CLAUDE.md sección 6.4)
action_levels = {
    'list': 4,
    'get': 4,
    'create': 4,
    'update': 4,
    'delete': 4,
    'search': 4
}

created_count = 0
for perm in perms:
    # Verificar si ya existe
    existing = db.query(PermissionTemplateItem).filter(
        PermissionTemplateItem.template_id == admin_template.id,
        PermissionTemplateItem.permission_id == perm.id
    ).first()

    if not existing:
        level = action_levels.get(perm.action, 4)  # Default 4 para Admin

        new_item = PermissionTemplateItem(
            template_id=admin_template.id,
            permission_id=perm.id,
            permission_level=level
        )
        db.add(new_item)
        created_count += 1
        print(f"   + Creado: {perm.action} -> nivel {level}")

if created_count > 0:
    db.commit()
    print(f"\n✓ {created_count} asignaciones creadas exitosamente")
else:
    print("\n✓ No hay asignaciones faltantes")

# 5. Verificación final
print("\n5. VERIFICACION FINAL:")
final_items = db.query(PermissionTemplateItem).filter(
    PermissionTemplateItem.template_id == admin_template.id,
    PermissionTemplateItem.permission_id.in_(perm_ids)
).all()

print(f"   Total asignaciones Admin para voucher-details: {len(final_items)}")
for item in final_items:
    perm = next((p for p in perms if p.id == item.permission_id), None)
    if perm:
        print(f"   - {perm.action}: nivel {item.permission_level}")

db.close()

print("\n" + "="*70)
print("DIAGNOSTICO COMPLETADO")
print("="*70 + "\n")
