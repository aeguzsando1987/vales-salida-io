from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

# Cargar variables de entorno (opcional)
load_dotenv()

# Configuración de autenticación con fallbacks
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-aqui")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Funciones de hash de contraseñas
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Funciones JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user_id(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Funciones de autorización por roles
def get_current_user(current_user_id: int = Depends(get_current_user_id)):
    from database import User, get_db
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Usuario inactivo")
        if user.is_deleted:
            raise HTTPException(status_code=403, detail="Usuario eliminado")
        return user
    finally:
        db.close()

def require_role(minimum_role: int):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role > minimum_role:
            raise HTTPException(
                status_code=403,
                detail=f"Se requiere rol de nivel {minimum_role} o superior. Tu rol actual: {current_user.role}"
            )
        return current_user
    return role_checker

def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != 1:
        raise HTTPException(status_code=403, detail="Se requiere rol de Administrador")
    return current_user

def require_manager_or_admin(current_user = Depends(get_current_user)):
    if current_user.role > 2:
        raise HTTPException(status_code=403, detail="Se requiere rol de Gerente o Administrador")
    return current_user

# Funciones específicas para evitar errores con require_role()
def require_collaborator_or_better(current_user = Depends(get_current_user)):
    if current_user.role > 3:
        raise HTTPException(status_code=403, detail="Se requiere rol de Colaborador o superior")
    return current_user

def require_any_user(current_user = Depends(get_current_user)):
    # Todos los usuarios autenticados (roles 1-5)
    return current_user