from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId

class StatusEvento(str, Enum):
    ATIVO = "ativo"
    CANCELADO = "cancelado"
    FINALIZADO = "finalizado"

class CategoriaEvento(str, Enum):
    ANIVERSARIO = "aniversario"
    CASAMENTO = "casamento"
    CORPORATIVO = "corporativo"
    OUTROS = "outros"

class StatusConvidado(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    RECUSADO = "recusado"

class Convidado(BaseModel):
    _id: Optional[ObjectId] = None
    nome: str = Field(..., min_length=2, description="Nome do convidado")
    email: EmailStr = Field(..., description="Email do convidado")
    telefone: Optional[str] = Field(None, description="Telefone do convidado")
    status: StatusConvidado = Field(default=StatusConvidado.PENDENTE)
    confirmado: Optional[bool] = None
    data_confirmacao: Optional[datetime] = None
    observacoes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "email": "joao@email.com",
                "telefone": "(11) 98765-4321",
                "status": "pendente"
            }
        }

class Evento(BaseModel):
    nome: str = Field(..., min_length=3, description="Nome do evento")
    responsavel: str = Field(..., min_length=2, description="Nome do responsável")
    data: str = Field(..., description="Data do evento (YYYY-MM-DD)")
    hora: str = Field(..., description="Hora do evento (HH:MM)")
    local: str = Field(..., min_length=3, description="Local do evento")
    descricao: Optional[str] = Field(None, min_length=1, description="Descrição do evento")
    categoria: CategoriaEvento = Field(default=CategoriaEvento.OUTROS)
    status: StatusEvento = Field(default=StatusEvento.ATIVO)
    max_convidados: Optional[int] = Field(None, gt=0)
    convidados: List[Convidado] = Field(default_factory=list)
    data_criacao: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    @validator('data')
    def validar_data(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Data deve estar no formato YYYY-MM-DD')
    
    @validator('hora')
    def validar_hora(cls, v):
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('Hora deve estar no formato HH:MM')

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Aniversário de 30 anos",
                "responsavel": "João Silva",
                "data": "2024-12-25",
                "hora": "19:00",
                "local": "Restaurante Central",
                "descricao": "Celebração do aniversário de 30 anos",
                "categoria": "aniversario",
                "max_convidados": 100
            }
        }

class EventoUpdate(BaseModel):
    nome: Optional[str] = None
    responsavel: Optional[str] = None
    data: Optional[str] = None
    hora: Optional[str] = None
    local: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[CategoriaEvento] = None
    status: Optional[StatusEvento] = None
    max_convidados: Optional[int] = None