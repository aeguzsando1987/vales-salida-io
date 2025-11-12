# Cómo Agregar Nuevas Entidades

Esta guía te muestra cómo agregar una nueva entidad (Alumno, Profesor, Departamento, etc.) siguiendo la arquitectura de capas ya establecida.

---

## 🌍 Entidades Base Incluidas

La plantilla ya incluye **3 entidades base** listas para usar:

### 1. **Individual** - Entidad de ejemplo completa
Demuestra todos los tipos de datos, validaciones y patrones avanzados:
- 40+ campos con diferentes tipos de datos
- Sistema de skills con JSONB
- Validaciones complejas
- Relaciones con Country y State

### 2. **Country** - Países con códigos ISO
Entidad base para geografía:
- Códigos ISO 3166 (alpha-2, alpha-3, numérico)
- Información de moneda
- 3 países precargados (USA, México, Colombia)
- Relación 1:N con States

### 3. **State** - Estados/Provincias/Departamentos
División administrativa por país:
- Relación N:1 con Country
- 114 estados precargados (50 USA + 32 MX + 32 CO)
- Validación automática de consistencia país-estado

**Uso en nuevas entidades**: Puedes relacionar tus entidades con Country y State para agregar información geográfica (ejemplo: Individual tiene country_id y state_id con validación).

---

## 📋 Resumen Rápido

Para agregar una entidad necesitas crear **7 archivos**:

```
app/entities/tu_entidad/
├── models/tu_entidad.py          # Modelo SQLAlchemy
├── repositories/tu_entidad_repository.py
├── services/tu_entidad_service.py
├── controllers/tu_entidad_controller.py
├── routers/tu_entidad_router.py
└── schemas/tu_entidad_schemas.py
```

Luego registrar el router en `main.py`.

**Tiempo estimado**: 30-45 minutos

---

## 🎯 Ejemplo Práctico: Entidad "Department"

Vamos a crear una entidad Department (Departamento) paso a paso.

### Convenciones de Nombres

- **Clase/Modelo**: `Department` (PascalCase, singular)
- **Tabla BD**: `departments` (snake_case, plural)
- **Variables**: `department` (snake_case, singular)
- **Carpeta**: `app/entities/departments/` (snake_case, plural)
- **Archivos**: `department.py`, `department_service.py`, etc. (snake_case, singular)

---

## Paso 1: Crear Estructura de Carpetas

```bash
cd app/entities
mkdir departments
cd departments
mkdir models repositories services controllers routers schemas
```

Crear archivos `__init__.py` vacíos:
```bash
touch __init__.py
touch models/__init__.py
touch repositories/__init__.py
touch services/__init__.py
touch controllers/__init__.py
touch routers/__init__.py
touch schemas/__init__.py
```

---

## Paso 2: Modelo (models/department.py)

**Plantilla básica**:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from app.shared.database import Base


class Department(Base):
    """Modelo Department - Representa departamentos de la organizacion"""
    __tablename__ = "departments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Campos basicos
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name})>"
```

**Si tiene relación con otra entidad** (ej: Department tiene muchos Persons):

```python
# Agregar al modelo Department:
from sqlalchemy.orm import relationship

persons = relationship("Person", back_populates="department")

# Agregar al modelo Person:
from sqlalchemy import ForeignKey

department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
department = relationship("Department", back_populates="persons")
```

**Ejemplo: Agregar relación con Country/State**:

```python
# Para agregar geografía a tu entidad:
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Student(Base):
    # ... otros campos ...

    # Relaciones geográficas
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True, index=True)

    country = relationship("Country", foreign_keys=[country_id])
    state = relationship("State", foreign_keys=[state_id])
```

**Validación automática país-estado**: Ver `app/entities/individuals/services/person_service.py:_validate_state_country_consistency()` para implementar validación que asegure que el estado pertenece al país seleccionado.

---

## Paso 3: Schemas (schemas/department_schemas.py)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class DepartmentBase(BaseModel):
    """Schema base"""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """Schema para crear"""
    pass


class DepartmentUpdate(BaseModel):
    """Schema para actualizar (todos opcionales)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema de respuesta"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## Paso 4: Repository (repositories/department_repository.py)

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from app.shared.base_repository import BaseRepository
from app.entities.departments.models.department import Department


class DepartmentRepository(BaseRepository[Department]):
    """Repositorio para Department"""

    def __init__(self, db: Session):
        super().__init__(Department, db)  # IMPORTANTE: (Model, db) no (db, Model)

    def get_by_code(self, code: str) -> Optional[Department]:
        """Busca por codigo unico"""
        return self.db.query(Department).filter(
            Department.code == code,
            Department.is_deleted == False
        ).first()

    def search_by_name(self, name: str) -> List[Department]:
        """Busqueda parcial por nombre"""
        return self.db.query(Department).filter(
            Department.name.ilike(f"%{name}%"),
            Department.is_deleted == False
        ).all()
```

**Tip**: BaseRepository ya incluye: `create()`, `get_by_id()`, `get_all()`, `update()`, `delete()`, `exists()`, `filter_by()`

---

## Paso 5: Service (services/department_service.py)

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from app.entities.departments.repositories.department_repository import DepartmentRepository
from app.entities.departments.models.department import Department
from app.entities.departments.schemas.department_schemas import DepartmentCreate, DepartmentUpdate
from app.shared.exceptions import NotFoundException, BusinessLogicException


class DepartmentService:
    """Logica de negocio para Department"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = DepartmentRepository(db)

    def create_department(self, data: DepartmentCreate, user_id: int) -> Department:
        """Crea un nuevo department"""
        # Validar codigo unico
        if self.repository.get_by_code(data.code):
            raise BusinessLogicException(f"Ya existe un departamento con codigo {data.code}")

        obj_data = data.model_dump()
        return self.repository.create(obj_data)

    def get_department(self, department_id: int) -> Department:
        """Obtiene por ID"""
        department = self.repository.get_by_id(department_id)
        if not department or department.is_deleted:
            raise NotFoundException(f"Department {department_id} no encontrado")
        return department

    def list_departments(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """Lista con paginacion"""
        return self.repository.get_all(skip, limit)

    def update_department(self, department_id: int, data: DepartmentUpdate, user_id: int) -> Department:
        """Actualiza un department"""
        department = self.get_department(department_id)

        # Validar codigo unico si cambio
        if data.code and data.code != department.code:
            if self.repository.get_by_code(data.code):
                raise BusinessLogicException(f"Ya existe un departamento con codigo {data.code}")

        update_data = data.model_dump(exclude_unset=True)
        return self.repository.update(department_id, update_data)

    def delete_department(self, department_id: int) -> bool:
        """Soft delete"""
        department = self.get_department(department_id)
        return self.repository.delete(department_id)
```

---

## Paso 6: Controller (controllers/department_controller.py)

```python
from typing import List
from sqlalchemy.orm import Session
from app.entities.departments.services.department_service import DepartmentService
from app.entities.departments.schemas.department_schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse
)


class DepartmentController:
    """Controlador para Department"""

    def __init__(self, db: Session):
        self.service = DepartmentService(db)

    def create(self, data: DepartmentCreate, user_id: int) -> DepartmentResponse:
        department = self.service.create_department(data, user_id)
        return DepartmentResponse.model_validate(department)

    def get_by_id(self, department_id: int) -> DepartmentResponse:
        department = self.service.get_department(department_id)
        return DepartmentResponse.model_validate(department)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[DepartmentResponse]:
        departments = self.service.list_departments(skip, limit)
        return [DepartmentResponse.model_validate(d) for d in departments]

    def update(self, department_id: int, data: DepartmentUpdate, user_id: int) -> DepartmentResponse:
        department = self.service.update_department(department_id, data, user_id)
        return DepartmentResponse.model_validate(department)

    def delete(self, department_id: int) -> dict:
        success = self.service.delete_department(department_id)
        return {"success": success, "message": "Department eliminado correctamente"}
```

---

## Paso 7: Router (routers/department_router.py)

```python
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.shared.database import get_db
from app.shared.dependencies import get_current_user
from app.entities.departments.controllers.department_controller import DepartmentController
from app.entities.departments.schemas.department_schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse
)


router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Crea un nuevo department"""
    controller = DepartmentController(db)
    return controller.create(data, current_user["id"])


@router.get("/{id}", response_model=DepartmentResponse)
def get_department(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene un department por ID"""
    controller = DepartmentController(db)
    return controller.get_by_id(id)


@router.get("/", response_model=List[DepartmentResponse])
def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista departments con paginacion"""
    controller = DepartmentController(db)
    return controller.get_all(skip, limit)


@router.put("/{id}", response_model=DepartmentResponse)
def update_department(
    id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Actualiza un department"""
    controller = DepartmentController(db)
    return controller.update(id, data, current_user["id"])


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_department(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Elimina (soft delete) un department"""
    controller = DepartmentController(db)
    return controller.delete(id)
```

---

## Paso 8: Registrar en main.py

Agregar estas líneas en `main.py`:

```python
# Importar el router
from app.entities.departments.routers.department_router import router as department_router

# Registrar en la app (después de los otros routers)
app.include_router(department_router)
```

---

## Paso 9: Crear Tabla en Base de Datos

### Opción A: Con Alembic (Recomendado)

```bash
# Generar migracion
alembic revision --autogenerate -m "Add departments table"

# Aplicar migracion
alembic upgrade head
```

### Opción B: Sin Alembic (Manual)

Ejecutar SQL directamente en PostgreSQL:

```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_departments_name ON departments(name);
CREATE INDEX idx_departments_code ON departments(code);
```

---

## ✅ Verificar que Funciona

1. **Reiniciar servidor**:
```bash
python main.py
```

2. **Ver documentación**:
```
http://localhost:8001/docs
```

3. **Probar endpoints**:
   - POST `/departments/` - Crear
   - GET `/departments/` - Listar
   - GET `/departments/{id}` - Obtener por ID
   - PUT `/departments/{id}` - Actualizar
   - DELETE `/departments/{id}` - Eliminar

---

## 🔥 Tips y Mejores Prácticas

### 1. Nombres de Campos Comunes
Siempre incluir estos campos base:
```python
id = Column(Integer, primary_key=True, index=True)
is_active = Column(Boolean, default=True, nullable=False)
is_deleted = Column(Boolean, default=False, nullable=False)
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2. Validaciones en Service
Poner lógica de negocio en el Service, no en Controller ni Repository:
- ✅ Service: Validar reglas de negocio
- ✅ Controller: Coordinar y transformar datos
- ✅ Repository: Solo queries a BD

### 3. Soft Delete
Siempre usar soft delete (is_deleted=True) en vez de borrar físicamente:
```python
# En Repository filter siempre agregar:
.filter(Model.is_deleted == False)
```

### 4. Índices en BD
Agregar índices a campos que se usan en búsquedas:
```python
name = Column(String(200), nullable=False, index=True)
code = Column(String(50), unique=True, nullable=False, index=True)
```

### 5. Relaciones
Para relacionar entidades:

**1:N (Un Department tiene muchos Persons)**:
```python
# En Department:
persons = relationship("Person", back_populates="department")

# En Person:
department_id = Column(Integer, ForeignKey('departments.id'))
department = relationship("Department", back_populates="persons")
```

**N:M (Muchos Students - Muchos Courses)**:
```python
# Tabla intermedia
student_courses = Table('student_courses', Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

# En Student:
courses = relationship("Course", secondary=student_courses, back_populates="students")

# En Course:
students = relationship("Student", secondary=student_courses, back_populates="courses")
```

---

## 📚 Ejemplos de Casos de Uso

### Sistema Educativo
- **Student** (relacionado a User)
- **Teacher** (relacionado a User)
- **Course** (tiene muchos Students)
- **Grade** (relacionado a Student y Course)
- **Classroom**

### Sistema RRHH
- **Employee** (relacionado a User)
- **Department** (tiene muchos Employees)
- **Position** (relacionado a Employee)
- **Payroll** (relacionado a Employee)

### CRM
- **Customer** (relacionado a User)
- **Lead** (puede convertirse en Customer)
- **Deal** (relacionado a Customer)
- **Invoice** (relacionado a Deal)

---

## ❓ Preguntas Frecuentes

**Q: ¿Cuándo usar Service vs Controller?**
A: Service = lógica de negocio. Controller = orquestación y transformación a schemas Pydantic.

**Q: ¿Necesito crear tests?**
A: Recomendado. Copiar estructura de `app/tests/test_persons/` y adaptar.

**Q: ¿Puedo agregar más métodos al Repository?**
A: Sí, agrega métodos específicos para queries complejas.

**Q: ¿Cómo manejo enums?**
A: Ver `app/entities/individuals/schemas/enums.py` como referencia.

---

## 🎯 Resumen Final

Para agregar una nueva entidad:

1. ✅ Crear 7 archivos (Model, Repository, Service, Controller, Router, Schemas, __init__)
2. ✅ Seguir convenciones de nombres
3. ✅ Usar BaseRepository para CRUD básico
4. ✅ Registrar router en main.py
5. ✅ Crear tabla en BD
6. ✅ Probar en /docs

**Tiempo total**: 30-45 minutos por entidad básica.

---

¿Necesitas ayuda? Revisa la entidad **Individual** en `app/entities/individuals/` como ejemplo completo con todos los tipos de datos y validaciones avanzadas.