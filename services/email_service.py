import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import logging
import uuid
import json
import asyncio
from email.mime.text import MIMEText
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from mailjet_rest import Client

# Carrega variáveis de ambiente
load_dotenv()

# Importar secreto
from config.secrets import SECRET_KEY

# Configurações de email
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'eventos@cod.events')
SENDER_NAME = os.getenv('SENDER_NAME', 'Code Events')
BASE_URL = os.getenv('BASE_URL', 'https://cod.events')

# Configurações Mailjet
MAILJET_API_KEY = os.getenv('MAILJET_API_KEY', '')
MAILJET_API_SECRET = os.getenv('MAILJET_API_SECRET', '')

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='email_logs.txt',
    filemode='a'
)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
        
    def gerar_tokens_para_evento(self, evento_id, email_convidado, base_url=None):
        """
        Gera tokens JWT com segurança adicional
        """
        # Usar BASE_URL global se nenhum for fornecido
        if not base_url:
            base_url = BASE_URL
            
        # Adicionar mais aleatoriedade ao token
        token_id = str(uuid.uuid4())
        
        # Token com informações adicionais
        token_confirmacao = jwt.encode(
            {
                'jti': token_id,  # ID único do token
                'evento_id': evento_id,
                'email': email_convidado,
                'acao': 'confirmar',
                'origem': 'sistema_rsvp',
                'exp': datetime.utcnow() + timedelta(days=30)
            },
            SECRET_KEY,
            algorithm='HS256'
        )
        
        token_recusa = jwt.encode(
            {
                'jti': token_id,
                'evento_id': evento_id,
                'email': email_convidado,
                'acao': 'recusar',
                'origem': 'sistema_rsvp',
                'exp': datetime.utcnow() + timedelta(days=30)
            },
            SECRET_KEY,
            algorithm='HS256'
        )
        
        # Criar links completos
        link_confirmacao = f"{base_url}/api/eventos/confirmar/{token_confirmacao}"
        link_recusa = f"{base_url}/api/eventos/recusar/{token_recusa}"
        
        return link_confirmacao, link_recusa

    async def enviar_email_html(self, email, assunto, conteudo_html, categorias=None):
        """
        Envio de email usando Mailjet com configurações anti-spam otimizadas
        """
        try:
            logger.info(f"Preparando email para {email} com assunto: {assunto}")
            
            # Criar versão texto plano do conteúdo HTML
            try:
                texto_plano = BeautifulSoup(conteudo_html, 'html.parser').get_text()
            except Exception as text_error:
                logger.warning(f"Erro ao criar versão texto: {text_error}")
                texto_plano = "Por favor, visualize este email em um cliente que suporta HTML."
            
            # ID de rastreamento único para este email
            tracking_id = str(uuid.uuid4())
            
            # Preparar categorias para tags Mailjet
            tags = []
            if categorias:
                tags = categorias[:5]  # Mailjet permite até 5 tags
            
            # Configurar payload para Mailjet
            data = {
                'Messages': [
                    {
                        'From': {
                            'Email': SENDER_EMAIL,
                            'Name': SENDER_NAME
                        },
                        'To': [
                            {
                                'Email': email
                            }
                        ],
                        'Subject': assunto,
                        'TextPart': texto_plano,
                        'HTMLPart': conteudo_html,
                        'CustomID': tracking_id,
                        'Headers': {
                            'X-MJ-CustomID': tracking_id,
                            'X-MJ-EventPayload': 'custom_payload',
                            'X-Mailjet-TrackOpen': '1',
                            'X-Mailjet-TrackClick': '1'
                        },
                        'TrackOpens': 'enabled',
                        'TrackClicks': 'enabled',
                        'CustomCampaign': 'code_events'
                    }
                ]
            }
            
            # Adicionar tags se existirem
            if tags:
                data['Messages'][0]['Tags'] = tags
            
            # Enviar email via Mailjet API
            logger.info(f"Enviando email via Mailjet para {email}")
            response = self.mailjet.send.create(data=data)
            
            # Verificar resposta da API
            status_code = response.status_code
            response_data = response.json()
            
            if status_code == 200:
                logger.info(f"Email enviado com sucesso para {email}. Tracking ID: {tracking_id}")
                logger.debug(f"Resposta Mailjet: {json.dumps(response_data)}")
                return True
            else:
                logger.error(f"Erro ao enviar email. Código: {status_code}")
                logger.error(f"Detalhes: {json.dumps(response_data)}")
                return False
                
        except Exception as e:
            logger.error(f"Erro no envio de email: {str(e)}")
            return False

    async def enviar_email_confirmacao(self, email, nome, evento_nome, evento_data, 
                                     evento_hora, evento_local, link_confirmacao, link_recusa):
        """
        Envia email de confirmação com template otimizado
        """
        assunto = f"Convite para {evento_nome} - Confirmação de Presença"
        
        # Template com design responsivo
        conteudo_html = self.gerar_template_email(
            nome=nome,
            evento_nome=evento_nome,
            evento_data=evento_data,
            evento_hora=evento_hora,
            evento_local=evento_local,
            link_confirmacao=link_confirmacao,
            link_recusa=link_recusa
        )
        
        # Categorias para rastreamento e organização
        categorias = ["convite", "rsvp", evento_nome.lower().replace(" ", "_")]
        
        return await self.enviar_email_html(email, assunto, conteudo_html, categorias=categorias)

    def gerar_template_email(self, **kwargs):
        """
        Template de email responsivo e otimizado
        """
        return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Convite para {kwargs.get('evento_nome', 'Evento')}</title>
    <style type="text/css">
        body, table, td, a {{ font-family: Arial, sans-serif; }}
        table {{ border-collapse: collapse; }}
        img {{ max-width: 100%; height: auto; border: 0; outline: none; text-decoration: none; }}
        h1, h2, h3, h4, h5, h6 {{ margin-top: 0; margin-bottom: 0; font-weight: bold; color: #333333; }}
        p {{ margin-top: 0; margin-bottom: 0; color: #333333; }}
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .mobile-padding {{ padding-left: 10px !important; padding-right: 10px !important; }}
            .full-width {{ width: 100% !important; }}
            .mobile-button {{ width: 100% !important; display: block !important; }}
            .mobile-center {{ text-align: center !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f7f7f7; -webkit-font-smoothing: antialiased; -webkit-text-size-adjust: none; width: 100%; font-family: Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f7f7f7;">
        <tr>
            <td align="center" style="padding: 20px 0px;">
                <!-- Preheader Text (não visível no email, mas ajuda com filtros de spam) -->
                <div style="display:none;font-size:1px;color:#ffffff;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">
                    Você foi convidado para {kwargs.get('evento_nome', 'Evento')} no dia {kwargs.get('evento_data', '04/06/2025')}. Por favor, confirme sua presença.
                </div>
                
                <table border="0" cellpadding="0" cellspacing="0" width="600" class="container" style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <!-- Logo Header -->
                    <tr>
                        <td align="center" bgcolor="#ffffff" style="padding: 20px 0 0 0;">
                            <h2 style="color: #1976D2; margin: 0; font-size: 22px; font-weight: bold;">CODE EVENTS</h2>
                        </td>
                    </tr>
                    
                    <!-- Cabeçalho -->
                    <tr>
                        <td align="center" bgcolor="#1976D2" style="padding: 30px 20px; border-radius: 0 0 4px 4px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: bold;">Convite Oficial</h1>
                        </td>
                    </tr>
                    
                    <!-- Conteúdo -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 30px 20px 30px;">
                            <p style="margin-top: 0; font-size: 16px; line-height: 1.5; color: #333333;">Olá, <strong>{kwargs.get('nome', 'Convidado')}</strong>,</p>
                            
                            <p style="margin: 15px 0; font-size: 16px; line-height: 1.5; color: #333333;">Temos o prazer de convidá-lo para o <strong>{kwargs.get('evento_nome', 'Evento')}</strong>.</p>
                            
                            <!-- Detalhes do evento -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f5f5f5; margin: 25px 0; border-left: 4px solid #1976D2; border-radius: 4px;">
                                <tr>
                                    <td colspan="2" style="padding: 15px 20px 5px 20px;">
                                        <h3 style="margin: 0; color: #1976D2; font-size: 18px;">Detalhes do Evento</h3>
                                    </td>
                                </tr>
                                <tr>
                                    <td width="100" style="padding: 10px 0 10px 20px;"><strong>Data:</strong></td>
                                    <td style="padding: 10px 20px 10px 0;">{kwargs.get('evento_data', '04/06/2025')}</td>
                                </tr>
                                <tr>
                                    <td width="100" style="padding: 10px 0 10px 20px;"><strong>Horário:</strong></td>
                                    <td style="padding: 10px 20px 10px 0;">{kwargs.get('evento_hora', '06:00')}</td>
                                </tr>
                                <tr>
                                    <td width="100" style="padding: 10px 0 10px 20px;"><strong>Local:</strong></td>
                                    <td style="padding: 10px 20px 10px 0;">{kwargs.get('evento_local', 'Casa')}</td>
                                </tr>
                            </table>
                            
                            <p style="margin: 25px 0; font-size: 16px; line-height: 1.5; color: #333333; text-align: center;">Por gentileza, confirme sua presença clicando em um dos botões abaixo:</p>
                            
                            <!-- Botões -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <table border="0" cellpadding="0" cellspacing="0" class="mobile-full-width">
                                            <tr>
                                                <td align="center" bgcolor="#4CAF50" class="mobile-button" style="border-radius: 4px; padding: 0px;">
                                                    <a href="{kwargs.get('link_confirmacao', '#')}" target="_blank" style="color: #ffffff; text-decoration: none; display: inline-block; font-weight: bold; font-size: 16px; padding: 15px 25px; border-radius: 4px; background-color: #4CAF50; width: 200px; text-align: center;">
                                                        Confirmar Presença
                                                    </a>
                                                </td>
                                                <td width="20" class="mobile-hidden"> </td>
                                                <td align="center" bgcolor="#f44336" class="mobile-button" style="border-radius: 4px; padding: 0px;">
                                                    <a href="{kwargs.get('link_recusa', '#')}" target="_blank" style="color: #ffffff; text-decoration: none; display: inline-block; font-weight: bold; font-size: 16px; padding: 15px 25px; border-radius: 4px; background-color: #f44336; width: 200px; text-align: center;">
                                                        Não Poderei Comparecer
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin-top: 30px; font-size: 16px; line-height: 1.5; color: #333333;">Agradecemos sua atenção e esperamos contar com sua presença!</p>
                            
                            <p style="margin-top: 25px; font-size: 16px; line-height: 1.5; color: #333333;">Atenciosamente,<br />
                            <strong>Equipe Code Events</strong></p>
                        </td>
                    </tr>
                    
                    <!-- Rodapé -->
                    <tr>
                        <td bgcolor="#f5f5f5" style="padding: 20px; text-align: center; color: #757575; font-size: 13px; border-radius: 0 0 4px 4px;">
                            <p style="margin: 0;">Este é um e-mail automático. Por favor, não responda diretamente a esta mensagem.</p>
                            <p style="margin-top: 10px; font-size: 12px;">
                                <a href="#" style="color: #757575; text-decoration: underline;">Cancelar inscrição</a>
                            </p>
                            <p style="margin-top: 10px; font-size: 12px; color: #9e9e9e;">
                                © 2025 Code Events. Todos os direitos reservados.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

# Cria uma instância global do serviço de email
email_service = EmailService()

# Teste quando executado diretamente
if __name__ == "__main__":
    async def teste_envio():
        # Teste de envio de email com Mailjet
        resultado = await email_service.enviar_email_html(
            email='seu-email@exemplo.com',  # Substitua por seu email real para teste
            assunto='Teste de Email Code Events com Mailjet',
            conteudo_html="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Teste do Sistema de Emails</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    <div style="background-color: #1976D2; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Teste de Envio com Mailjet</h1>
                    </div>
                    <div style="padding: 20px;">
                        <p>Este é um email de teste do sistema Code Events usando Mailjet.</p>
                        <p>Se você está recebendo este email, a configuração com Mailjet está funcionando corretamente.</p>
                        <p>Agora você pode enviar emails de maneira confiável e eficiente para seus usuários!</p>
                        <div style="margin: 25px 0; padding: 15px; background-color: #f5f5f5; border-left: 4px solid #1976D2; border-radius: 4px;">
                            <strong>Benefícios do Mailjet:</strong>
                            <ul style="margin-top: 10px; padding-left: 20px;">
                                <li>Alta taxa de entrega</li>
                                <li>Baixas chances de cair em spam</li>
                                <li>Analytics detalhados</li>
                                <li>Escalabilidade</li>
                            </ul>
                        </div>
                        <p>Este email foi enviado às {datetime.now().strftime('%H:%M:%S')} em {datetime.now().strftime('%d/%m/%Y')}.</p>
                    </div>
                    <div style="background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                        <p>© 2025 Code Events. Todos os direitos reservados.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        
        if resultado:
            print("Email de teste enviado com sucesso!")
        else:
            print("Falha ao enviar email de teste!")
    
    # Executa o teste
    asyncio.run(teste_envio())