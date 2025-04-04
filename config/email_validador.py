import re
from email_validator import validate_email, EmailNotValidError
import logging

class EmailValidador:
    @staticmethod
    def validar_email(email):
        """
        Valida um endereço de email usando múltiplas técnicas
        
        Args:
            email (str): Endereço de email a ser validado
        
        Returns:
            dict: Resultado da validação com informações detalhadas
        """
        # Verificações preliminares
        if not email or not isinstance(email, str):
            return {
                'valido': False,
                'motivo': 'Email não é uma string válida',
                'email_normalizado': None
            }
        
        # Remover espaços em branco
        email = email.strip().lower()
        
        # Validação por expressão regular (primeiro filtro)
        padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(padrao_email, email):
            return {
                'valido': False,
                'motivo': 'Formato de email inválido',
                'email_normalizado': None
            }
        
        # Validação usando email_validator
        try:
            # Valida e normaliza o email
            validacao = validate_email(email)
            email_normalizado = validacao.email
            
            return {
                'valido': True,
                'motivo': 'Email válido',
                'email_normalizado': email_normalizado
            }
        
        except EmailNotValidError as e:
            # Registra o erro de validação
            logging.warning(f"Erro na validação de email {email}: {str(e)}")
            
            return {
                'valido': False,
                'motivo': str(e),
                'email_normalizado': None
            }
    
    @staticmethod
    def validar_lista_emails(lista_emails):
        """
        Valida uma lista de emails
        
        Args:
            lista_emails (list): Lista de emails para validação
        
        Returns:
            dict: Resultado da validação de todos os emails
        """
        resultados = []
        emails_validos = []
        emails_invalidos = []
        
        for email in lista_emails:
            resultado = EmailValidador.validar_email(email)
            resultados.append(resultado)
            
            if resultado['valido']:
                emails_validos.append(resultado['email_normalizado'])
            else:
                emails_invalidos.append({
                    'email_original': email,
                    'motivo': resultado['motivo']
                })
        
        return {
            'total_emails': len(lista_emails),
            'emails_validos': emails_validos,
            'emails_invalidos': emails_invalidos,
            'taxa_validade': len(emails_validos) / len(lista_emails) * 100 if lista_emails else 0
        }
    
    @staticmethod
    def filtrar_emails_validos(lista_emails):
        """
        Filtra apenas emails válidos de uma lista
        
        Args:
            lista_emails (list): Lista de emails para filtrar
        
        Returns:
            list: Lista de emails válidos
        """
        return [
            email for email in lista_emails 
            if EmailValidador.validar_email(email)['valido']
        ]

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Exemplo de uso
if __name__ == '__main__':
    # Exemplos de uso
    emails_teste = [
        'usuario@exemplo.com',
        'email_invalido',
        'outro.email@dominio.com.br',
        'nome+teste@gmail.com'
    ]
    
    # Validar lista de emails
    resultado_validacao = EmailValidador.validar_lista_emails(emails_teste)
    print("Resultado da Validação:")
    print(f"Total de Emails: {resultado_validacao['total_emails']}")
    print(f"Emails Válidos: {resultado_validacao['emails_validos']}")
    print(f"Emails Inválidos: {resultado_validacao['emails_invalidos']}")
    print(f"Taxa de Validade: {resultado_validacao['taxa_validade']:.2f}%")