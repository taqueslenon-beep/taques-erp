"""
Página de configuração da integração Slack.

Permite:
- Conectar conta Slack via OAuth2
- Visualizar status da conexão
- Desconectar conta
- Gerenciar canais vinculados
"""

from nicegui import ui, app, run
from typing import Optional
import asyncio

from ...core import layout
from ...auth import is_authenticated, get_current_user
from .slack_config import (
    is_slack_configured,
    get_slack_token_for_user,
    get_configuration_status
)
from .slack_database import (
    save_slack_token,
    get_slack_token,
    delete_slack_token,
    get_audit_logs
)
from .slack_api import SlackAPI


def slack_settings_page():
    """
    Página de configuração da integração Slack.
    Rota: /casos/slack/settings
    """
    import asyncio
    
    if not is_authenticated():
        ui.open('/login')
        return
    
    user = get_current_user()
    if not user:
        ui.open('/login')
        return
    
    user_id = user.get('uid')
    if not user_id:
        ui.open('/login')
        return
    
    layout('Configurações Slack')
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-6 gap-6'):
        ui.label('Integração com Slack').classes('text-3xl font-bold mb-2')
        ui.label('Configure sua conta Slack para exibir mensagens nos casos jurídicos.').classes('text-gray-600 mb-6')
        
        # Status da configuração
        with ui.card().classes('w-full p-6'):
            ui.label('Status da Configuração').classes('text-xl font-semibold mb-4')
            
            config_status = ui.label('Verificando...').classes('text-lg')
            token_status = ui.label('').classes('text-sm text-gray-600')
            
            async def check_status():
                """Verifica status da configuração."""
                # Verifica se credenciais estão configuradas
                if not is_slack_configured():
                    config_status.text = '❌ Slack não configurado'
                    config_status.classes(remove='text-green-600 text-red-600', add='text-red-600')
                    token_status.text = 'As credenciais do Slack (Client ID, Secret) não estão configuradas.'
                    return
                
                config_status.text = '✅ Slack configurado'
                config_status.classes(remove='text-green-600 text-red-600', add='text-green-600')
                
                # Verifica se usuário tem token
                token = await run.io_bound(get_slack_token_for_user, user_id)
                
                if token:
                    # Testa conexão
                    try:
                        api = SlackAPI(token)
                        test_result = api.test_connection()
                        
                        if test_result:
                            token_status.text = '✅ Conta conectada e funcionando'
                            token_status.classes(remove='text-green-600 text-red-600', add='text-green-600')
                        else:
                            token_status.text = '⚠️ Token inválido ou expirado'
                            token_status.classes(remove='text-green-600 text-red-600', add='text-orange-600')
                    except Exception as e:
                        token_status.text = f'❌ Erro ao conectar: {str(e)}'
                        token_status.classes(remove='text-green-600 text-red-600', add='text-red-600')
                else:
                    token_status.text = 'Não conectado. Clique em "Conectar Slack" para começar.'
                    token_status.classes(remove='text-green-600 text-red-600', add='text-gray-600')
            
            asyncio.create_task(check_status())
        
        # Botões de ação
        with ui.card().classes('w-full p-6'):
            ui.label('Ações').classes('text-xl font-semibold mb-4')
            
            connect_button = ui.button('Conectar Slack', icon='link', color='primary')
            disconnect_button = ui.button('Desconectar', icon='link_off', color='red')
            refresh_button = ui.button('Atualizar Status', icon='refresh', color='secondary')
            
            async def connect_slack():
                """Inicia processo de conexão OAuth."""
                if not is_slack_configured():
                    ui.notify('Slack não está configurado. Configure as credenciais primeiro.', type='negative')
                    return
                
                # Importa função atualizada
                from .slack_config import get_oauth_url, generate_state_token
                
                # Gera state para segurança CSRF
                state = generate_state_token()
                app.storage.user['slack_oauth_state'] = state
                
                # Gera URL de autorização
                auth_url = get_oauth_url(state)
                
                # Abre em nova aba
                ui.open(auth_url, new_tab=True)
                
                ui.notify('Redirecionando para autorização do Slack...', type='info')
            
            async def disconnect_slack():
                """Desconecta conta Slack."""
                result = ui.dialog()
                with result, ui.card().classes('p-6'):
                    ui.label('Desconectar Slack?').classes('text-xl font-semibold mb-4')
                    ui.label('Todas as integrações com canais serão mantidas, mas não será possível buscar novas mensagens.').classes('mb-4')
                    
                    with ui.row().classes('gap-2 justify-end'):
                        ui.button('Cancelar', on_click=result.close)
                        async def confirm_disconnect():
                            success = await run.io_bound(delete_slack_token, user_id)
                            if success:
                                ui.notify('Conta desconectada com sucesso!', type='positive')
                                await check_status()
                            else:
                                ui.notify('Erro ao desconectar.', type='negative')
                            result.close()
                        
                        ui.button('Desconectar', on_click=confirm_disconnect, color='red')
                
                result.open()
            
            connect_button.on('click', connect_slack)
            disconnect_button.on('click', disconnect_slack)
            refresh_button.on('click', check_status)
        
        # Logs de auditoria
        with ui.card().classes('w-full p-6'):
            ui.label('Logs de Auditoria').classes('text-xl font-semibold mb-4')
            
            logs_container = ui.column().classes('w-full')
            
            async def load_audit_logs():
                """Carrega logs de auditoria."""
                logs = await run.io_bound(get_audit_logs, user_id=user_id, limit=20)
                
                logs_container.clear()
                
                if not logs:
                    with logs_container:
                        ui.label('Nenhum log encontrado.').classes('text-gray-500')
                    return
                
                with logs_container:
                    for log in logs:
                        action = log.get('action', 'unknown')
                        timestamp = log.get('timestamp')
                        details = log.get('details', {})
                        
                        if timestamp:
                            from datetime import datetime
                            if isinstance(timestamp, str):
                                dt = datetime.fromisoformat(timestamp)
                            else:
                                dt = timestamp
                            time_str = dt.strftime('%d/%m/%Y %H:%M')
                        else:
                            time_str = 'Data desconhecida'
                        
                        with ui.card().classes('p-3 mb-2'):
                            ui.label(f'{action} - {time_str}').classes('font-semibold')
                            if details:
                                ui.label(str(details)).classes('text-sm text-gray-600')
            
            asyncio.create_task(load_audit_logs())
            ui.button('Atualizar Logs', icon='refresh', on_click=load_audit_logs).classes('mt-4')
    
    # Nota: O handler de callback OAuth está em slack_auth_callback.py
    # e é registrado automaticamente quando o módulo é importado


def setup_slack_routes(app):
    """
    Configura rotas do Slack no app NiceGUI.
    
    Args:
        app: Instância do app NiceGUI
    """
    app.add_page(slack_settings_page, '/casos/slack/settings')

