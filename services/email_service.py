from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import os
from dotenv import load_dotenv
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do serviço de email
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)
        
    async def enviar_email_confirmacao(
        self,
        email: str,
        nome: str,
        evento_nome: str,
        evento_data: str,
        evento_hora: str,
        evento_local: str,
        link_confirmacao: str,
        link_recusa: str
    ) -> bool:
        try:
            # Template HTML do email com design melhorado
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; margin: 0; padding: 0;">
                    <div style="max-width: 600px; margin: 20px auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #1a73e8; margin-bottom: 20px;">Olá, {nome}!</h2>
                        <p>Você foi convidado(a) para o evento <strong>{evento_nome}</strong>.</p>
                        
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>Data:</strong> {evento_data}</p>
                            <p style="margin: 5px 0;"><strong>Hora:</strong> {evento_hora}</p>
                            <p style="margin: 5px 0;"><strong>Local:</strong> {evento_local}</p>
                        </div>
                        
                        <p>Por favor, confirme sua presença clicando em um dos botões abaixo:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{link_confirmacao}" 
                               style="background-color: #4CAF50; color: white; padding: 12px 25px; 
                                      text-decoration: none; border-radius: 5px; margin: 0 10px; 
                                      display: inline-block; font-weight: bold;">
                                ✓ Confirmar Presença
                            </a>
                            
                            <a href="{link_recusa}" 
                               style="background-color: #dc3545; color: white; padding: 12px 25px; 
                                      text-decoration: none; border-radius: 5px; margin: 10px; 
                                      display: inline-block; font-weight: bold;">
                                ✗ Não Poderei Comparecer
                            </a>
                        </div>
                        
                        <p style="margin-top: 30px;">Aguardamos sua resposta!</p>
                        <p style="color: #666; font-size: 12px; border-top: 1px solid #eee; margin-top: 20px; padding-top: 20px;">
                            Este é um email automático, por favor não responda.<br>
                            Se você não conseguir clicar nos botões, copie e cole os links no seu navegador.
                        </p>
                    </div>
                </body>
            </html>
            """

            message = MessageSchema(
                subject=f"Convite para {evento_nome}",
                recipients=[email],
                body=html,
                subtype="html"
            )

            await self.fastmail.send_message(message)
            logger.info(f"Email enviado com sucesso para {email}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email para {email}: {str(e)}")
            raise

# Cria uma instância global do serviço de email
email_service = EmailService()