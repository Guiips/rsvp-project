from fastapi import APIRouter, HTTPException, Request, Depends, Form, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from dotenv import load_dotenv
from config.secrets import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Carregar variáveis de ambiente
load_dotenv()

# Router de autenticação
router = APIRouter(tags=["auth"])

# Templates
templates = Jinja2Templates(directory="templates")

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Hash das senhas
ADMIN_PASSWORD_HASH = pwd_context.hash("admin123")
CODE_EVENTS_PASSWORD_HASH = pwd_context.hash("code123")

# Informações de usuários
USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": ADMIN_PASSWORD_HASH,
        "role": "admin"
    },
    "code.events": {
        "username": "code.events",
        "hashed_password": CODE_EVENTS_PASSWORD_HASH,
        "role": "reporter"
    }
}

def verify_password(plain_password, hashed_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado"""
    is_valid = pwd_context.verify(plain_password, hashed_password)
    print(f"Verificando senha: {is_valid}")  # Debug
    return is_valid

def get_password_hash(password):
    """Gera um hash para a senha fornecida"""
    return pwd_context.hash(password)

def get_user(username: str):
    """Retorna os dados do usuário se existir"""
    if username in USERS:
        user_dict = USERS[username]
        print(f"Usuário encontrado: {username}")  # Debug
        return user_dict
    print(f"Usuário não encontrado: {username}")  # Debug
    return None

def authenticate_user(username: str, password: str):
    """Autentica um usuário"""
    print(f"Tentativa de autenticação para usuário: {username}")  # Debug
    user = get_user(username)
    if not user:
        print("Usuário não encontrado")  # Debug
        return False
    print(f"Hash armazenado: {user['hashed_password']}")  # Debug
    if not verify_password(password, user["hashed_password"]):
        print("Senha incorreta")  # Debug
        return False
    print("Autenticação bem-sucedida")  # Debug
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Cria um token JWT de acesso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    print(f"Criando token para: {to_encode}")  # Debug
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint para obter um token de acesso"""
    print(f"Tentativa de login para: {form_data.username}")  # Debug
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        print("Falha na autenticação")  # Debug
        raise HTTPException(
            status_code=401,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    print("Token criado com sucesso")  # Debug
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renderiza a página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def process_login(username: str = Form(...), password: str = Form(...)):
    """Processa o login do usuário"""
    print(f"Processando login para usuário: {username}")  # Debug
    user = authenticate_user(username, password)
    if not user:
        print("Falha no login")  # Debug
        return {"success": False, "message": "Nome de usuário ou senha incorretos"}
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    
    print("Login bem-sucedido")  # Debug
    return {
        "success": True, 
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"]
    }

async def verificar_autenticacao(request: Request, call_next):
    """Middleware para verificar autenticação em rotas protegidas"""
    
    # Lista de rotas públicas
    rotas_publicas = [
        "/login", 
        "/api/auth/login", 
        "/api/auth/token", 
        "/static/", 
        "/health", 
        "/favicon.ico",
        "/sair",
        # Adicionar rotas de confirmação/recusa como públicas
        "/api/eventos/confirmar/",
        "/api/eventos/recusar/",
        "/api/eventos/confirmar-presenca/"
    ]
    
    # Verifica se a rota atual é pública
    rota_atual = request.url.path
    for rota in rotas_publicas:
        if rota_atual.startswith(rota):
            return await call_next(request)
    
    # Verifica o token
    token = request.cookies.get("access_token")
    
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "")
        
        # Restrições para usuário reporter
        if role == "reporter":
            # Só permite acesso a relatórios
            allowed_routes = [
                "/relatorios", 
                "/api/relatorios"
            ]
            
            # Verifica se a rota atual é permitida
            if not any(rota_atual.startswith(route) for route in allowed_routes):
                return RedirectResponse(url="/relatorios", status_code=303)
        
    except (JWTError, Exception):
        return RedirectResponse(url="/login", status_code=303)
    
    return await call_next(request)

async def get_current_user(request: str | Request):
    """Obtém o usuário atual"""
    # Se for uma string (token), use o método existente
    if isinstance(request, str):
        try:
            payload = jwt.decode(request, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Token inválido")
            return get_user(username)
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido")
    
    # Se for um objeto Request, extraia o token
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token não encontrado")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return get_user(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Função de utilidade para verificar se o usuário é admin
def is_admin(user_data):
    return user_data.get("role") == "admin"

# Redefinir a senha do admin
@router.post("/reset-admin-password")
async def reset_admin_password():
    """Redefine a senha do admin para o valor padrão (apenas para desenvolvimento)"""
    new_hash = pwd_context.hash("admin123")
    USERS["admin"]["hashed_password"] = new_hash
    print(f"Senha do admin redefinida. Novo hash: {new_hash}")  # Debug
    return {"message": "Senha do admin redefinida para 'admin123'"}