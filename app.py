from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from routes.eventos import eventos_router
from config.database import conectar_db, fechar_conexao
import os

# Inicializa o FastAPI
app = FastAPI(
    title="Sistema RSVP",
    description="API para gerenciamento de eventos e confirmações de presença",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://sistema-rsvp-gd-frontend-557abbaacd62.herokuapp.com"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configura pasta de arquivos estáticos
uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Evento de inicialização - conecta ao banco
@app.on_event("startup")
async def startup_db_client():
    await conectar_db()

# Evento de encerramento - fecha conexão com banco
@app.on_event("shutdown")
async def shutdown_db_client():
    from config.database import fechar_conexao
    await fechar_conexao()

# Rota raiz
@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Sistema RSVP</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                .info {
                    margin-bottom: 15px;
                }
                a {
                    color: #0066cc;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>API do Sistema RSVP</h1>
                <div class="info">
                    <p>Status: API está funcionando!</p>
                    <p>Versão: 1.0.0</p>
                    <p>Para acessar a documentação completa da API, <a href="/docs">clique aqui</a>.</p>
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# Rota personalizada para documentação Swagger
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Sistema RSVP - Documentação API"
    )

# Rota para o schema OpenAPI
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title="Sistema RSVP",
        version="1.0.0",
        description="API para gerenciamento de eventos e confirmações de presença",
        routes=app.routes,
    )

# Inclui as rotas de eventos com prefixo /api/eventos
app.include_router(
    eventos_router,
    prefix="/api/eventos",
    tags=["eventos"]
)

# Configuração para execução local
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )