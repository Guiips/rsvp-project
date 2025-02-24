import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de email do .env
SMTP_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('MAIL_PORT', 587))
SMTP_USERNAME = os.getenv('MAIL_USERNAME')
SMTP_PASSWORD = os.getenv('MAIL_PASSWORD')
SENDER_EMAIL = os.getenv('MAIL_FROM')


# URL base do site
BASE_URL = "https://rsvpcodevents.online"

class EmailService:
    @staticmethod
    def gerar_token_confirmacao(evento_id, email_convidado):
        """
        Gera um token JWT para confirmação de convite
        """
        try:
            # Token expira em 7 dias
            expiracao = datetime.utcnow() + timedelta(days=7)
            
            payload = {
                "evento_id": str(evento_id),
                "email": email_convidado,
                "exp": expiracao
            }
            
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return token
        except Exception as e:
            print(f"Erro ao gerar token de confirmação: {e}")
            return None

    @staticmethod
    async def enviar_email_confirmacao(
        email: str, 
        nome: str, 
        evento_nome: str, 
        evento_data: str, 
        evento_hora: str, 
        evento_local: str, 
        link_confirmacao: str, 
        link_recusa: str
    ):
        """
        Envia email de confirmação
        """
        try:
            # Validar configurações de email
            if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
                print("Configurações de email incompletas")
                return False

            # Crie a mensagem de email
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = f"Convite para o evento: {evento_nome}"
            
            # Corpo do email em HTML
            corpo_email = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
                    <h2>Convite para o Evento: {evento_nome}</h2>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3>Detalhes do Evento</h3>
                        <p><strong>Nome:</strong> {evento_nome}</p>
                        <p><strong>Data:</strong> {evento_data}</p>
                        <p><strong>Hora:</strong> {evento_hora}</p>
                        <p><strong>Local:</strong> {evento_local}</p>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <p>Olá {nome}, por favor, confirme sua participação:</p>
                        <a href="{link_confirmacao}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                            Confirmar Presença
                        </a>
                        <a href="{link_recusa}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            Recusar Convite
                        </a>
                    </div>
                    
                    <p style="color: #888; font-size: 12px;">
                        Este link expirará em 7 dias. Caso não consiga clicar, copie e cole no navegador.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Anexe o corpo do email
            msg.attach(MIMEText(corpo_email, 'html'))
            
            # Envie o email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"Email enviado com sucesso para {email}")
            return True
        
        except Exception as e:
            print(f"Erro ao enviar email para {email}: {e}")
            return False

# Cria uma instância do serviço de email
email_service = EmailService()