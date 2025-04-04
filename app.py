from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import os
from datetime import datetime

# Importações das rotas
from routes.eventos import eventos_router
from routes.auth import router as auth_router, verificar_autenticacao, get_current_user
from routes.relatorios import router as relatorios_router

# Importações de configuração
from config.database import conectar_db, fechar_conexao, get_database
from config.secrets import SECRET_KEY, ALGORITHM
from jose import jwt

# Obtém o diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicação...")
    await conectar_db()
    yield
    print("Encerrando aplicação...")
    await fechar_conexao()

# Criar a aplicação FastAPI
app = FastAPI(
    title="Sistema RSVP",
    description="Sistema para gerenciamento de eventos e confirmações de presença",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configuração dos templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Middleware de autenticação
@app.middleware("http")
async def authenticate(request: Request, call_next):
    # Debug log
    print(f"Rota acessada: {request.url.path}")
    
    # Verifica se é uma rota pública
    public_paths = [
        "/api/auth/login",
        "/api/auth/token",
        "/api/eventos/confirmar",
        "/api/eventos/recusar",
        "/api/eventos/confirmar-presenca",
        "/api/eventos/salvar-observacoes",  # Adicionada rota de observações
        "/api/eventos/motivo-recusa",       # Adicionada rota de recusa
        "/static",
        "/uploads",
        "/login"
    ]
    
    # Verifica se é uma rota de convidado (observações, motivo de recusa, etc)
    guest_paths = [
        "salvar-observacoes",
        "motivo-recusa",
        "enviar-email",
        "confirmar-presenca",
        "confirmar",
        "recusar"
    ]
    
    # Se for uma solicitação de arquivo estático ou upload
    if request.url.path.startswith(("/static/", "/uploads/")):
        return await call_next(request)
    
    # Verifica se é uma rota de convidado
    is_guest_action = any(path in request.url.path for path in guest_paths)
    
    # Verifica se é um acesso a detalhes de evento
    is_event_detail = (
        "/eventos/" in request.url.path and 
        request.method == "GET"
    )
    
    # Verifica se é uma rota pública
    is_public_path = any(request.url.path.startswith(path) for path in public_paths)

    print(f"Is public path: {is_public_path}")
    print(f"Is guest action: {is_guest_action}")
    print(f"Is event detail: {is_event_detail}")
    
    # Se for rota pública, ação de convidado ou detalhe de evento, permite o acesso
    if is_public_path or is_guest_action or is_event_detail:
        print("Permitindo acesso à rota pública")
        return await call_next(request)
    
    # Para outras rotas, verifica autenticação
    token = request.cookies.get("access_token")
    if not token:
        print("Token não encontrado")
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="Não autenticado")
        return RedirectResponse(url="/login")
    
    response = await call_next(request)
    return response

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adiciona middleware de sessão
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
    session_cookie="session",
    max_age=1800  # 30 minutos
)

# Configuração de diretórios estáticos
static_dir = BASE_DIR / "static"
uploads_dir = BASE_DIR / "uploads"

# Cria diretórios se não existirem
static_dir.mkdir(exist_ok=True)
uploads_dir.mkdir(exist_ok=True)

# Monta diretórios estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Inclui os routers
app.include_router(eventos_router, prefix="/api/eventos", tags=["eventos"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(relatorios_router, prefix="/api/relatorios", tags=["relatorios"])

# Rota raiz
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Rota principal - redireciona para login se não autenticado"""
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            role = payload.get("role", "")
            
            if role == "admin":
                return RedirectResponse(url="/eventos")
            elif role == "reporter":
                return RedirectResponse(url="/relatorios")
            return RedirectResponse(url="/eventos")
        except:
            pass
    return RedirectResponse(url="/login")

# Rotas de autenticação
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "year": datetime.now().year}
    )

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request):
    """Rota POST para o login"""
    return RedirectResponse(url="/api/auth/login", status_code=307)

# Rotas de eventos
@app.get("/eventos", response_class=HTMLResponse)
async def lista_eventos(request: Request):
    """Página de listagem de eventos"""
    user = await get_current_user(request)
    if user['role'] != 'admin':
        return RedirectResponse(url="/relatorios", status_code=303)
    
    return templates.TemplateResponse(
        "eventos/lista.html",
        {"request": request, "active_page": "eventos", "year": datetime.now().year}
    )

@app.get("/eventos/novo", response_class=HTMLResponse)
async def novo_evento(request: Request):
    """Página de criação de novo evento"""
    user = await get_current_user(request)
    if user['role'] != 'admin':
        return RedirectResponse(url="/relatorios", status_code=303)
    
    return templates.TemplateResponse(
        "eventos/criar.html",
        {"request": request, "active_page": "novo", "year": datetime.now().year}
    )

@app.get("/eventos/{evento_id}", response_class=HTMLResponse)
async def detalhes_evento(request: Request, evento_id: str):
    """Página de detalhes do evento"""
    print(f"Acessando detalhes do evento: {evento_id}")
    
    try:
        # Tentar obter o usuário, mas não bloquear se não estiver autenticado
        user = None
        try:
            user = await get_current_user(request)
        except:
            print("Usuário não autenticado - acessando como convidado")
            pass
        
        # Renderiza a página sempre, mesmo sem autenticação
        return templates.TemplateResponse(
            "eventos/detalhes.html",
            {
                "request": request,
                "evento_id": evento_id,
                "active_page": "eventos",
                "year": datetime.now().year,
                "is_admin": user and user.get('role') == 'admin'
            }
        )
    except Exception as e:
        print(f"Erro ao acessar detalhes do evento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota de relatórios
@app.get("/relatorios", response_class=HTMLResponse)
async def pagina_relatorios(request: Request):
    """Página de relatórios"""
    try:
        db = get_database()
        eventos = []
        
        async for evento in db.eventos.find():
            if '_id' in evento:
                evento['_id'] = str(evento['_id'])
            eventos.append({
                "id": evento['_id'],
                "nome": evento.get('nome', 'Evento sem nome'),
                "data": evento.get('data', 'Sem data')
            })
        
        return templates.TemplateResponse(
            "relatorios/index.html",
            {
                "request": request, 
                "active_page": "relatorios", 
                "year": datetime.now().year,
                "eventos": eventos
            }
        )
    except Exception as e:
        print(f"Erro ao carregar eventos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota de logout
@app.get("/sair")
async def logout(request: Request):
    """Rota para fazer logout"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token", path="/")
    response.headers.update({
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })
    return response

# Rota de health check
@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

# Configuração para execução local
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        workers=1
    )