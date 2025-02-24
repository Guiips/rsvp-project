# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from models.user import User  # Adicione esta linha no topo

# Configurações de segurança
SECRET_KEY = "sua_chave_secreta_aqui"  # Mude isto em produção!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Setup do password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

# Usuários pré-definidos
USERS = {
    "code.events": {
        "username": "code.events",
        "password": pwd_context.hash("Code@2025"),
        "is_admin": False
    },
    "Guilherme": {
        "username": "Guilherme",
        "password": pwd_context.hash("Pedefeijao2@2029"),
        "is_admin": True
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    if username in USERS:
        user_dict = USERS[username]
        return User(**user_dict)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, USERS[username]["password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "admin": user.is_admin},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "redirect_url": "/eventos"}  # Adicionado redirect_url

# Middleware para proteção de rotas
def admin_required(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

# Exemplo de rota protegida que requer login
@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Exemplo de rota que requer admin
@router.get("/admin")
async def admin_route(current_user: User = Depends(admin_required)):
    return {"message": "Admin access granted", "user": current_user}