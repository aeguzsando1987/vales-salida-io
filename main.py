from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db, create_tables, User, ExampleEntity
# COMENTADO TEMPORALMENTE: Conflicto con nuevo modelo Individual
# from modules.persons.models import Person
from auth import hash_password, verify_password, create_access_token, verify_token, get_current_user_id, get_current_user, require_admin, require_manager_or_admin, require_collaborator_or_better, require_any_user
import os
from dotenv import load_dotenv

# Cargar variables de entorno (opcional)
load_dotenv()

# Importar routers de módulos
# COMENTADO TEMPORALMENTE: Para probar nueva arquitectura sin conflictos
# from modules.persons import router as persons_router
# Importar nueva arquitectura
from app.entities.individuals.routers.individual_router import router as new_individuals_router
from app.entities.countries.routers.country_router import router as country_router
from app.entities.states.routers.state_router import router as state_router
from app.entities.companies.routers.company_router import router as company_router
from app.entities.branches.routers.branch_router import router as branch_router
from app.entities.products.routers.product_router import router as product_router
from app.entities.vouchers.routers.voucher_router import router as voucher_router
from app.entities.voucher_details.routers.voucher_detail_router import router as voucher_detail_router
from app.shared.routers.admin_permissions_router import router as admin_permissions_router

# Crear aplicación FastAPI con configuración de seguridad para Swagger
app = FastAPI(
    title=os.getenv("APP_NAME", "Simple FastAPI Template"),
    version=os.getenv("VERSION", "1.0.0"),
    openapi_tags=[
        {"name": "auth", "description": "Operaciones de autenticación"},
        {"name": "users", "description": "Gestión de usuarios"},
        {"name": "examples", "description": "Entidades de ejemplo"},
        {"name": "Individuals", "description": "Gestión de individuos"},
        {"name": "Countries", "description": "Gestión de paises"},
        {"name": "States", "description": "Gestión de estados/provincias"},
        {"name": "Companies", "description": "Gestión de empresas"},
        {"name": "Branches", "description": "Gestión de sucursales/ubicaciones"},
        {"name": "Products", "description": "Gestión de productos (cache opcional)"},
        {"name": "Voucher Details", "description": "Gestión de líneas de detalle de vales (artículos)"},
        {"name": "Admin - User Permissions", "description": "Gestión de permisos a nivel de usuario (Fase 3)"},
        {"name": "health", "description": "Estado del sistema"}
    ]
)

# Configurar CORS para webapp_demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",  # Vanilla JS (Live Server)
        "http://127.0.0.1:5500",
        "http://localhost:3000",  # React
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración OAuth2 para Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Incluir routers de módulos
# COMENTADO TEMPORALMENTE: Para probar nueva arquitectura sin conflictos
# app.include_router(persons_router)
# Incluir nueva arquitectura de individuos (ahora en el path principal /individuals)
app.include_router(new_individuals_router)
# Incluir routers de entidades base
app.include_router(country_router)
app.include_router(state_router)
app.include_router(company_router)
app.include_router(branch_router)
app.include_router(product_router)
app.include_router(voucher_router)
app.include_router(voucher_detail_router)
# Incluir router de administración de permisos (Phase 3)
app.include_router(admin_permissions_router)

# Modelos Pydantic para requests/responses
class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: int = 4  # Default: 4=Lector

class ExampleCreate(BaseModel):
    user_id: Optional[int] = None  # Ahora es opcional correctamente
    code: str
    title: str
    description: Optional[str] = None
    status: str = "active"

class ExampleWithUserCreate(BaseModel):
    # Datos del usuario
    user_email: str
    user_name: str
    user_password: str
    # Datos de la entidad
    code: str
    title: str
    description: Optional[str] = None
    status: str = "active"

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[int] = None
    is_active: Optional[bool] = None

class ExampleUpdate(BaseModel):
    user_id: Optional[int] = None
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

# Endpoints de autenticación
@app.post("/token", tags=["auth"], summary="Obtener token de acceso")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Buscar usuario por email (username en OAuth2)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crear token
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/login", tags=["auth"], summary="Iniciar sesión (alternativo)")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # Buscar usuario
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # Crear token
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# Endpoints de usuarios
@app.post("/users", tags=["users"], summary="Crear usuario")
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user = Depends(require_collaborator_or_better)):
    # Verificar si el email ya existe
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email ya existe")

    # Crear usuario
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}

@app.get("/users", tags=["users"], summary="Listar usuarios")
def get_users(db: Session = Depends(get_db), current_user = Depends(require_manager_or_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "name": u.name, "is_active": u.is_active} for u in users]

@app.get("/users/me", tags=["users"], summary="Perfil del usuario actual")
def get_current_user(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@app.get("/users/roles", tags=["users"], summary="Obtener lista de roles disponibles")
def get_user_roles():
    """
    Retorna la lista de roles disponibles en el sistema.
    No requiere autenticación para permitir selección durante registro.
    """
    return [
        {"id": 1, "name": "Admin", "description": "Administrador con acceso total"},
        {"id": 2, "name": "Gerente", "description": "Gerente con acceso de gestión"},
        {"id": 3, "name": "Colaborador", "description": "Colaborador con acceso limitado"},
        {"id": 4, "name": "Lector", "description": "Usuario con acceso de solo lectura"},
        {"id": 5, "name": "Guest", "description": "Invitado con acceso mínimo"}
    ]

@app.get("/users/{user_id}", tags=["users"], summary="Obtener usuario específico")
def get_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(require_manager_or_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user.id, "email": user.email, "name": user.name, "is_active": user.is_active, "created_at": user.created_at}

@app.put("/users/{user_id}", tags=["users"], summary="Actualizar usuario")
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db), current_user = Depends(require_manager_or_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar email único si se está actualizando
    if user_data.email and user_data.email != user.email:
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email ya existe")

    # Actualizar campos
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name, "is_active": user.is_active}

@app.delete("/users/{user_id}", tags=["users"], summary="Eliminar usuario (soft delete)")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Soft delete usando is_deleted
    user.is_deleted = True
    db.commit()
    return {"message": "Usuario eliminado exitosamente (soft delete)"}

@app.delete("/users/{user_id}/hard", tags=["users"], summary="Eliminar usuario permanentemente (hard delete)")
def hard_delete_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Hard delete - eliminación permanente
    db.delete(user)
    db.commit()
    return {"message": "Usuario eliminado permanentemente (hard delete)"}

@app.patch("/users/{user_id}/activate", tags=["users"], summary="Activar usuario")
def activate_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.is_active = True
    db.commit()
    return {"message": "Usuario activado exitosamente"}

@app.patch("/users/{user_id}/deactivate", tags=["users"], summary="Desactivar usuario")
def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.is_active = False
    db.commit()
    return {"message": "Usuario desactivado exitosamente"}

# Endpoints de ExampleEntity (plantilla para replicar)
@app.post("/examples", tags=["examples"], summary="Crear entidad ejemplo")
def create_example(example_data: ExampleCreate, db: Session = Depends(get_db), current_user = Depends(require_collaborator_or_better)):
    # Verificar si el código ya existe
    if db.query(ExampleEntity).filter(ExampleEntity.code == example_data.code).first():
        raise HTTPException(status_code=400, detail="Código ya existe")

    # Crear entidad
    entity = ExampleEntity(**example_data.dict())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return {"id": entity.id, "code": entity.code, "title": entity.title}

@app.get("/examples", tags=["examples"], summary="Listar entidades ejemplo")
def get_examples(db: Session = Depends(get_db), current_user = Depends(require_any_user)):
    entities = db.query(ExampleEntity).all()
    return [{"id": e.id, "code": e.code, "title": e.title, "user_id": e.user_id} for e in entities]

@app.get("/examples/{example_id}", tags=["examples"], summary="Obtener entidad específica")
def get_example(example_id: int, db: Session = Depends(get_db), current_user = Depends(require_any_user)):
    entity = db.query(ExampleEntity).filter(ExampleEntity.id == example_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")
    return {
        "id": entity.id,
        "code": entity.code,
        "title": entity.title,
        "description": entity.description,
        "status": entity.status,
        "user_id": entity.user_id,
        "is_active": entity.is_active,
        "created_at": entity.created_at
    }

@app.put("/examples/{example_id}", tags=["examples"], summary="Actualizar entidad ejemplo")
def update_example(example_id: int, example_data: ExampleUpdate, db: Session = Depends(get_db), current_user = Depends(require_collaborator_or_better)):
    entity = db.query(ExampleEntity).filter(ExampleEntity.id == example_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")

    # Verificar código único si se está actualizando
    if example_data.code and example_data.code != entity.code:
        if db.query(ExampleEntity).filter(ExampleEntity.code == example_data.code).first():
            raise HTTPException(status_code=400, detail="Código ya existe")

    # Actualizar campos
    update_data = example_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    db.commit()
    db.refresh(entity)
    return {
        "id": entity.id,
        "code": entity.code,
        "title": entity.title,
        "description": entity.description,
        "status": entity.status,
        "user_id": entity.user_id
    }

@app.delete("/examples/{example_id}", tags=["examples"], summary="Eliminar entidad ejemplo")
def delete_example(example_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    entity = db.query(ExampleEntity).filter(ExampleEntity.id == example_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")

    # Soft delete
    entity.is_active = False
    db.commit()
    return {"message": "Entidad eliminada exitosamente"}

@app.post("/examples/with-user", tags=["examples"], summary="Crear entidad ejemplo con usuario")
def create_example_with_user(data: ExampleWithUserCreate, db: Session = Depends(get_db), current_user = Depends(require_manager_or_admin)):
    # Verificar si el email ya existe
    if db.query(User).filter(User.email == data.user_email).first():
        raise HTTPException(status_code=400, detail="Email ya existe")

    # Verificar si el código ya existe
    if db.query(ExampleEntity).filter(ExampleEntity.code == data.code).first():
        raise HTTPException(status_code=400, detail="Código ya existe")

    try:
        # Transacción atómica: crear usuario y entidad
        # 1. Crear usuario
        user = User(
            email=data.user_email,
            name=data.user_name,
            password_hash=hash_password(data.user_password)
        )
        db.add(user)
        db.flush()  # Obtener el ID sin hacer commit

        # 2. Crear entidad asociada al usuario
        entity = ExampleEntity(
            user_id=user.id,
            code=data.code,
            title=data.title,
            description=data.description,
            status=data.status
        )
        db.add(entity)

        # 3. Hacer commit de ambos
        db.commit()
        db.refresh(user)
        db.refresh(entity)

        return {
            "message": "Usuario y entidad creados exitosamente",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            },
            "entity": {
                "id": entity.id,
                "code": entity.code,
                "title": entity.title,
                "user_id": entity.user_id
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear usuario y entidad: {str(e)}")

# Endpoint de salud - Solo Admin
@app.get("/health", tags=["health"], summary="Estado del sistema")
def health_check(db: Session = Depends(get_db)):
    return {"status": "ok", "database": "connected"}

# Crear admin por defecto al iniciar
@app.on_event("startup")
def startup_event():
    print("Iniciando aplicación...")
    create_tables()

    # Crear usuario admin por defecto con valores de .env
    db = next(get_db())
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@bapta.com.mx")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "root")

    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            name="Administrador",
            password_hash=hash_password(admin_password),
            role=1  # Role 1 = Admin
        )
        db.add(admin)
        db.commit()
        print(f"Usuario admin creado: {admin_email} (Role: Admin)")
    else:
        print("Usuario admin ya existe")

    # Inicializar base de datos con paises y estados
    from app.shared.init_db import initialize_database
    initialize_database(db)

    # Ejecutar autodiscovery de permisos (Phase 2)
    try:
        from app.shared.autodiscover_permissions import autodiscover_and_sync
        print("\nEjecutando autodiscovery de permisos...")
        autodiscover_and_sync(app, db, dry_run=False)
    except Exception as e:
        print(f"Error en autodiscovery: {e}")
        # No bloquear el inicio si falla autodiscovery
        pass

    # La auto-asignación de permisos al Admin ahora se ejecuta automáticamente
    # en initialize_database() -> initialize_permissions()

    # Iniciar scheduler de tareas automáticas (Fase 2)
    from app.config.settings import settings
    if settings.scheduler_enabled:
        from app.shared.scheduler import start_scheduler
        start_scheduler()
        print("Scheduler de tareas iniciado correctamente")
    else:
        print("⚠ Scheduler deshabilitado en configuración")

    db.close()


@app.on_event("shutdown")
def shutdown_event():
    """Detener scheduler al cerrar aplicación"""
    from app.config.settings import settings
    if settings.scheduler_enabled:
        from app.shared.scheduler import stop_scheduler
        stop_scheduler()
        print("Scheduler detenido correctamente")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "9000"))
    uvicorn.run(app, host=host, port=port)