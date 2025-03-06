from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from routes.eventos import eventos_router
from config.database import conectar_db, fechar_conexao
import os
from pathlib import Path
from services.email_service import email_service
from routes.auth import router as auth_router, verificar_autenticacao
from fastapi.security import OAuth2PasswordBearer
from routes.relatorios import router as relatorios_router
from datetime import datetime
from jose import jwt, JWTError
from config.secrets import SECRET_KEY, ALGORITHM
from fastapi import HTTPException, Request
from config.database import get_database
from routes.auth import get_current_user

# Middleware de autenticação
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        return await verificar_autenticacao(request, call_next)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código executado na inicialização
    print("Iniciando aplicação...")
    await conectar_db()
    
    yield  # Aqui a aplicação está rodando
    
    # Código executado no desligamento
    print("Encerrando aplicação...")
    await fechar_conexao()

# Inicializa o FastAPI
app = FastAPI(
    title="Sistema RSVP",
    description="Sistema para gerenciamento de eventos e confirmações de presença",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Obtém o diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent

# Configuração dos templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Adiciona o middleware de autenticação
app.add_middleware(AuthMiddleware)

# Inclui as rotas de eventos
app.include_router(
    eventos_router,
    prefix="/api/eventos",
    tags=["eventos"]
)

# Adiciona o router de autenticação
app.include_router(auth_router, prefix="/api/auth")

# Adiciona o router de relatórios
app.include_router(
    relatorios_router,
    prefix="/api/relatorios",
    tags=["relatorios"]
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

# Rota raiz redireciona para login ou tela adequada
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Rota principal - redireciona para login se não autenticado"""
    # Verificar se já está autenticado
    token = request.cookies.get("access_token")
    if token:
        try:
            # Decode e valida o token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            role = payload.get("role", "")
            
            # Redirecionar com base no papel
            if role == "admin":
                return RedirectResponse(url="/eventos")
            elif role == "reporter":
                return RedirectResponse(url="/relatorios")
            else:
                return RedirectResponse(url="/eventos")
        except:
            # Se o token for inválido, redireciona para login
            pass
    
    # Se não autenticado ou token inválido, redireciona para login
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "year": datetime.now().year}
    )

# IMPORTANTE: Adiciona a rota POST para login
@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request):
    """Rota POST para o login - redireciona para a API"""
    return RedirectResponse(url="/api/auth/login", status_code=307)

# Rotas para as páginas
@app.get("/eventos", response_class=HTMLResponse)
async def lista_eventos(request: Request):
    """Página de listagem de eventos"""
    return templates.TemplateResponse(
        "eventos/lista.html",
        {"request": request, "active_page": "eventos", "year": datetime.now().year}
    )

@app.get("/eventos/novo", response_class=HTMLResponse)
async def novo_evento(request: Request):
    """Página de criação de novo evento"""
    return templates.TemplateResponse(
        "eventos/criar.html",
        {"request": request, "active_page": "novo", "year": datetime.now().year}
    )

@app.get("/eventos/{evento_id}", response_class=HTMLResponse)
async def detalhes_evento(request: Request, evento_id: str):
    """Página de detalhes do evento"""
    return templates.TemplateResponse(
        "eventos/detalhes.html",
        {
            "request": request,
            "evento_id": evento_id,
            "active_page": "eventos",
            "year": datetime.now().year
        }
    )

# Adicionar uma rota específica para relatórios
@app.get("/relatorios")
async def pagina_relatorios(request: Request):
    """Página de relatórios"""
    try:
        print("Iniciando carregamento de eventos para relatórios")
        db = get_database()
        print("Banco de dados obtido com sucesso")
        
        eventos = []
        print("Buscando eventos no banco de dados")
        
        # Primeiro, conte o número de eventos
        total_eventos = await db.eventos.count_documents({})
        print(f"Total de eventos encontrados: {total_eventos}")
        
        # Busque os eventos
        async for evento in db.eventos.find():
            print(f"Evento encontrado: {evento}")
            
            if '_id' in evento:
                evento['_id'] = str(evento['_id'])
            
            eventos.append({
                "id": evento['_id'],
                "nome": evento.get('nome', 'Evento sem nome'),
                "data": evento.get('data', 'Sem data')
            })
        
        print(f"Número de eventos processados: {len(eventos)}")
        
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
        print(f"Erro DETALHADO ao carregar eventos: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/database")
async def debug_database():
    """Endpoint para depuração da conexão com o banco de dados"""
    try:
        db = get_database()
        
        # Tente algumas operações básicas
        total_eventos = await db.eventos.count_documents({})
        eventos = await db.eventos.find().to_list(length=None)
        
        return {
            "status": "success", 
            "total_eventos": total_eventos,
            "eventos": [str(evento) for evento in eventos]
        }
    except Exception as e:
        print(f"Erro de depuração do banco de dados: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/eventos")
async def lista_eventos(request: Request):
    """Página de listagem de eventos"""
    user = await get_current_user(request)
    
    if user['role'] != 'admin':
        return RedirectResponse(url="/relatorios", status_code=303)
    
    return templates.TemplateResponse(
        "eventos/lista.html",
        {"request": request, "active_page": "eventos", "year": datetime.now().year}
    )

@app.get("/eventos/novo")
async def novo_evento(request: Request):
    """Página de criação de novo evento"""
    user = await get_current_user(request)
    
    if user['role'] != 'admin':
        return RedirectResponse(url="/relatorios", status_code=303)
    
    return templates.TemplateResponse(
        "eventos/criar.html",
        {"request": request, "active_page": "novo", "year": datetime.now().year}
    )

@app.get("/eventos/{evento_id}")
async def detalhes_evento(request: Request, evento_id: str):
    """Página de detalhes do evento"""
    user = await get_current_user(request)
    
    if user['role'] != 'admin':
        return RedirectResponse(url="/relatorios", status_code=303)
    
    return templates.TemplateResponse(
        "eventos/detalhes.html",
        {
            "request": request,
            "evento_id": evento_id,
            "active_page": "eventos",
            "year": datetime.now().year
        }
    )

# Rota de logout
@app.get("/sair")
async def logout(request: Request):
    """Rota para fazer logout - limpa o cookie do token e redireciona para login"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token", path="/")
    # Também podemos adicionar cabeçalhos para forçar não-cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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