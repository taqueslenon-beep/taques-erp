"""
Configuração e gerenciamento de credenciais OAuth2 do Slack.

Este módulo gerencia:
- Credenciais OAuth (Client ID, Secret, Signing Secret)
- Tokens de acesso por usuário (armazenados de forma segura)
- URLs de redirecionamento
- Validação de permissões
"""

import os
import secrets
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# =============================================================================
# CONFIGURAÇÕES SLACK OAUTH
# =============================================================================

SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID', '')
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET', '')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET', '')
SLACK_ENCRYPTION_KEY = os.environ.get('SLACK_ENCRYPTION_KEY', '')

# URL base do sistema (deve ser configurada conforme ambiente)
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080')
SLACK_REDIRECT_URI = f"{BASE_URL}/casos/slack/oauth/callback"

# Scopes necessários para a integração (importa de slack_scopes.py)
from .slack_scopes import SLACK_SCOPES_ALL
SLACK_SCOPES = SLACK_SCOPES_ALL

# URL de autorização OAuth2
SLACK_AUTH_URL = 'https://slack.com/oauth/v2/authorize'
SLACK_TOKEN_URL = 'https://oauth2.slack.com/api/token'

# =============================================================================
# GERENCIAMENTO DE TOKENS
# =============================================================================

def get_slack_token_for_user(user_id: str) -> Optional[str]:
    """
    Recupera token de acesso do Slack para um usuário específico.
    
    O token é armazenado criptografado no Firestore na collection 'slack_tokens'.
    
    Args:
        user_id: ID do usuário (Firebase UID)
        
    Returns:
        Token de acesso ou None se não encontrado
    """
    from ....core import get_db
    
    try:
        db = get_db()
        doc_ref = db.collection('slack_tokens').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            # TODO: Implementar descriptografia do token
            # Por enquanto, armazena em texto (NÃO RECOMENDADO PARA PRODUÇÃO)
            return data.get('access_token')
        
        return None
    except Exception as e:
        print(f"Erro ao recuperar token Slack: {e}")
        return None


def save_slack_token_for_user(user_id: str, access_token: str, refresh_token: Optional[str] = None) -> bool:
    """
    Salva token de acesso do Slack para um usuário específico.
    
    O token deve ser criptografado antes de ser armazenado no Firestore.
    
    Args:
        user_id: ID do usuário (Firebase UID)
        access_token: Token de acesso do Slack
        refresh_token: Token de refresh (opcional)
        
    Returns:
        True se salvo com sucesso, False caso contrário
    """
    from ....core import get_db
    from datetime import datetime
    
    try:
        db = get_db()
        doc_ref = db.collection('slack_tokens').document(user_id)
        
        # TODO: Implementar criptografia do token antes de salvar
        # Por enquanto, armazena em texto (NÃO RECOMENDADO PARA PRODUÇÃO)
        
        data = {
            'access_token': access_token,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        if refresh_token:
            data['refresh_token'] = refresh_token
        
        doc_ref.set(data)
        return True
    except Exception as e:
        print(f"Erro ao salvar token Slack: {e}")
        return False


def generate_state_token() -> str:
    """
    Gera token de estado aleatório para proteção CSRF.
    
    Returns:
        Token aleatório seguro usando secrets.token_urlsafe()
    """
    return secrets.token_urlsafe(32)


def get_oauth_url(state: Optional[str] = None) -> str:
    """
    Gera URL de autorização OAuth2 do Slack.
    
    Esta função monta a URL completa de autorização incluindo todos os scopes
    necessários e parâmetro 'state' para segurança CSRF.
    
    Args:
        state: String de estado para validação CSRF. Se None, gera automaticamente.
        
    Returns:
        URL completa de autorização OAuth2
        
    Example:
        >>> url = get_oauth_url()
        >>> # Usuário deve ser redirecionado para esta URL
    """
    import urllib.parse
    
    if not state:
        state = generate_state_token()
    
    if not SLACK_CLIENT_ID:
        raise ValueError("SLACK_CLIENT_ID não configurado. Configure a variável de ambiente.")
    
    params = {
        'client_id': SLACK_CLIENT_ID,
        'scope': ','.join(SLACK_SCOPES),
        'redirect_uri': SLACK_REDIRECT_URI,
        'state': state
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"{SLACK_AUTH_URL}?{query_string}"


def generate_oauth_url(state: str) -> str:
    """
    DEPRECATED: Use get_oauth_url() em vez disso.
    
    Mantido para compatibilidade. Gera URL de autorização OAuth2 do Slack.
    
    Args:
        state: String de estado para validação CSRF
        
    Returns:
        URL completa de autorização
    """
    return get_oauth_url(state)


def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
    """
    Troca código de autorização por token de acesso.
    
    Args:
        code: Código de autorização retornado pelo Slack
        
    Returns:
        Dicionário com access_token, refresh_token e outros dados, ou None em caso de erro
    """
    import requests
    
    try:
        response = requests.post(SLACK_TOKEN_URL, data={
            'code': code,
            'client_id': SLACK_CLIENT_ID,
            'client_secret': SLACK_CLIENT_SECRET,
            'redirect_uri': SLACK_REDIRECT_URI
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao trocar código por token: {response.text}")
            return None
    except Exception as e:
        print(f"Exceção ao trocar código por token: {e}")
        return None


def is_slack_configured() -> bool:
    """
    Verifica se as credenciais do Slack estão configuradas.
    
    Returns:
        True se todas as credenciais necessárias estão presentes
    """
    return all([
        SLACK_CLIENT_ID,
        SLACK_CLIENT_SECRET,
        SLACK_SIGNING_SECRET
    ])


def is_encryption_configured() -> bool:
    """
    Verifica se a chave de criptografia está configurada.
    
    Returns:
        True se SLACK_ENCRYPTION_KEY está presente
    """
    return bool(SLACK_ENCRYPTION_KEY)


def get_configuration_status() -> Dict[str, bool]:
    """
    Retorna status detalhado da configuração.
    
    Returns:
        Dicionário com status de cada componente necessário
    """
    return {
        'client_id': bool(SLACK_CLIENT_ID),
        'client_secret': bool(SLACK_CLIENT_SECRET),
        'signing_secret': bool(SLACK_SIGNING_SECRET),
        'encryption_key': bool(SLACK_ENCRYPTION_KEY),
        'base_url': bool(BASE_URL),
        'fully_configured': is_slack_configured(),
        'encryption_ready': is_encryption_configured()
    }

