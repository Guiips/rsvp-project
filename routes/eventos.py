from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from models.evento import Evento, Convidado, StatusConvidado, EventoUpdate
from config.database import obter_db, get_database
from bson import ObjectId
from datetime import datetime
import io
from openpyxl import load_workbook
from fastapi.responses import HTMLResponse

# Cria o roteador de eventos
eventos_router = APIRouter()

@eventos_router.post("/eventos")
async def criar_evento(evento: Evento):
    db = obter_db()
    try:
        # Converte o dicionário para garantir que todos os campos estejam presentes
        evento_dict = evento.dict(exclude_unset=True)
        
        # Insere o evento
        result = await db.eventos.insert_one(evento_dict)
        
        # Converte o ID para string
        evento_dict['_id'] = str(result.inserted_id)
        
        return evento_dict
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.get("/")  # Mudança aqui
async def listar_eventos():
    db = obter_db()
    eventos = []
    async for evento in db.eventos.find():
        evento['_id'] = str(evento['_id'])
        eventos.append(evento)
    return eventos

@eventos_router.get("/eventos/{evento_id}")
async def obter_evento(evento_id: str):
    db = obter_db()
    try:
        # Converte o ID do evento para ObjectId
        object_id = ObjectId(evento_id)
        
        # Busca o evento no banco de dados
        evento = await db.eventos.find_one({"_id": object_id})
        
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Converte ObjectId para string
        evento['_id'] = str(evento['_id'])
        
        # Garante que o campo convidados existe
        if 'convidados' not in evento:
            evento['convidados'] = []
        
        return evento
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.post("/eventos/{evento_id}/convidados")
async def adicionar_convidado(evento_id: str, convidado: Convidado):
    db = obter_db()
    try:
        # Converte o ID do evento para ObjectId
        object_id = ObjectId(evento_id)
        
        # Verifica se o evento existe
        evento_existente = await db.eventos.find_one({"_id": object_id})
        if not evento_existente:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Adiciona o convidado
        resultado = await db.eventos.update_one(
            {"_id": object_id},
            {"$push": {"convidados": convidado.dict()}}
        )
        
        # Busca o evento atualizado
        evento_atualizado = await db.eventos.find_one({"_id": object_id})
        evento_atualizado['_id'] = str(evento_atualizado['_id'])
        
        return evento_atualizado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.get("/confirmar-presenca/{evento_id}/{convidado_email}/{resposta}")
async def link_confirmacao(
    evento_id: str, 
    convidado_email: str, 
    resposta: str,
    db = Depends(get_database)
):
    try:
        # Converte o ID do evento para ObjectId
        evento_oid = ObjectId(evento_id)

        # Converte a resposta para booleano
        confirmado = resposta.lower() == 'sim'

        # Atualiza o status do convidado
        resultado = await db[db.get_database_name()]["eventos"].update_one(
            {
                "_id": evento_oid, 
                "convidados.email": convidado_email
            },
            {
                "$set": {
                    "convidados.$.confirmado": confirmado,
                    "convidados.$.data_confirmacao": datetime.utcnow(),
                    "convidados.$.status": (
                        StatusConvidado.CONFIRMADO if confirmado 
                        else StatusConvidado.RECUSADO
                    )
                }
            }
        )

        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="Convidado ou Evento não encontrado")

        # Retorna uma página HTML de confirmação
        return HTMLResponse(content=f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background-color: #f0f0f0; 
                }}
                .container {{ 
                    background-color: white; 
                    padding: 30px; 
                    border-radius: 10px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                    max-width: 500px; 
                    margin: 0 auto; 
                }}
                h1 {{ color: #333; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Confirmação de Presença</h1>
                <p>Você {'confirmou' if confirmado else 'recusou'} a presença no evento.</p>
                <p>Obrigado por sua resposta!</p>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.post("/eventos/{evento_id}/convidados/importar")
async def importar_convidados(evento_id: str, file: UploadFile = File(...)):
    db = obter_db()
    try:
        # Converte o ID do evento para ObjectId
        object_id = ObjectId(evento_id)
        
        # Busca o evento
        evento = await db.eventos.find_one({"_id": object_id})
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Lê o arquivo
        contents = await file.read()
        workbook = load_workbook(io.BytesIO(contents))
        worksheet = workbook.active
        
        convidados = []
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            # Permite 2 ou 3 colunas (nome, email, telefone)
            nome = row[0]
            email = row[1]
            telefone = row[2] if len(row) > 2 else None
            
            convidado = {
                'nome': nome, 
                'email': email, 
                'telefone': telefone,
                'status': StatusConvidado.PENDENTE
            }
            convidados.append(convidado)
        
        return {"convidados": convidados}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.post("/eventos/{evento_id}/convidados/confirmar-importacao")
async def confirmar_importacao_convidados(evento_id: str, convidados: List[dict]):
    db = obter_db()
    try:
        # Converte o ID do evento para ObjectId
        object_id = ObjectId(evento_id)
        
        # Busca o evento
        evento = await db.eventos.find_one({"_id": object_id})
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Obtém a lista atual de convidados
        lista_convidados = evento.get('convidados', [])
        
        # Adiciona novos convidados
        lista_convidados.extend(convidados)
        
        # Atualiza o documento no banco de dados
        await db.eventos.update_one(
            {"_id": object_id},
            {"$set": {"convidados": lista_convidados}}
        )
        
        # Busca o evento atualizado
        evento_atualizado = await db.eventos.find_one({"_id": object_id})
        evento_atualizado['_id'] = str(evento_atualizado['_id'])
        
        return evento_atualizado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.patch("/eventos/{evento_id}")
async def atualizar_evento(evento_id: str, evento_update: EventoUpdate):
    db = obter_db()
    try:
        # Converte o ID do evento para ObjectId
        object_id = ObjectId(evento_id)
        
        # Cria um dicionário com os campos a serem atualizados
        update_data = {k: v for k, v in evento_update.dict().items() if v is not None}
        
        # Atualiza o evento
        resultado = await db.eventos.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Busca o evento atualizado
        evento_atualizado = await db.eventos.find_one({"_id": object_id})
        evento_atualizado['_id'] = str(evento_atualizado['_id'])
        
        return evento_atualizado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.delete("/eventos/{evento_id}")
async def deletar_evento(evento_id: str):
    db = obter_db()
    try:
        # Converte o ID do evento para ObjectId
        object_id = ObjectId(evento_id)
        
        # Deleta o evento
        resultado = await db.eventos.delete_one({"_id": object_id})
        
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        return {"mensagem": "Evento deletado com sucesso"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))