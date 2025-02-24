import smtplib
import aiosmtplib
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

# Chave secreta (importe de auth ou defina aqui)
SECRET_KEY = "sistema_rsvp_secret_key_2024"

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
            email, nome, evento_nome, evento_data, evento_hora, evento_local,
            link_confirmacao=None, link_recusa=None
    ):
        """
        Função para enviar email de confirmação com links para confirmar ou recusar presença no evento.
        """
        try:
            # Usar as configurações do .env em vez de valores hardcoded
            smtp_server = SMTP_SERVER
            smtp_port = SMTP_PORT
            smtp_username = SMTP_USERNAME
            smtp_password = SMTP_PASSWORD
            
            # Criar a mensagem de email
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Convite para o evento: {evento_nome}"
            message["From"] = SENDER_EMAIL or smtp_username
            message["To"] = email
            
            # Texto do email
            text = f"""
            Olá {nome},
            
            Você foi convidado para o evento {evento_nome}.
            
            Data: {evento_data}
            Hora: {evento_hora}
            Local: {evento_local}
            
            Para confirmar sua presença, acesse o link:
            {link_confirmacao}
            
            Para recusar o convite, acesse o link:
            {link_recusa}
            
            Atenciosamente,
            Equipe de Eventos
            """
            
            # Versão HTML do email
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; padding: 20px; }}
                    .button {{ display: inline-block; padding: 10px 20px; margin: 10px; 
                              text-decoration: none; border-radius: 5px; color: white; }}
                    .confirm {{ background-color: #28a745; }}
                    .decline {{ background-color: #dc3545; }}
                    .details {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Convite para Evento</h1>
                    </div>
                    
                    <p>Olá <strong>{nome}</strong>,</p>
                    
                    <p>Você foi convidado para o evento <strong>{evento_nome}</strong>.</p>
                    
                    <div class="details">
                        <p><strong>Data:</strong> {evento_data}</p>
                        <p><strong>Hora:</strong> {evento_hora}</p>
                        <p><strong>Local:</strong> {evento_local}</p>
                    </div>
                    
                    <p>Por favor, confirme sua presença:</p>
                    
                    <div style="text-align: center;">
                        <a href="{link_confirmacao}" class="button confirm">Confirmar Presença</a>
                        <a href="{link_recusa}" class="button decline">Recusar Convite</a>
                    </div>
                    
                    <p>Atenciosamente,<br>Equipe de Eventos</p>
                </div>
            </body>
            </html>
            """
            
            # Anexar partes à mensagem
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Tentar com aiosmtplib primeiro (assíncrono)
            try:
                async with aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port) as server:
                    await server.starttls()
                    await server.login(smtp_username, smtp_password)
                    await server.send_message(message)
            except ImportError:
                # Fallback para smtplib padrão se aiosmtplib não estiver disponível
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(message)
            
            print(f"Email enviado com sucesso para {email}")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email para {email}: {str(e)}")
            return False
            
    @staticmethod
    def gerar_tokens_para_evento(evento_id, email_convidado, base_url=None):
        """
        Gera tokens JWT e links completos para confirmação e recusa de presença
        """
        if base_url is None:
            base_url = BASE_URL
            
        # Token para confirmar presença
        token_confirmacao = EmailService.gerar_token_confirmacao(evento_id, email_convidado)
        
        # Token para recusar presença (mesma estrutura, mas vamos diferenciá-los na rota)
        token_recusa = jwt.encode({
            "evento_id": str(evento_id),
            "email": email_convidado,
            "exp": datetime.utcnow() + timedelta(days=7)
        }, SECRET_KEY, algorithm="HS256")
        
        # Criar links completos
        link_confirmacao = f"{base_url}/api/eventos/confirmar/{token_confirmacao}"
        link_recusa = f"{base_url}/api/eventos/recusar/{token_recusa}"
        
        return link_confirmacao, link_recusa

# Cria uma instância do serviço de email
email_service = EmailService()