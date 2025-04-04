import re
import logging
from typing import Optional, Dict, Any
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from config.email_validador import EmailValidador

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Usuario(Base):
    __tablename__ = 'usuarios'

    id: int
    nome: str
    email: str
    senha_hash: str
    ativo: bool
    tipo_usuario: str

class UsuarioService:
    def __init__(self, db_session: Session = None):
        """
        Inicializa o serviço de usuário com uma sessão de banco de dados
        """
        self.session = db_session or SessionLocal()
        self.model = Usuario

    def hash_senha(self, senha: str) -> str:
        """
        Gera um hash seguro para a senha
        
        Args:
            senha (str): Senha em texto plano
        
        Returns:
            str: Senha hashada
        """
        return pbkdf2_sha256.hash(senha)

    def verificar_senha(self, senha_texto: str, senha_hash: str) -> bool:
        """
        Verifica se a senha corresponde ao hash

        Args:
            senha_texto (str): Senha em texto plano
            senha_hash (str): Hash da senha armazenada

        Returns:
            bool: True se a senha está correta, False caso contrário
        """
        try:
            return pbkdf2_sha256.verify(senha_texto, senha_hash)
        except Exception:
            return False

    def criar_usuario(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo usuário com validações robustas

        Args:
            dados (dict): Dicionário com dados do usuário

        Returns:
            dict: Informações do usuário criado ou erro
        """
        try:
            # Validação de email
            validacao_email = EmailValidador.validar_email(dados.get('email', ''))
            
            if not validacao_email['valido']:
                raise ValueError(f"Email inválido: {validacao_email['motivo']}")
            
            # Usa o email normalizado
            email_normalizado = validacao_email['email_normalizado']
            
            # Verificar se email já existe
            usuario_existente = self.session.query(self.model).filter_by(email=email_normalizado).first()
            if usuario_existente:
                raise ValueError("Email já cadastrado")
            
            # Validações adicionais
            if not dados.get('nome'):
                raise ValueError("Nome é obrigatório")
            
            if len(dados.get('senha', '')) < 8:
                raise ValueError("Senha deve ter no mínimo 8 caracteres")
            
            # Criar novo usuário
            novo_usuario = self.model(
                nome=dados['nome'],
                email=email_normalizado,
                senha_hash=self.hash_senha(dados['senha']),
                ativo=True,
                tipo_usuario=dados.get('tipo_usuario', 'padrao')
            )
            
            # Adicionar e commitar
            self.session.add(novo_usuario)
            self.session.commit()
            
            # Retornar dados do usuário sem a senha
            return {
                'id': novo_usuario.id,
                'nome': novo_usuario.nome,
                'email': novo_usuario.email,
                'tipo_usuario': novo_usuario.tipo_usuario
            }
        
        except (IntegrityError, ValueError) as e:
            # Rollback em caso de erro
            self.session.rollback()
            logger.error(f"Erro ao criar usuário: {str(e)}")
            raise
        
        except Exception as e:
            # Capturar qualquer outro erro inesperado
            self.session.rollback()
            logger.error(f"Erro inesperado ao criar usuário: {str(e)}")
            raise ValueError(f"Erro ao criar usuário: {str(e)}")

    def atualizar_usuario(self, usuario_id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza informações de um usuário

        Args:
            usuario_id (int): ID do usuário
            dados (dict): Dados a serem atualizados

        Returns:
            dict: Informações atualizadas do usuário
        """
        try:
            # Buscar usuário
            usuario = self.session.query(self.model).get(usuario_id)
            
            if not usuario:
                raise ValueError("Usuário não encontrado")
            
            # Validar email se fornecido
            if 'email' in dados:
                validacao_email = EmailValidador.validar_email(dados['email'])
                
                if not validacao_email['valido']:
                    raise ValueError(f"Email inválido: {validacao_email['motivo']}")
                
                dados['email'] = validacao_email['email_normalizado']
            
            # Atualizar campos
            for chave, valor in dados.items():
                if chave == 'senha':
                    # Atualizar senha com hash
                    if len(valor) < 8:
                        raise ValueError("Senha deve ter no mínimo 8 caracteres")
                    setattr(usuario, 'senha_hash', self.hash_senha(valor))
                elif hasattr(usuario, chave):
                    setattr(usuario, chave, valor)
            
            # Commitar alterações
            self.session.commit()
            
            return {
                'id': usuario.id,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo_usuario': usuario.tipo_usuario
            }
        
        except ValueError as e:
            self.session.rollback()
            logger.error(f"Erro de validação: {str(e)}")
            raise
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao atualizar usuário: {str(e)}")
            raise ValueError(f"Erro ao atualizar usuário: {str(e)}")

    def desativar_usuario(self, usuario_id: int) -> bool:
        """
        Desativa um usuário em vez de excluí-lo

        Args:
            usuario_id (int): ID do usuário

        Returns:
            bool: True se desativado com sucesso
        """
        try:
            usuario = self.session.query(self.model).get(usuario_id)
            
            if not usuario:
                raise ValueError("Usuário não encontrado")
            
            usuario.ativo = False
            self.session.commit()
            
            logger.info(f"Usuário {usuario_id} desativado")
            return True
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao desativar usuário: {str(e)}")
            return False

    def autenticar(self, email: str, senha: str) -> Optional[Dict[str, Any]]:
        """
        Autentica um usuário

        Args:
            email (str): Email do usuário
            senha (str): Senha do usuário

        Returns:
            dict: Informações do usuário se autenticação for bem-sucedida
        """
        try:
            # Validar email
            validacao_email = EmailValidador.validar_email(email)
            
            if not validacao_email['valido']:
                logger.warning(f"Tentativa de login com email inválido: {email}")
                return None
            
            email_normalizado = validacao_email['email_normalizado']
            
            # Buscar usuário
            usuario = self.session.query(self.model).filter_by(
                email=email_normalizado, 
                ativo=True
            ).first()
            
            if not usuario:
                logger.warning(f"Usuário não encontrado: {email_normalizado}")
                return None
            
            # Verificar senha
            if not self.verificar_senha(senha, usuario.senha_hash):
                logger.warning(f"Senha incorreta para usuário: {email_normalizado}")
                return None
            
            # Retornar informações do usuário
            return {
                'id': usuario.id,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo_usuario': usuario.tipo_usuario
            }
        
        except Exception as e:
            logger.error(f"Erro durante autenticação: {str(e)}")
            return None

# Criar uma instância global
usuario_service = UsuarioService()