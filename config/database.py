from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging
from pymongo.errors import ConnectionFailure

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Variáveis globais para conexão com o banco de dados
client = None
DATABASE_NAME = os.getenv('DATABASE_NAME', 'rsvp_db')

# Na função conectar_db(), substitua os prints por logs
async def conectar_db():
    """
    Estabelece conexão com o MongoDB
    
    Returns:
        AsyncIOMotorClient: Cliente de conexão com o MongoDB
    """
    global client
    try:
        # URL do MongoDB a partir das variáveis de ambiente
        mongodb_url = os.getenv('MONGODB_URL')
        
        if not mongodb_url:
            logger.error("MONGODB_URL não configurada")
            raise ValueError("MONGODB_URL não configurada")
        
        # Estabelece conexão com o MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        
        # Verifica a conexão
        await client.admin.command('ping')
        
        logger.info(f"Conectado ao banco de dados: {DATABASE_NAME}")
        return client
    except ConnectionFailure as e:
        logger.error(f"Erro de conexão com o banco de dados: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise

def get_database():
    """
    Obtém a instância do banco de dados
    
    Returns:
        AsyncIOMotorDatabase: Instância do banco de dados MongoDB
    """
    if not client:
        raise RuntimeError("Conexão com o banco de dados não estabelecida")
    return client[DATABASE_NAME]

def obter_db():
    """
    Alias para get_database para manter compatibilidade
    
    Returns:
        AsyncIOMotorDatabase: Instância do banco de dados MongoDB
    """
    return get_database()

async def fechar_conexao():
    """
    Fecha a conexão com o banco de dados de forma segura
    """
    global client
    if client:
        client.close()
        print("\U0001f6d1 Conexão com o banco de dados fechada")
        client = None

def get_client():
    """
    Obtém o cliente de conexão com o MongoDB
    
    Returns:
        AsyncIOMotorClient: Cliente de conexão com o MongoDB
    """
    if not client:
        raise RuntimeError("Conexão com o banco de dados não estabelecida")
    return client