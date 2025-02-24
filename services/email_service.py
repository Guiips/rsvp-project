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

# Chave secreta para tokens (você pode gerar uma chave única)
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
    def enviar_convite_email(evento, convidado):
        """
        Envia email de convite para um convidado
        """
        try:
            # Validar configurações de email
            if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
                print("Configurações de email incompletas")
                return False

            # Gere tokens de confirmação e recusa
            token_confirmacao = EmailService.gerar_token_confirmacao(evento['_id'], convidado['email'])
            token_recusa = EmailService.gerar_token_confirmacao(evento['_id'], convidado['email'])
            
            if not token_confirmacao or not token_recusa:
                print("Falha ao gerar tokens")
                return False

            # Links de confirmação
            link_confirmacao = f"{BASE_URL}/eventos/confirmar/{token_confirmacao}"
            link_recusa = f"{BASE_URL}/eventos/recusar/{token_recusa}"
            
            # Crie a mensagem de email
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = convidado['email']
            msg['Subject'] = f"Convite para o evento: {evento['nome']}"
            
            # Corpo do email em HTML
            corpo_email = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
                    <h2>Convite para o Evento: {evento['nome']}</h2>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3>Detalhes do Evento</h3>
                        <p><strong>Data:</strong> {evento['data']}</p>
                        <p><strong>Local:</strong> {evento['local']}</p>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <p>Por favor, confirme sua participação:</p>
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
            
            print(f"Email enviado com sucesso para {convidado['email']}")
            return True
        
        except Exception as e:
            print(f"Erro ao enviar email para {convidado['email']}: {e}")
            return False

    @staticmethod
    def enviar_email_confirmacao(evento, convidado, status):
        """
        Envia email de confirmação ou recusa
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = convidado['email']
            
            if status == 'confirmado':
                msg['Subject'] = f"Confirmação de Presença - {evento['nome']}"
                corpo_email = f"""
                <html>
                <body>
                    <h2>Presença Confirmada</h2>
                    <p>Você confirmou presença no evento: {evento['nome']}</p>
                    <p>Data: {evento['data']}</p>
                    <p>Local: {evento['local']}</p>
                </body>
                </html>
                """
            else:
                msg['Subject'] = f"Convite Recusado - {evento['nome']}"
                corpo_email = f"""
                <html>
                <body>
                    <h2>Convite Recusado</h2>
                    <p>Você recusou o convite para o evento: {evento['nome']}</p>
                </body>
                </html>
                """
            
            msg.attach(MIMEText(corpo_email, 'html'))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Erro ao enviar email de confirmação: {e}")
            return False