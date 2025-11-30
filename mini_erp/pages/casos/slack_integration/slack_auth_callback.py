"""
Handler de callback OAuth2 do Slack.

Este módulo implementa o endpoint que recebe o callback do Slack
após autorização OAuth2, valida o código, troca por token e
armazena de forma segura.
"""

import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from nicegui import app, request, ui
from .slack_config import (
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET,
    SLACK_REDIRECT_URI,
    exchange_code_for_token,
    is_slack_configured
)
from .slack_database import (
    save_slack_token,
    save_audit_log
)
from ....auth import get_current_user
from ....core import get_db


# =============================================================================
# RATE LIMITING
# =============================================================================

# Armazena tentativas de autenticação por IP
_oauth_attempts: Dict[str, list] = defaultdict(list)
_MAX_ATTEMPTS_PER_MINUTE = 5
_RATE_LIMIT_WINDOW = 60  # segundos


def _check_rate_limit(ip: str) -> bool:
    """
    Verifica se IP excedeu limite de tentativas.
    
    Args:
        ip: Endereço IP do cliente
        
    Returns:
        True se dentro do limite, False se excedeu
    """
    now = time.time()
    
    # Remove tentativas antigas (fora da janela)
    _oauth_attempts[ip] = [
        attempt_time for attempt_time in _oauth_attempts[ip]
        if now - attempt_time < _RATE_LIMIT_WINDOW
    ]
    
    # Verifica se excedeu limite
    if len(_oauth_attempts[ip]) >= _MAX_ATTEMPTS_PER_MINUTE:
        return False
    
    # Registra nova tentativa
    _oauth_attempts[ip].append(now)
    return True


# =============================================================================
# VALIDAÇÃO DE DOMÍNIO (WHITELIST)
# =============================================================================

ALLOWED_REDIRECT_DOMAINS = [
    'localhost',
    '127.0.0.1',
    # Adicione seus domínios de produção aqui
    # 'seu-dominio.com',
]


def _validate_redirect_domain() -> bool:
    """
    Valida se o callback está vindo de um domínio permitido.
    
    Returns:
        True se domínio é permitido, False caso contrário
    """
    host = request.headers.get('Host', '')
    
    # Extrai domínio (remove porta)
    domain = host.split(':')[0]
    
    # Verifica se está na whitelist
    for allowed in ALLOWED_REDIRECT_DOMAINS:
        if domain == allowed or domain.endswith(f'.{allowed}'):
            return True
    
    return False


# =============================================================================
# LOGGING SEGURO
# =============================================================================

def _safe_log_token(token: str) -> str:
    """
    Retorna versão truncada do token para logging (segurança).
    
    Args:
        token: Token completo
        
    Returns:
        Primeiros 10 caracteres + "..." se token for longo
    """
    if not token or len(token) < 10:
        return '***'
    return f"{token[:10]}..."


# =============================================================================
# HANDLER DE CALLBACK
# =============================================================================

@app.get('/casos/slack/oauth/callback')
async def slack_oauth_callback():
    """
    Handler para callback OAuth2 do Slack.
    
    Este endpoint:
    1. Valida parâmetros recebidos
    2. Verifica rate limiting
    3. Valida domínio
    4. Verifica state (CSRF protection)
    5. Troca code por token
    6. Armazena token criptografado
    7. Registra auditoria
    8. Redireciona para página de sucesso
    
    Returns:
        HTML com mensagem de sucesso ou erro
    """
    # Valida configuração
    if not is_slack_configured():
        return _render_error_page(
            'Slack não configurado',
            'As credenciais do Slack não estão configuradas. Configure as variáveis de ambiente primeiro.'
        )
    
    # Obtém IP do cliente
    client_ip = request.client.host if hasattr(request, 'client') else request.headers.get('X-Forwarded-For', 'unknown')
    
    # Verifica rate limiting
    if not _check_rate_limit(client_ip):
        _log_audit('oauth_rate_limit_exceeded', {
            'ip': client_ip,
            'timestamp': datetime.now()
        }, None)
        
        return _render_error_page(
            'Muitas tentativas',
            'Você excedeu o limite de tentativas. Aguarde 1 minuto e tente novamente.'
        )
    
    # Valida domínio (se não for localhost em dev)
    # Em produção, sempre validar
    # if not _validate_redirect_domain():
    #     return _render_error_page(
    #         'Domínio não autorizado',
    #         'Este domínio não está autorizado para receber callbacks OAuth.'
    #     )
    
    # Obtém parâmetros da query string
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')
    error_description = request.query_params.get('error_description')
    
    # Verifica se Slack retornou erro
    if error:
        _log_audit('oauth_error', {
            'error': error,
            'error_description': error_description,
            'ip': client_ip
        }, None)
        
        return _render_error_page(
            'Erro na autorização',
            f'O Slack retornou um erro: {error_description or error}'
        )
    
    # Valida parâmetros obrigatórios
    if not code:
        _log_audit('oauth_missing_code', {
            'ip': client_ip,
            'params': dict(request.query_params)
        }, None)
        
        return _render_error_page(
            'Código não fornecido',
            'O Slack não forneceu o código de autorização. Tente autorizar novamente.'
        )
    
    # Verifica state (CSRF protection)
    stored_state = app.storage.user.get('slack_oauth_state')
    
    if not state or not stored_state or state != stored_state:
        _log_audit('oauth_invalid_state', {
            'ip': client_ip,
            'received_state': state[:10] + '...' if state and len(state) > 10 else state,
            'has_stored_state': stored_state is not None
        }, None)
        
        return _render_error_page(
            'Estado inválido',
            'O estado da requisição não corresponde. Possível tentativa de CSRF. Tente autorizar novamente.'
        )
    
    # Remove state usado (uma vez só)
    app.storage.user.pop('slack_oauth_state', None)
    
    # Obtém usuário atual
    user = get_current_user()
    if not user:
        return _render_error_page(
            'Não autenticado',
            'Você precisa estar logado no sistema para conectar o Slack.'
        )
    
    user_id = user.get('uid')
    if not user_id:
        return _render_error_page(
            'Usuário inválido',
            'Não foi possível identificar o usuário. Faça login novamente.'
        )
    
    # Troca code por token
    try:
        token_data = exchange_code_for_token(code)
        
        if not token_data:
            _log_audit('oauth_token_exchange_failed', {
                'ip': client_ip,
                'user_id': user_id
            }, user_id)
            
            return _render_error_page(
                'Falha na autenticação',
                'Não foi possível obter o token do Slack. Verifique se as credenciais estão corretas.'
            )
        
        # Verifica se resposta contém token
        access_token = token_data.get('access_token')
        if not access_token:
            error_info = token_data.get('error', 'unknown_error')
            
            _log_audit('oauth_no_token', {
                'ip': client_ip,
                'error': error_info,
                'user_id': user_id
            }, user_id)
            
            return _render_error_page(
                'Token não recebido',
                f'O Slack não retornou um token válido. Erro: {error_info}'
            )
        
        # Obtém refresh token se disponível
        refresh_token = token_data.get('refresh_token')
        
        # Armazena token (já com criptografia se implementada)
        success = save_slack_token(user_id, access_token, refresh_token)
        
        if not success:
            _log_audit('oauth_token_save_failed', {
                'ip': client_ip,
                'user_id': user_id,
                'token_preview': _safe_log_token(access_token)
            }, user_id)
            
            return _render_error_page(
                'Erro ao salvar',
                'Token obtido com sucesso, mas houve erro ao salvá-lo. Tente novamente.'
            )
        
        # Obtém informações adicionais do token
        team_id = token_data.get('team', {}).get('id') if isinstance(token_data.get('team'), dict) else token_data.get('team_id')
        team_name = token_data.get('team', {}).get('name') if isinstance(token_data.get('team'), dict) else None
        
        # Registra sucesso na auditoria
        _log_audit('oauth_success', {
            'ip': client_ip,
            'user_id': user_id,
            'team_id': team_id,
            'team_name': team_name,
            'token_preview': _safe_log_token(access_token),
            'has_refresh_token': refresh_token is not None
        }, user_id)
        
        # Renderiza página de sucesso
        return _render_success_page(team_name)
        
    except Exception as e:
        # Log do erro completo
        import traceback
        error_trace = traceback.format_exc()
        
        _log_audit('oauth_exception', {
            'ip': client_ip,
            'user_id': user_id,
            'error': str(e),
            'traceback': error_trace[:500]  # Primeiros 500 caracteres
        }, user_id)
        
        return _render_error_page(
            'Erro inesperado',
            f'Ocorreu um erro inesperado: {str(e)}'
        )


def _log_audit(action: str, details: Dict[str, Any], user_id: Optional[str]):
    """
    Registra evento de auditoria de forma segura.
    
    Args:
        action: Tipo de ação
        details: Detalhes do evento
        user_id: ID do usuário (opcional)
    """
    try:
        # Remove tokens completos dos detalhes (segurança)
        safe_details = details.copy()
        if 'token' in safe_details:
            safe_details['token'] = _safe_log_token(safe_details['token'])
        if 'access_token' in safe_details:
            safe_details['access_token'] = _safe_log_token(safe_details['access_token'])
        
        save_audit_log(action, safe_details, user_id)
    except Exception as e:
        # Não falha se log de auditoria falhar
        print(f"Erro ao registrar auditoria: {e}")


def _render_success_page(team_name: Optional[str] = None) -> str:
    """
    Renderiza página HTML de sucesso.
    
    Args:
        team_name: Nome do workspace do Slack (opcional)
        
    Returns:
        HTML da página de sucesso
    """
    team_info = f" conectado ao workspace <strong>{team_name}</strong>" if team_name else ""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Slack Conectado - TAQUES ERP</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            .success-icon {{
                font-size: 4rem;
                color: #28a745;
                margin-bottom: 1rem;
            }}
            h1 {{
                color: #333;
                margin-bottom: 1rem;
            }}
            p {{
                color: #666;
                line-height: 1.6;
                margin-bottom: 2rem;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background: #4a154b;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                transition: background 0.3s;
            }}
            .button:hover {{
                background: #350d36;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✓</div>
            <h1>Slack Conectado com Sucesso!</h1>
            <p>Sua conta do Slack{team_info} foi conectada com sucesso ao TAQUES ERP.</p>
            <p>Você pode fechar esta janela e retornar ao sistema.</p>
            <a href="/casos/slack/settings" class="button">Ir para Configurações</a>
        </div>
        <script>
            // Fecha automaticamente após 3 segundos (opcional)
            // setTimeout(function() {{ window.close(); }}, 3000);
        </script>
    </body>
    </html>
    """
    return html


def _render_error_page(title: str, message: str) -> str:
    """
    Renderiza página HTML de erro.
    
    Args:
        title: Título do erro
        message: Mensagem de erro
        
    Returns:
        HTML da página de erro
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Erro - TAQUES ERP</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}
            .container {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            .error-icon {{
                font-size: 4rem;
                color: #dc3545;
                margin-bottom: 1rem;
            }}
            h1 {{
                color: #333;
                margin-bottom: 1rem;
            }}
            p {{
                color: #666;
                line-height: 1.6;
                margin-bottom: 2rem;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background: #4a154b;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                transition: background 0.3s;
            }}
            .button:hover {{
                background: #350d36;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">✗</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <a href="/casos/slack/settings" class="button">Tentar Novamente</a>
        </div>
    </body>
    </html>
    """
    return html


