import smtplib
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from config.secrets import SECRET_KEY

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
    def gerar_token_confirmacao(evento_id, email_convidado, acao='confirmar'):
        """
        Gera um token JWT para confirmação ou recusa de convite
        """
        try:
            # Token expira em 7 dias
            expiracao = datetime.utcnow() + timedelta(days=7)
            
            payload = {
                "evento_id": str(evento_id),
                "email": email_convidado,
                "acao": acao,
                "exp": expiracao
            }
            
            print(f"Gerando token para evento_id={evento_id}, email={email_convidado}, acao={acao}")
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
            # Usar as configurações do .env
            smtp_server = SMTP_SERVER
            smtp_port = SMTP_PORT
            smtp_username = SMTP_USERNAME
            smtp_password = SMTP_PASSWORD
            
            print(f"Enviando email para {email} usando servidor {smtp_server}:{smtp_port}")
            
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
            
            Após confirmar ou recusar sua presença, você poderá adicionar observações importantes como:
            - Restrições alimentares
            - Necessidades especiais
            - Outras informações relevantes
            
            Atenciosamente,
            Equipe de Eventos
            """
            
            # Versão HTML do email
            html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{ 
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{ 
                        text-align: center;
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    .event-title {{
                        color: #1a73e8;
                        font-size: 24px;
                        margin-bottom: 10px;
                    }}
                    .details {{ 
                        background-color: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .button-container {{
                        text-align: center;
                        margin: 25px 0;
                    }}
                    .button {{ 
                        display: inline-block;
                        padding: 12px 24px;
                        margin: 10px;
                        text-decoration: none;
                        border-radius: 50px;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }}
                    .confirm {{ 
                        background-color: #28a745;
                        color: white;
                    }}
                    .confirm:hover {{
                        background-color: #218838;
                    }}
                    .decline {{ 
                        background-color: #dc3545;
                        color: white;
                    }}
                    .decline:hover {{
                        background-color: #c82333;
                    }}
                    .obs-section {{
                        background-color: #e8f5e9;
                        padding: 20px;
                        border-radius: 8px;
                        margin-top: 20px;
                    }}
                    .obs-title {{
                        color: #2e7d32;
                        font-size: 18px;
                        margin-bottom: 10px;
                    }}
                    .obs-list {{
                        margin: 10px 0;
                        padding-left: 20px;
                    }}
                    .obs-list li {{
                        margin: 5px 0;
                        color: #1b5e20;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 class="event-title">Convite para Evento</h1>
                    </div>
                    
                    <p>Olá <strong>{nome}</strong>,</p>
                    
                    <p>Você foi convidado para o evento <strong>{evento_nome}</strong>.</p>
                    
                    <div class="details">
                        <p><strong>Data:</strong> {evento_data}</p>
                        <p><strong>Hora:</strong> {evento_hora}</p>
                        <p><strong>Local:</strong> {evento_local}</p>
                    </div>
                    
                    <div class="button-container">
                        <a href="{link_confirmacao}" class="button confirm">Confirmar Presença</a>
                        <a href="{link_recusa}" class="button decline">Recusar Convite</a>
                    </div>

                    <div class="obs-section">
                        <h2 class="obs-title">Informações Adicionais</h2>
                        <p>Após confirmar ou recusar sua presença, você poderá adicionar observações importantes como:</p>
                        <ul class="obs-list">
                            <li>Restrições alimentares</li>
                            <li>Necessidades especiais</li>
                            <li>Outras informações relevantes</li>
                        </ul>
                    </div>
                    
                    <div class="footer">
                        <p>Atenciosamente,<br>Equipe de Eventos</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Anexar partes à mensagem
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Tentar enviar o email primeiro com smtplib
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    # Inicie TLS apenas se a porta for 587 ou 25
                    if smtp_port in [587, 25]:
                        server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(message)
                    print(f"Email enviado com sucesso para {email}")
                    return True
            except Exception as smtp_error:
                print(f"Erro ao enviar email com smtplib: {str(smtp_error)}")
                # Tentar com aiosmtplib como fallback
                try:
                    if smtp_port == 465:
                        async with aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port, use_tls=True) as server:
                            await server.login(smtp_username, smtp_password)
                            await server.send_message(message)
                    else:
                        async with aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port) as server:
                            await server.starttls()
                            await server.login(smtp_username, smtp_password)
                            await server.send_message(message)
                    print(f"Email enviado com sucesso para {email} (via aiosmtplib)")
                    return True
                except Exception as async_error:
                    print(f"Erro ao enviar email com aiosmtplib: {str(async_error)}")
                    raise
                    
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
        token_confirmacao = EmailService.gerar_token_confirmacao(evento_id, email_convidado, acao='confirmar')
        
        # Token para recusar presença
        token_recusa = EmailService.gerar_token_confirmacao(evento_id, email_convidado, acao='recusar')
        
        print(f"Link confirmação base: {base_url}/api/eventos/confirmar/")
        print(f"Link recusa base: {base_url}/api/eventos/recusar/")
        
        # Criar links completos
        link_confirmacao = f"{base_url}/api/eventos/confirmar/{token_confirmacao}"
        link_recusa = f"{base_url}/api/eventos/recusar/{token_recusa}"
        
        return link_confirmacao, link_recusa

# Cria uma instância do serviço de email
email_service = EmailService()