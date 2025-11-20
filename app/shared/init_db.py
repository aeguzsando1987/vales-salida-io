"""
Inicializacion de Base de Datos

Script que se ejecuta al startup de la aplicacion para:
1. Crear tablas si no existen
2. Cargar datos iniciales de paises y estados
"""
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from database import Base, engine
from app.shared.data.countries_states_data import COUNTRIES_STATES_DATA
from app.entities.countries.models.country import Country
from app.entities.states.models.state import State

# Imports para sistema de permisos
from app.shared.models.permission import Permission
from app.shared.models.permission_template import PermissionTemplate
from app.shared.models.permission_template_item import PermissionTemplateItem
from app.shared.data.permissions_seed_data import (
    BASE_PERMISSIONS,
    PERMISSION_TEMPLATES,
    TEMPLATE_PERMISSION_MATRIX,
    get_permission_by_entity_action,
    get_template_by_role
)


def table_exists(table_name: str) -> bool:
    """Verifica si una tabla existe en la base de datos."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def initialize_database(db: Session):
    """
    Inicializa la base de datos con tablas y datos base.

    Esta funcion es idempotente: puede ejecutarse multiples veces sin duplicar datos.
    """
    print("Inicializando base de datos...")

    # 1. Crear tablas si no existen
    if not table_exists("countries") or not table_exists("states"):
        print("Creando tablas de base de datos...")
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas exitosamente")
    else:
        print("Tablas ya existen")

    # 2. Inicializar sistema de permisos (ANTES de verificar países)
    initialize_permissions(db)

    # 3. Verificar si ya existen datos de países
    existing_countries = db.query(Country).count()
    if existing_countries > 0:
        print(f"Base de datos ya contiene {existing_countries} paises. Omitiendo seed de paises/estados.")
        return

    # 3. Cargar datos de paises y estados
    print("Cargando datos de paises y estados...")

    countries_created = 0
    states_created = 0

    for country_key, country_data in COUNTRIES_STATES_DATA.items():
        # Crear pais
        country = Country(
            name=country_data["name"],
            iso_code_2=country_data["iso_code_2"],
            iso_code_3=country_data["iso_code_3"],
            numeric_code=country_data.get("numeric_code"),
            phone_code=country_data.get("phone_code"),
            currency_code=country_data.get("currency_code"),
            currency_name=country_data.get("currency_name"),
            is_active=True
        )
        db.add(country)
        db.flush()  # Para obtener el ID del pais
        countries_created += 1

        # Crear estados del pais
        for state_data in country_data["states"]:
            state = State(
                name=state_data["name"],
                code=state_data["code"],
                country_id=country.id,
                is_active=True
            )
            db.add(state)
            states_created += 1

    # Commit de todos los cambios
    db.commit()

    print(f"Se crearon {countries_created} paises")
    print(f"Se crearon {states_created} estados/provincias/departamentos")
    print("Inicializacion de base de datos completada")


def seed_countries_states(db: Session):
    """
    Funcion alternativa para cargar solo datos de paises/estados
    sin crear tablas.
    """
    existing_countries = db.query(Country).count()
    if existing_countries > 0:
        print(f"Ya existen {existing_countries} paises. No se cargaran datos.")
        return

    countries_created = 0
    states_created = 0

    for country_key, country_data in COUNTRIES_STATES_DATA.items():
        country = Country(
            name=country_data["name"],
            iso_code_2=country_data["iso_code_2"],
            iso_code_3=country_data["iso_code_3"],
            numeric_code=country_data.get("numeric_code"),
            phone_code=country_data.get("phone_code"),
            currency_code=country_data.get("currency_code"),
            currency_name=country_data.get("currency_name"),
            is_active=True
        )
        db.add(country)
        db.flush()
        countries_created += 1

        for state_data in country_data["states"]:
            state = State(
                name=state_data["name"],
                code=state_data["code"],
                country_id=country.id,
                is_active=True
            )
            db.add(state)
            states_created += 1

    db.commit()
    print(f"Seed completado: {countries_created} paises, {states_created} estados")


def initialize_permissions(db: Session):
    """
    Inicializa el sistema de permisos granulares con datos base.

    Crea:
    1. Permisos base (permissions table)
    2. Templates de permisos por rol (permission_templates table)
    3. Items de template con niveles y scopes (permission_template_items table)
    4. Auto-asigna TODOS los permisos al Admin con nivel 4 (NUEVO)

    Esta funcion es idempotente: puede ejecutarse multiples veces sin duplicar datos.
    """
    print("\nInicializando sistema de permisos...")

    # 1. Verificar si ya existen permisos
    existing_permissions = db.query(Permission).count()
    already_initialized = existing_permissions > 0

    if already_initialized:
        print(f"Sistema de permisos ya inicializado ({existing_permissions} permisos existentes)")
        # NO retornar - continuar para asignar nuevos permisos al Admin
    else:
        # 2. Crear permisos base
        print("Creando permisos base...")
        permissions_dict = {}  # Para referencia posterior: "entity:action" -> Permission

        for perm_data in BASE_PERMISSIONS:
            perm = Permission(**perm_data)
            db.add(perm)
            db.flush()  # Obtener ID
            key = f"{perm.entity}:{perm.action}"
            permissions_dict[key] = perm

        permissions_count = len(permissions_dict)
        print(f"  {permissions_count} permisos base creados")

        # 3. Crear templates de permisos
        print("Creando templates de permisos por rol...")
        templates_dict = {}  # role_name -> PermissionTemplate

        for template_data in PERMISSION_TEMPLATES:
            template = PermissionTemplate(**template_data)
            db.add(template)
            db.flush()  # Obtener ID
            templates_dict[template.role_name] = template

        templates_count = len(templates_dict)
        print(f"  {templates_count} templates creados")

        # 4. Crear items de template (asignación permisos a templates con niveles y scopes)
        print("Asignando permisos a templates...")
        items_count = 0

        for role_name, permissions_config in TEMPLATE_PERMISSION_MATRIX.items():
            template = templates_dict.get(role_name)
            if not template:
                print(f"  Warning: Template '{role_name}' not found, skipping")
                continue

            for perm_config in permissions_config:
                # Buscar el permiso correspondiente
                perm_key = f"{perm_config['entity']}:{perm_config['action']}"
                permission = permissions_dict.get(perm_key)

                if not permission:
                    print(f"  Warning: Permission '{perm_key}' not found, skipping")
                    continue

                # Crear item de template
                item = PermissionTemplateItem(
                    template_id=template.id,
                    permission_id=permission.id,
                    permission_level=perm_config['level'],
                    scope=perm_config['scope']
                )
                db.add(item)
                items_count += 1

        # 5. Commit de todos los cambios (solo si NO estaba inicializado)
        db.commit()

        print(f"  {items_count} asignaciones de permisos creadas")

    # 6. AUTO-ASIGNAR PERMISOS A TODOS LOS ROLES (Phase 3+)
    # Esta sección se ejecuta SIEMPRE para sincronizar nuevos permisos con templates
    print("\nAuto-asignando permisos a roles...")

    # Definir niveles de permiso por defecto para cada rol
    # Admin siempre tiene nivel 4, los demás roles tienen niveles según la entidad
    default_permission_levels = {
        "Admin": 4,      # Acceso total a todo
        "Manager": 3,    # Create en la mayoría de entidades
        "Collaborator": 2,  # Update en sus propios recursos
        "Reader": 1,     # Solo lectura
        "Guest": 0,      # Sin acceso por defecto
        "Checker": 1     # Lectura básica para validación QR
    }

    # Obtener todos los templates
    all_templates = db.query(PermissionTemplate).filter(
        PermissionTemplate.is_active == True
    ).all()

    if not all_templates:
        print("  [WARN] No se encontraron templates, omitiendo auto-asignación")
    else:
        # Obtener todos los permisos existentes
        all_perms = db.query(Permission).all()

        total_newly_assigned = 0

        for template in all_templates:
            # Obtener IDs de permisos ya asignados a este template
            existing_items = db.query(PermissionTemplateItem).filter(
                PermissionTemplateItem.template_id == template.id
            ).all()
            existing_perm_ids = {item.permission_id for item in existing_items}

            # Nivel por defecto según el rol
            default_level = default_permission_levels.get(template.role_name, 0)

            # Asignar permisos faltantes
            newly_assigned = 0
            for perm in all_perms:
                if perm.id not in existing_perm_ids:
                    new_item = PermissionTemplateItem(
                        template_id=template.id,
                        permission_id=perm.id,
                        permission_level=default_level,
                        scope="all"
                    )
                    db.add(new_item)
                    newly_assigned += 1
                    total_newly_assigned += 1

            if newly_assigned > 0:
                print(f"  [+] {template.role_name}: {newly_assigned} permisos nuevos (nivel {default_level})")

        if total_newly_assigned > 0:
            db.commit()
            print(f"\n  [OK] Total: {total_newly_assigned} asignaciones nuevas")
        else:
            print(f"  [OK] Todos los permisos ya estaban asignados a todos los roles")

        print(f"  [OK] Total permisos en sistema: {len(all_perms)}")

    print("Sistema de permisos inicializado exitosamente\n")