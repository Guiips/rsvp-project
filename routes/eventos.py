from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from models.evento import Evento, Convidado, StatusConvidado, EventoUpdate
from config.database import obter_db, get_database
from services.email_service import email_service
from bson import ObjectId
from datetime import datetime
import io
from openpyxl import load_workbook
from jose import jwt
from routes.auth import SECRET_KEY

# Cria o roteador de eventos
eventos_router = APIRouter()

# Templates config
templates = Jinja2Templates(directory="templates")

@eventos_router.post("/")
async def criar_evento(evento: Evento):
    """Cria um novo evento"""
    db = obter_db()
    try:
        evento_dict = evento.dict(exclude_unset=True)
        result = await db.eventos.insert_one(evento_dict)
        evento_dict['_id'] = str(result.inserted_id)
        return evento_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.get("/")
async def listar_eventos():
    """Lista todos os eventos"""
    db = obter_db()
    eventos = []
    async for evento in db.eventos.find():
        if '_id' in evento:
            evento['_id'] = str(evento['_id'])
        if 'convidados' in evento:
            for convidado in evento.get('convidados', []):
                if '_id' in convidado:
                    convidado['_id'] = str(convidado['_id'])
        eventos.append(evento)
    return eventos

@eventos_router.get("/{evento_id}")
async def obter_evento(evento_id: str):
    """Obtém detalhes de um evento específico"""
    db = obter_db()
    try:
        object_id = ObjectId(evento_id)
        evento = await db.eventos.find_one({"_id": object_id})
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        evento['_id'] = str(evento['_id'])
        return evento
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.delete("/{evento_id}")
async def excluir_evento(evento_id: str):
    """Exclui um evento"""
    db = obter_db()
    try:
        object_id = ObjectId(evento_id)
        resultado = await db.eventos.delete_one({"_id": object_id})
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        return {"mensagem": "Evento deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.post("/{evento_id}/convidados")
async def adicionar_convidado(request: Request, evento_id: str, convidado: Convidado):
    """Adiciona um novo convidado ao evento"""
    db = obter_db()
    try:
        object_id = ObjectId(evento_id)
        evento = await db.eventos.find_one({"_id": object_id})
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")

        # Gera os links de confirmação
        base_url = str(request.base_url).rstrip('/')
        link_confirmacao = f"{base_url}/api/eventos/confirmar-presenca/{evento_id}/{convidado.email}/sim"
        link_recusa = f"{base_url}/api/eventos/confirmar-presenca/{evento_id}/{convidado.email}/nao"

        # Adiciona o convidado
        convidado_dict = convidado.dict()
        await db.eventos.update_one(
            {"_id": object_id},
            {"$push": {"convidados": convidado_dict}}
        )

        # Envia o email de confirmação
        try:
            await email_service.enviar_email_confirmacao(
                email=convidado.email,
                nome=convidado.nome,
                evento_nome=evento['nome'],
                evento_data=evento['data'],
                evento_hora=evento['hora'],
                evento_local=evento['local'],
                link_confirmacao=link_confirmacao,
                link_recusa=link_recusa
            )
        except Exception as email_error:
            print(f"Erro ao enviar email: {str(email_error)}")

        # Retorna o evento atualizado
        evento_atualizado = await db.eventos.find_one({"_id": object_id})
        evento_atualizado['_id'] = str(evento_atualizado['_id'])
        return evento_atualizado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eventos_router.post("/{evento_id}/convidados/importar")
async def importar_convidados(request: Request, evento_id: str, file: UploadFile = File(...)):
    """Importa lista de convidados de um arquivo Excel"""
    db = obter_db()
    try:
        # Verifica se o arquivo foi enviado
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

        # Lê o conteúdo do arquivo
        contents = await file.read()
        
        # Verifica se o conteúdo não está vazio
        if not contents:
            raise HTTPException(status_code=400, detail="Arquivo vazio")

        # Usa BytesIO para processar o arquivo
        try:
            workbook = load_workbook(io.BytesIO(contents))
        except Exception as excel_error:
            print(f"Erro ao processar Excel: {excel_error}")
            raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo Excel: {str(excel_error)}")

        worksheet = workbook.active

        # Converte o ID do evento
        try:
            object_id = ObjectId(evento_id)
        except Exception as id_error:
            print(f"Erro ao converter ID do evento: {id_error}")
            raise HTTPException(status_code=400, detail="ID de evento inválido")

        # Busca o evento
        evento = await db.eventos.find_one({"_id": object_id})
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")

        base_url = str(request.base_url).rstrip('/')
        convidados = []
        erros_email = []

        # Processar linhas do Excel
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            # Pula linhas sem dados suficientes
            if not row or len(row) < 2 or not row[0] or not row[1]:
                continue

            nome = str(row[0]).strip()
            email = str(row[1]).strip()
            telefone = str(row[2]).strip() if len(row) > 2 and row[2] else None

            # Validações básicas
            if not nome or not email:
                print(f"Linha inválida: {row}")
                continue

            # Gera os links de confirmação
            link_confirmacao = f"{base_url}/api/eventos/confirmar-presenca/{evento_id}/{email}/sim"
            link_recusa = f"{base_url}/api/eventos/confirmar-presenca/{evento_id}/{email}/nao"

            convidado = {
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'status': StatusConvidado.PENDENTE
            }
            convidados.append(convidado)

            # Tenta enviar o email
            try:
                await email_service.enviar_email_confirmacao(
                    email=email,
                    nome=nome,
                    evento_nome=evento['nome'],
                    evento_data=evento['data'],
                    evento_hora=evento['hora'],
                    evento_local=evento['local'],
                    link_confirmacao=link_confirmacao,
                    link_recusa=link_recusa
                )
            except Exception as email_error:
                print(f"Erro ao enviar email para {email}: {str(email_error)}")
                erros_email.append(email)

        # Atualiza o evento com todos os convidados
        if convidados:
            await db.eventos.update_one(
                {"_id": object_id},
                {"$push": {"convidados": {"$each": convidados}}}
            )

        return {
            "convidados": convidados,
            "total_importados": len(convidados),
            "erros_email": erros_email
        }

    except HTTPException:
        # Re-raise HTTPExceptions para que sejam tratadas corretamente
        raise
    except Exception as e:
        # Log detalhado do erro
        import traceback
        print(f"Erro não tratado na importação de convidados: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@eventos_router.get("/confirmar-presenca/{evento_id}/{convidado_email}/{resposta}")
async def confirmar_presenca(
    request: Request,
    evento_id: str,
    convidado_email: str,
    resposta: str
):
    """Processa a confirmação de presença do convidado"""
    try:
        # Converte o ID do evento para ObjectId
        evento_oid = ObjectId(evento_id)
        db = obter_db()

        # Busca o evento
        evento = await db.eventos.find_one({"_id": evento_oid})
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")

        # Converte a resposta para booleano
        confirmado = resposta.lower() == 'sim'

        # Atualiza o status do convidado
        resultado = await db.eventos.update_one(
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
            raise HTTPException(status_code=404, detail="Convidado não encontrado")

        # Renderiza a página de confirmação
        return templates.TemplateResponse(
            "confirmacao_sucesso.html",
            {
                "request": request,
                "confirmado": confirmado,
                "evento": evento,
                "email": convidado_email
            }
        )

    except Exception as e:
        return templates.TemplateResponse("confirmacao_erro.html", {
            "request": request, 
            "mensagem": "Erro ao processar confirmação."
        })


@eventos_router.post("/{evento_id}/convidados/enviar-email")
async def enviar_email_convidado(
    request: Request,
    evento_id: str,
    dados: dict = Body(...)
):
    """Envia email de confirmação para um convidado específico"""
    try:
        db = obter_db()
        object_id = ObjectId(evento_id)
        evento = await db.eventos.find_one({"_id": object_id})
        
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        # Gera os links de confirmação
        base_url = str(request.base_url).rstrip('/')
        link_confirmacao = f"{base_url}/api/eventos/confirmar-presenca/{evento_id}/{dados['email']}/sim"
        link_recusa = f"{base_url}/api/eventos/confirmar-presenca/{evento_id}/{dados['email']}/nao"
        
        # Envia o email
        resultado = await email_service.enviar_email_confirmacao(
            email=dados['email'],
            nome=dados['nome'],
            evento_nome=evento['nome'],
            evento_data=evento['data'],
            evento_hora=evento['hora'],
            evento_local=evento['local'],
            link_confirmacao=link_confirmacao,
            link_recusa=link_recusa
        )
        
        if resultado:
            return {"mensagem": "Email enviado com sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao enviar email")
        
    except Exception as e:
        print(f"Erro ao enviar email individual: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar email: {str(e)}")


@eventos_router.get("/confirmar/{token}")
async def confirmar_convite(token: str, request: Request):
    try:
        db = obter_db()
        # Decodificar o token para encontrar o evento e o convidado
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        evento_id = decoded_token.get('evento_id')
        email_convidado = decoded_token.get('email')
        
        # Buscar o evento
        evento = await db.eventos.find_one({"_id": ObjectId(evento_id)})
        
        if not evento:
            return templates.TemplateResponse("confirmacao_erro.html", {
                "request": request, 
                "mensagem": "Evento não encontrado."
            })
        
        # Encontrar o convidado no evento
        convidados = evento.get('convidados', [])
        convidado_atualizado = False
        
        for convidado in convidados:
            if convidado.get('email') == email_convidado:
                # Atualizar o status do convidado
                convidado['status'] = 'confirmado'
                convidado_atualizado = True
                break
        
        if convidado_atualizado:
            # Atualizar o evento no banco de dados
            await db.eventos.update_one(
                {"_id": ObjectId(evento_id)},
                {"$set": {"convidados": convidados}}
            )
            
            return templates.TemplateResponse("confirmacao_sucesso.html", {
                "request": request, 
                "evento": evento,
                "status": "confirmado"
            })
        else:
            return templates.TemplateResponse("confirmacao_erro.html", {
                "request": request, 
                "mensagem": "Convidado não encontrado."
            })
    
    except jwt.ExpiredSignatureError:
        return templates.TemplateResponse("confirmacao_erro.html", {
            "request": request, 
            "mensagem": "Link de confirmação expirado."
        })
    except Exception as e:
        return templates.TemplateResponse("confirmacao_erro.html", {
            "request": request, 
            "mensagem": "Erro ao processar confirmação."
        })

@eventos_router.get("/recusar/{token}")
async def recusar_convite(token: str, request: Request):
    try:
        db = obter_db()
        # Decodificar o token para encontrar o evento e o convidado
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        evento_id = decoded_token.get('evento_id')
        email_convidado = decoded_token.get('email')
        
        # Buscar o evento
        evento = await db.eventos.find_one({"_id": ObjectId(evento_id)})
        
        if not evento:
            return templates.TemplateResponse("confirmacao_erro.html", {
                "request": request, 
                "mensagem": "Evento não encontrado."
            })
        
        # Encontrar o convidado no evento
        convidados = evento.get('convidados', [])
        convidado_atualizado = False
        
        for convidado in convidados:
            if convidado.get('email') == email_convidado:
                # Atualizar o status do convidado
                convidado['status'] = 'recusado'
                convidado_atualizado = True
                break
        
        if convidado_atualizado:
            # Atualizar o evento no banco de dados
            await db.eventos.update_one(
                {"_id": ObjectId(evento_id)},
                {"$set": {"convidados": convidados}}
            )
            
            return templates.TemplateResponse("confirmacao_sucesso.html", {
                "request": request, 
                "evento": evento,
                "status": "recusado"
            })
        else:
            return templates.TemplateResponse("confirmacao_erro.html", {
                "request": request, 
                "mensagem": "Convidado não encontrado."
            })
    
    except jwt.ExpiredSignatureError:
        return templates.TemplateResponse("confirmacao_erro.html", {
            "request": request, 
            "mensagem": "Link de confirmação expirado."
        })
    except Exception as e:
        return templates.TemplateResponse("confirmacao_erro.html", {
            "request": request, 
            "mensagem": "Erro ao processar confirmação."
        })

@eventos_router.patch("/{evento_id}")
async def atualizar_evento(evento_id: str, evento_update: EventoUpdate):
    """Atualiza os dados de um evento"""
    db = obter_db()
    try:
        object_id = ObjectId(evento_id)
        update_data = {k: v for k, v in evento_update.dict().items() if v is not None}
        
        resultado = await db.eventos.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        
        evento_atualizado = await db.eventos.find_one({"_id": object_id})
        evento_atualizado['_id'] = str(evento_atualizado['_id'])
        
        return evento_atualizado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))