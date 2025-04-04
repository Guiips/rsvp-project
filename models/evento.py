from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime, date
from enum import Enum
from bson import ObjectId
from config.email_validador import EmailValidador
import re

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
    nome: str = Field(..., min_length=2, max_length=100, description="Nome do convidado")
    email: EmailStr = Field(..., description="Email do convidado")
    telefone: Optional[str] = Field(None, description="Telefone do convidado (formato: (11) 98765-4321)")
    status: StatusConvidado = Field(default=StatusConvidado.PENDENTE)
    confirmado: Optional[bool] = None
    data_confirmacao: Optional[datetime] = None
    observacoes: Optional[str] = Field(None, max_length=500)

    @validator('email')
    def validar_email(cls, v):
        """
        Validação adicional de email usando EmailValidador
        """
        validacao = EmailValidador.validar_email(v)
        if not validacao['valido']:
            raise ValueError(f"Email inválido: {validacao['motivo']}")
        return validacao['email_normalizado']

    @validator('telefone', always=True, pre=True)
    def validar_telefone(cls, v):
        """
        Validação do telefone
        """
        if v is not None:
            # Regex para validar telefone no formato (11) 98765-4321
            padrao_telefone = re.compile(r'^\(\d{2}\) \d{4,5}-\d{4}$')
            if not padrao_telefone.match(v):
                raise ValueError("Telefone inválido. Use o formato (11) 98765-4321")
        return v

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
    nome: str = Field(..., min_length=3, max_length=100, description="Nome do evento")
    responsavel: str = Field(..., min_length=2, max_length=100, description="Nome do responsável")
    data: str = Field(..., description="Data do evento (YYYY-MM-DD)")
    hora: str = Field(..., description="Hora do evento (HH:MM)")
    local: str = Field(..., min_length=3, max_length=200, description="Local do evento")
    descricao: Optional[str] = Field(None, max_length=1000, description="Descrição do evento")
    categoria: CategoriaEvento = Field(default=CategoriaEvento.OUTROS)
    status: StatusEvento = Field(default=StatusEvento.ATIVO)
    max_convidados: Optional[int] = Field(None, gt=0)
    convidados: List[Convidado] = Field(default_factory=list)
    data_criacao: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    @validator('data')
    def validar_data(cls, v):
        try:
            data_evento = datetime.strptime(v, '%Y-%m-%d').date()
            
            # Verificar se a data é futura
            if data_evento < date.today():
                raise ValueError('Data do evento deve ser no futuro')
            
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

    @validator('convidados', each_item=False)
    def validar_max_convidados(cls, convidados, values):
        """
        Validar número máximo de convidados
        """
        max_convidados = values.get('max_convidados')
        if max_convidados is not None and len(convidados) > max_convidados:
            raise ValueError(f'Número máximo de convidados excedido. Limite: {max_convidados}')
        return convidados

    def gerar_link_confirmacao(self, convidado: Convidado) -> str:
        """
        Gera link de confirmação para um convidado
        """
        from services.token_service import gerar_token_confirmacao
        
        return gerar_token_confirmacao(
            evento_id=str(self._id),
            email=convidado.email
        )

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
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    responsavel: Optional[str] = Field(None, min_length=2, max_length=100)
    data: Optional[str] = None
    hora: Optional[str] = None
    local: Optional[str] = Field(None, min_length=3, max_length=200)
    descricao: Optional[str] = Field(None, max_length=1000)
    categoria: Optional[CategoriaEvento] = None
    status: Optional[StatusEvento] = None
    max_convidados: Optional[int] = Field(None, gt=0)

    @validator('data')
    def validar_data(cls, v):
        if v is not None:
            try:
                data_evento = datetime.strptime(v, '%Y-%m-%d').date()
                
                # Verificar se a data é futura
                if data_evento < date.today():
                    raise ValueError('Data do evento deve ser no futuro')
                
                return v
            except ValueError:
                raise ValueError('Data deve estar no formato YYYY-MM-DD')

    @validator('hora')
    def validar_hora(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%H:%M')
                return v
            except ValueError:
                raise ValueError('Hora deve estar no formato HH:MM')

# Funções auxiliares
def validar_email_convidado(email: str) -> bool:
    """
    Função auxiliar para validação de email de convidado
    """
    return EmailValidador.validar_email(email)['valido']