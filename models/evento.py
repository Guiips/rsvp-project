from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId

class StatusConvidado(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    RECUSADO = "recusado"

class Convidado(BaseModel):
    _id: Optional[ObjectId] = None
    nome: str
    email: str
    telefone: Optional[str] = None
    status: Optional[StatusConvidado] = StatusConvidado.PENDENTE
    confirmado: Optional[bool] = None
    data_confirmacao: Optional[datetime] = None

class Evento(BaseModel):
    nome: str = Field(..., min_length=3, description="Nome do evento")
    responsavel: str = Field(..., min_length=2, description="Nome do responsável")
    data: str = Field(..., description="Data do evento")
    hora: str = Field(..., description="Hora do evento")
    local: str = Field(..., min_length=3, description="Local do evento")
    descricao: Optional[str] = Field(None, min_length=1, description="Descrição do evento")
    convidados: List[Convidado] = Field(default_factory=list, description="Lista de convidados")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Aniversário de 30 anos",
                "responsavel": "João Silva",
                "data": "2024-12-25",
                "hora": "19:00",
                "local": "Restaurante Central",
                "descricao": "Celebração do aniversário de 30 anos com amigos e família",
                "convidados": []
            }
        }

class ConvidadoUpdate(BaseModel):
    status: StatusConvidado
    observacoes: Optional[str] = None

class EventoUpdate(BaseModel):
    nome: Optional[str] = None
    responsavel: Optional[str] = None
    data: Optional[str] = None
    hora: Optional[str] = None
    local: Optional[str] = None
    descricao: Optional[str] = None
    max_convidados: Optional[int] = None
    status: Optional[str] = None
    categoria: Optional[str] = None