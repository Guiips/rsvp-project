from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from routes.eventos import eventos_router
from config.database import conectar_db, fechar_conexao
import os
from pathlib import Path
from services.email_service import email_service
from routes.auth import router as auth_router
from fastapi.security import OAuth2PasswordBearer
from routes.relatorios import router as relatorios_router

# Inicializa o FastAPI (APENAS UMA VEZ)
app = FastAPI(
    title="Sistema RSVP",
    description="Sistema para gerenciamento de eventos e confirmações de presença",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# Obtém o diretório base do projeto (APENAS UMA VEZ)
BASE_DIR = Path(__file__).resolve().parent

# Configuração dos templates (APENAS UMA VEZ)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Adiciona o router de autenticação
app.include_router(auth_router)

app.include_router(
    relatorios_router,
    prefix="/api/relatorios",
    tags=["relatorios"]
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Rota raiz redireciona para login
@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Inclui as rotas de eventos
app.include_router(
    eventos_router,
    prefix="/api/eventos",
    tags=["eventos"]
)

# Configura pasta de arquivos estáticos
static_dir = BASE_DIR / "static"
uploads_dir = BASE_DIR / "uploads"

# Cria diretórios se não existirem
static_dir.mkdir(exist_ok=True)
uploads_dir.mkdir(exist_ok=True)

# Monta diretórios estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Eventos de inicialização e encerramento
@app.on_event("startup")
async def startup_db_client():
    await conectar_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await fechar_conexao()

# Rotas para as páginas
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial - Lista de eventos"""
    return templates.TemplateResponse(
        "eventos/lista.html",
        {"request": request, "active_page": "home"}
    )

@app.get("/eventos", response_class=HTMLResponse)
async def lista_eventos(request: Request):
    """Página de listagem de eventos"""
    return templates.TemplateResponse(
        "eventos/lista.html",
        {"request": request, "active_page": "eventos"}
    )

@app.get("/eventos/novo", response_class=HTMLResponse)
async def novo_evento(request: Request):
    """Página de criação de novo evento"""
    return templates.TemplateResponse(
        "eventos/criar.html",
        {"request": request, "active_page": "novo"}
    )

@app.get("/eventos/{evento_id}", response_class=HTMLResponse)
async def detalhes_evento(request: Request, evento_id: str):
    """Página de detalhes do evento"""
    return templates.TemplateResponse(
        "eventos/detalhes.html",
        {
            "request": request,
            "evento_id": evento_id,
            "active_page": "eventos"
        }
    )

# Rota de verificação de saúde da API
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
    
    # Obtém a porta do ambiente ou usa 8000 como padrão
    port = int(os.getenv("PORT", 8000))
    
    # Configuração do uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # Permite acesso externo
        port=port,
        reload=True,  # Recarrega automaticamente ao alterar código
        workers=1  # Número de processos workers
    )