from fastapi import APIRouter, HTTPException, Request, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from config.secrets import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Carregar variáveis de ambiente
load_dotenv()

# Router de autenticação
router = APIRouter()  # Nome correto para compatibilidade com app.py

# Templates
templates = Jinja2Templates(directory="templates")

# Informações fictícias de usuário (em produção, deveriam ser armazenadas no banco de dados)
# A senha do usuário admin é "admin123"
USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }
}

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def verify_password(plain_password, hashed_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Gera um hash para a senha fornecida"""
    return pwd_context.hash(password)

def get_user(username: str):
    """Retorna os dados do usuário se existir"""
    if username in USERS:
        user_dict = USERS[username]
        return user_dict
    return None

def authenticate_user(username: str, password: str):
    """Autentica um usuário"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Cria um token JWT de acesso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Obtém o usuário atual a partir do token JWT"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Credenciais inválidas",
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

# Rotas de autenticação
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint para obter um token de acesso"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renderiza a página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def process_login(username: str = Form(...), password: str = Form(...)):
    """Processa o login do usuário"""
    user = authenticate_user(username, password)
    if not user:
        # Redireciona para a página de login com erro
        return {"success": False, "message": "Nome de usuário ou senha incorretos"}
    
    # Gera o token de acesso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    # Retorna sucesso e token para o frontend
    return {
        "success": True, 
        "access_token": access_token,
        "token_type": "bearer"
    }