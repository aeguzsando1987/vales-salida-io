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
        # Inicializar datos de prueba (requiere países existentes)
        initialize_test_data(db)
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

    # Inicializar datos de prueba (requiere países cargados)
    initialize_test_data(db)


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

    # MATRIZ DE PERMISOS VALIDADA CONTRA CASOS DE USO
    # Esta matriz fue extraída de los flujos reales del sistema
    # Mapeo de roles:
    #   Admin (role=1) = SUPER_ADMIN
    #   Manager (role=2) = GERENTE
    #   Collaborator (role=3) = SUPERVISOR (NO trabajador)
    #   Reader (role=4) = COLABORADOR (Roberto, Paula, Valerie, Richi)
    #   Checker (role=6) = VIGILANCIA (Enrique)
    PERMISSION_MATRIX = {
        # === VOUCHERS ===
        # Permisos completos para todas las acciones de vouchers
        'vouchers': {
            # CRUD básico
            'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 3, 'Guest': 0, 'Checker': 0},
            'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 2, 'Guest': 0, 'Checker': 0},
            'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            # Workflow - acciones principales
            'approve': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'cancel': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'validate_exit': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 3},
            'confirm_entry': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 3},
            'close': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'start_transit': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'check_overdue': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            # Búsqueda y consultas
            'search': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'advanced': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'folio': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'company': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'status': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'overview': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'enums': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            # Logs y auditoría
            'logs': {'Admin': 4, 'Manager': 3, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'view_logs': {'Admin': 4, 'Manager': 3, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            # PDF y documentos
            'generate_pdf': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'download_pdf': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'generation_info': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'pdf_metadata': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'view_generation_info': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'view_pdf_metadata': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'view_tasks': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            # QR
            'generate_qr': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'validate_qr': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 0, 'Guest': 0, 'Checker': 1},
            'scan_qr': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 3},
            # Estadísticas y mantenimiento
            'view_statistics': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 0},
            'maintenance': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        },
        # === VOUCHER-DETAILS ===
        'voucher-details': {
            'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 3, 'Guest': 0, 'Checker': 0},
            'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 2, 'Guest': 0, 'Checker': 0},
            'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 2, 'Reader': 2, 'Guest': 0, 'Checker': 0},
            'voucher': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'products': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
        },
        # === COMPANIES ===
        'companies': {
            'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
        },
        # === BRANCHES ===
        'branches': {
            'create': {'Admin': 4, 'Manager': 3, 'Collaborator': 3, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'list': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'get': {'Admin': 4, 'Manager': 1, 'Collaborator': 1, 'Reader': 1, 'Guest': 0, 'Checker': 1},
            'update': {'Admin': 4, 'Manager': 2, 'Collaborator': 2, 'Reader': 0, 'Guest': 0, 'Checker': 0},
            'delete': {'Admin': 4, 'Manager': 4, 'Collaborator': 0, 'Reader': 0, 'Guest': 0, 'Checker': 0},
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

    # Niveles de permiso por defecto GLOBAL para cada rol
    # Solo se usa si la entidad:acción NO está en PERMISSION_MATRIX
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
        total_updated = 0

        for template in all_templates:
            # Obtener items existentes para este template
            existing_items = db.query(PermissionTemplateItem).filter(
                PermissionTemplateItem.template_id == template.id
            ).all()
            existing_items_dict = {item.permission_id: item for item in existing_items}

            newly_assigned = 0
            updated = 0

            for perm in all_perms:
                # Determinar nivel correcto según PERMISSION_MATRIX
                entity = perm.entity
                action = perm.action

                # Intentar obtener nivel de la matriz
                correct_level = None
                if entity in PERMISSION_MATRIX:
                    if action in PERMISSION_MATRIX[entity]:
                        correct_level = PERMISSION_MATRIX[entity][action].get(
                            template.role_name,
                            None
                        )

                # Si no está en la matriz, usar nivel global por defecto
                if correct_level is None:
                    correct_level = default_permission_levels.get(template.role_name, 0)

                if perm.id not in existing_items_dict:
                    # CREAR: Permiso no existe para este template
                    new_item = PermissionTemplateItem(
                        template_id=template.id,
                        permission_id=perm.id,
                        permission_level=correct_level,
                        scope="all"
                    )
                    db.add(new_item)
                    newly_assigned += 1
                    total_newly_assigned += 1
                else:
                    # ACTUALIZAR: Permiso existe pero puede tener nivel incorrecto
                    existing_item = existing_items_dict[perm.id]
                    if existing_item.permission_level != correct_level:
                        old_level = existing_item.permission_level
                        existing_item.permission_level = correct_level
                        updated += 1
                        total_updated += 1
                        # Solo mostrar cambios significativos (de 0 a algo o viceversa)
                        if old_level == 0 or correct_level == 0:
                            print(f"  [~] {template.role_name}: {entity}:{action} {old_level} -> {correct_level}")

            if newly_assigned > 0:
                print(f"  [+] {template.role_name}: {newly_assigned} permisos nuevos")
            if updated > 0:
                print(f"  [~] {template.role_name}: {updated} permisos actualizados")

        if total_newly_assigned > 0 or total_updated > 0:
            db.commit()
            print(f"\n  [OK] Nuevos: {total_newly_assigned}, Actualizados: {total_updated}")
        else:
            print(f"  [OK] Todos los permisos ya estaban correctamente configurados")

        print(f"  [OK] Total permisos en sistema: {len(all_perms)}")

    print("Sistema de permisos inicializado exitosamente\n")


def initialize_test_data(db: Session):
    """
    Inicializa datos de prueba para desarrollo.

    Crea:
    1. Usuarios de prueba (manager, collaborator, reader)
    2. 1 Empresa de prueba
    3. 1 Sucursal de prueba
    4. 2 Productos de prueba

    Solo se ejecuta si los datos no existen (idempotente).
    """
    from database import User
    from auth import hash_password
    from app.entities.companies.models.company import Company
    from app.entities.branches.models.branch import Branch
    from app.entities.products.models.product import Product, ProductCategoryEnum

    print("\n" + "="*65)
    print("INICIALIZANDO DATOS DE PRUEBA")
    print("="*65)

    # ==================== 1. USUARIOS DE PRUEBA ====================
    print("\n1. Creando usuarios de prueba...")

    test_users = [
        {
            "email": "manager@test.com",
            "name": "Manager Test",
            "password": "test123",
            "role": 2  # Manager
        },
        {
            "email": "supervisor@test.com",
            "name": "Supervisor Test",
            "password": "test123",
            "role": 3  # Collaborator (Supervisor)
        },
        {
            "email": "collaborator@test.com",
            "name": "Collaborator Test",
            "password": "test123",
            "role": 4  # Reader (Collaborator)
        }
    ]

    users_created = 0
    for user_data in test_users:
        # Verificar si ya existe
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            new_user = User(
                email=user_data["email"],
                name=user_data["name"],
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True
            )
            db.add(new_user)
            users_created += 1
            print(f"  [+] Usuario creado: {user_data['email']} (role={user_data['role']})")
        else:
            print(f"  [·] Usuario ya existe: {user_data['email']}")

    if users_created > 0:
        db.commit()
        print(f"\n  [OK] {users_created} usuarios creados")
    else:
        print(f"\n  [OK] Todos los usuarios de prueba ya existían")

    # ==================== 2. EMPRESA DE PRUEBA ====================
    print("\n2. Creando empresa de prueba...")

    # Obtener país México (asumiendo que ya existe en seed data)
    from app.entities.countries.models.country import Country as CountryModel
    mexico = db.query(CountryModel).filter(CountryModel.iso_code_2 == "MX").first()
    country_id = mexico.id if mexico else 1  # Fallback a ID 1

    company_data = {
        "company_name": "Empresa de Prueba S.A. de C.V.",
        "legal_name": "Empresa de Prueba Sociedad Anónima de Capital Variable",
        "tin": "TES123456789",
        "tax_system": "RFC",
        "country_id": country_id,
        "email": "contacto@testcompany.com",
        "phone": "+52 33 1234 5678",
        "address": "Av. Prueba #123",
        "city": "Guadalajara",
        "postal_code": "44100"
    }

    existing_company = db.query(Company).filter(Company.tin == company_data["tin"]).first()
    if not existing_company:
        new_company = Company(**company_data)
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        company_id = new_company.id
        print(f"  [+] Empresa creada: {company_data['company_name']} (ID: {company_id})")
    else:
        company_id = existing_company.id
        print(f"  [·] Empresa ya existe: {existing_company.company_name} (ID: {company_id})")

    # ==================== 3. SUCURSAL DE PRUEBA ====================
    print("\n3. Creando sucursal de prueba...")

    branch_data = {
        "branch_code": "ALM-01",
        "branch_name": "Almacén Principal",
        "branch_type": "warehouse",
        "description": "Almacén principal de prueba",
        "company_id": company_id,
        "country_id": country_id,
        "address": "Calle Almacén #456",
        "city": "Guadalajara",
        "postal_code": "44110",
        "phone": "+52 33 8765 4321",
        "email": "almacen@testcompany.com"
    }

    existing_branch = db.query(Branch).filter(Branch.branch_code == branch_data["branch_code"]).first()
    if not existing_branch:
        new_branch = Branch(**branch_data)
        db.add(new_branch)
        db.commit()
        db.refresh(new_branch)
        branch_id = new_branch.id
        print(f"  [+] Sucursal creada: {branch_data['branch_name']} (ID: {branch_id})")
    else:
        branch_id = existing_branch.id
        print(f"  [·] Sucursal ya existe: {existing_branch.branch_name} (ID: {branch_id})")

    # ==================== 4. PRODUCTOS DE PRUEBA ====================
    print("\n4. Creando productos de prueba...")

    test_products = [
        {
            "code": "TOOL-001",
            "name": "Martillo Stanley 16oz",
            "description": "Martillo de acero forjado con mango de fibra de vidrio",
            "category": ProductCategoryEnum.TOOL,
            "unit_of_measure": "PZA",
            "part_number": "ST-51-616",
            "is_serialized": False
        },
        {
            "code": "COMP-001",
            "name": "Laptop Dell Latitude 5420",
            "description": "Laptop empresarial Intel Core i5, 16GB RAM, 512GB SSD",
            "category": ProductCategoryEnum.COMPUTER_EQUIPMENT,
            "unit_of_measure": "PZA",
            "part_number": "DELL-LAT-5420",
            "is_serialized": True
        }
    ]

    products_created = 0
    for product_data in test_products:
        existing_product = db.query(Product).filter(Product.code == product_data["code"]).first()
        if not existing_product:
            new_product = Product(**product_data)
            db.add(new_product)
            products_created += 1
            print(f"  [+] Producto creado: {product_data['name']}")
        else:
            print(f"  [·] Producto ya existe: {existing_product.name}")

    if products_created > 0:
        db.commit()
        print(f"\n  [OK] {products_created} productos creados")
    else:
        print(f"\n  [OK] Todos los productos de prueba ya existían")

    print("\n" + "="*65)
    print("DATOS DE PRUEBA INICIALIZADOS EXITOSAMENTE")
    print("="*65)
    print("\nCredenciales de prueba:")
    print("  - Admin:        alonso.guzman@gpamex.com / root")
    print("  - Manager:      manager@test.com / test123")
    print("  - Supervisor:   supervisor@test.com / test123")
    print("  - Collaborator: collaborator@test.com / test123")
    print("\n")