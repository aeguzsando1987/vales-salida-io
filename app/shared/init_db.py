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

    Esta funcion es idempotente: puede ejecutarse multiples veces sin duplicar datos.
    """
    print("\nInicializando sistema de permisos...")

    # 1. Verificar si ya existen permisos
    existing_permissions = db.query(Permission).count()
    if existing_permissions > 0:
        print(f"Sistema de permisos ya inicializado ({existing_permissions} permisos existentes)")
        return

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

    # 5. Commit de todos los cambios
    db.commit()

    print(f"  {items_count} asignaciones de permisos creadas")
    print("Sistema de permisos inicializado exitosamente\n")