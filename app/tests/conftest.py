"""
Configuracion de fixtures para tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from auth import create_access_token


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fixture que proporciona una sesion de BD limpia para cada test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Fixture que proporciona un cliente HTTP de test con BD mockeada."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_token():
    """Token de autenticacion para usuario admin."""
    return create_access_token(data={"sub": "1"})


@pytest.fixture
def auth_headers(admin_token):
    """Headers HTTP con token de autenticacion."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_person_data():
    """Datos base para crear una persona de prueba."""
    return {
        "first_name": "Juan",
        "last_name": "Perez",
        "email": "juan.perez@test.com",
        "age": 30,
        "is_active": True
    }


@pytest.fixture
def sample_person_extended_data():
    """Datos extendidos para crear una persona con mas informacion."""
    return {
        "first_name": "Maria",
        "last_name": "Garcia",
        "email": "maria.garcia@test.com",
        "age": 28,
        "birth_date": "1996-05-15",
        "gender": "F",
        "height": 1.65,
        "weight": 60.0,
        "monthly_salary": 3500.00,
        "phone_numbers": ["555-0123", "555-0456"],
        "is_active": True
    }


@pytest.fixture
def sample_skill_data():
    """Datos para agregar una skill a una persona."""
    return {
        "name": "Python",
        "category": "TECHNICAL",
        "level": "ADVANCED",
        "years_experience": 4
    }


@pytest.fixture
def sample_multiple_skills():
    """Lista de skills para agregar a una persona."""
    return [
        {
            "name": "Python",
            "category": "TECHNICAL",
            "level": "ADVANCED",
            "years_experience": 4
        },
        {
            "name": "JavaScript",
            "category": "TECHNICAL",
            "level": "INTERMEDIATE",
            "years_experience": 2
        },
        {
            "name": "Docker",
            "category": "TOOL",
            "level": "EXPERT",
            "years_experience": 5
        }
    ]


@pytest.fixture
def created_person(client, auth_headers, sample_person_data):
    """Crea una persona en la BD de test y retorna su ID y datos."""
    response = client.post(
        "/persons/",
        json=sample_person_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    person_data = response.json()
    return person_data


@pytest.fixture
def person_with_skills(client, auth_headers, sample_person_extended_data, sample_multiple_skills):
    """Crea una persona con multiples skills en la BD de test."""
    response = client.post(
        "/persons/",
        json=sample_person_extended_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    person_data = response.json()
    person_id = person_data["id"]

    for skill in sample_multiple_skills:
        skill_response = client.post(
            f"/persons/{person_id}/skills",
            json=skill,
            headers=auth_headers
        )
        assert skill_response.status_code == 200

    return person_data
