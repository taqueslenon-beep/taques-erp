"""
Componentes de UI NiceGUI para exibição de mensagens do Slack.

Este módulo contém:
- Componente de thread do Slack
- Renderização de mensagens individuais
- Modal de vinculação de canal
- Indicadores de status
"""

from nicegui import ui, run
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import asyncio

from .slack_models import SlackMessage, SlackUser, SlackChannel
from .slack_api import SlackAPI
from .slack_database import (
    get_linked_channel_for_case,
    link_channel_to_case,
    unlink_channel_from_case,
    get_cached_messages,
    save_message_to_cache
)
from .slack_config import get_slack_token_for_user, is_slack_configured


# =============================================================================
# CSS CUSTOMIZADO
# =============================================================================

SLACK_UI_CSS = '''
<style>
.slack-thread-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    max-height: 600px;
    overflow-y: auto;
}

.slack-message {
    display: flex;
    gap: 12px;
    padding: 12px;
    margin-bottom: 8px;
    background: white;
    border-radius: 8px;
    border-left: 3px solid transparent;
    transition: all 0.2s;
}

.slack-message:hover {
    background: #f0f0f0;
    border-left-color: #4a154b;
}

.slack-message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 4px;
    flex-shrink: 0;
}

.slack-message-content {
    flex: 1;
    min-width: 0;
}

.slack-message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.slack-message-author {
    font-weight: 600;
    color: #1264a3;
}

.slack-message-timestamp {
    color: #616061;
    font-size: 12px;
}

.slack-message-text {
    color: #1d1c1d;
    line-height: 1.5;
    word-wrap: break-word;
}

.slack-message-reactions {
    display: flex;
    gap: 4px;
    margin-top: 8px;
    flex-wrap: wrap;
}

.slack-reaction {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    background: #f0f0f0;
    border-radius: 12px;
    font-size: 12px;
}

.slack-channel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    background: white;
    border-radius: 8px 8px 0 0;
    border-bottom: 1px solid #e0e0e0;
}

.slack-empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #616061;
}

.slack-loading {
    text-align: center;
    padding: 20px;
    color: #616061;
}
</style>
'''


def format_slack_text(text: str) -> str:
    """
    Formata texto do Slack para HTML básico.
    
    Converte:
    - <@U123> para menções de usuário
    - <#C123> para menções de canal
    - Links <http://...|texto> para links HTML
    - *texto* para negrito
    - _texto_ para itálico
    
    Args:
        text: Texto bruto do Slack
        
    Returns:
        Texto formatado em HTML
    """
    import re
    
    # Escapa HTML existente
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Links com formato <http://url|texto>
    text = re.sub(r'&lt;(https?://[^|]+)\|([^&]+)&gt;', r'<a href="\1" target="_blank">\2</a>', text)
    
    # Links simples <http://url>
    text = re.sub(r'&lt;(https?://[^&]+)&gt;', r'<a href="\1" target="_blank">\1</a>', text)
    
    # Menções de usuário <@U123>
    text = re.sub(r'&lt;@([^&]+)&gt;', r'<span class="slack-mention">@\1</span>', text)
    
    # Menções de canal <#C123>
    text = re.sub(r'&lt;#([^|]+)\|([^&]+)&gt;', r'<span class="slack-channel-mention">#\2</span>', text)
    text = re.sub(r'&lt;#([^&]+)&gt;', r'<span class="slack-channel-mention">#\1</span>', text)
    
    # Negrito *texto*
    text = re.sub(r'\*([^*]+)\*', r'<strong>\1</strong>', text)
    
    # Itálico _texto_
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
    
    # Quebras de linha
    text = text.replace('\n', '<br>')
    
    return text


def format_timestamp(ts: str) -> str:
    """
    Formata timestamp do Slack para exibição legível.
    
    Args:
        ts: Timestamp do Slack (ex: "1609459200.123456")
        
    Returns:
        String formatada (ex: "15/01/2021 14:30")
    """
    try:
        dt = datetime.fromtimestamp(float(ts))
        return dt.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return ts


def render_slack_message(message: SlackMessage, user_cache: Optional[Dict[str, SlackUser]] = None) -> str:
    """
    Renderiza uma mensagem do Slack em HTML.
    
    Args:
        message: Objeto SlackMessage
        user_cache: Cache opcional de usuários
        
    Returns:
        HTML da mensagem
    """
    user = message.user
    
    if user_cache and message.user_id and not user:
        user = user_cache.get(message.user_id)
    
    # Informações do autor
    author_name = user.get_display_name() if user else 'Usuário Desconhecido'
    avatar_url = user.get_avatar_url(48) if user else 'https://via.placeholder.com/48'
    
    # Timestamp formatado
    timestamp_str = format_timestamp(message.ts)
    
    # Texto formatado
    text_html = format_slack_text(message.text)
    
    # Reações
    reactions_html = ''
    if message.reactions:
        reactions = []
        for reaction in message.reactions:
            name = reaction.get('name', '')
            count = reaction.get('count', 0)
            reactions.append(f'<span class="slack-reaction">{name} {count}</span>')
        reactions_html = f'<div class="slack-message-reactions">{"".join(reactions)}</div>'
    
    # Build HTML
    html = f'''
    <div class="slack-message">
        <img src="{avatar_url}" alt="{author_name}" class="slack-message-avatar" />
        <div class="slack-message-content">
            <div class="slack-message-header">
                <span class="slack-message-author">{author_name}</span>
                <span class="slack-message-timestamp">{timestamp_str}</span>
            </div>
            <div class="slack-message-text">{text_html}</div>
            {reactions_html}
        </div>
    </div>
    '''
    
    return html


class SlackThreadComponent:
    """
    Componente NiceGUI para exibir thread de mensagens do Slack.
    
    Gerencia:
    - Carregamento de mensagens
    - Atualização automática
    - Cache local
    - Estados de erro
    """
    
    def __init__(self, case_slug: str, user_id: str):
        """
        Inicializa componente.
        
        Args:
            case_slug: Slug do caso jurídico
            user_id: ID do usuário logado
        """
        self.case_slug = case_slug
        self.user_id = user_id
        self.messages: List[SlackMessage] = []
        self.user_cache: Dict[str, SlackUser] = {}
        self.channel_id: Optional[str] = None
        self.channel_name: Optional[str] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._is_loading = False
    
    async def load_messages(self, limit: int = 50) -> bool:
        """
        Carrega mensagens do canal vinculado ao caso.
        
        Args:
            limit: Número máximo de mensagens
            
        Returns:
            True se carregado com sucesso
        """
        try:
            self._is_loading = True
            
            # Verifica se Slack está configurado
            if not is_slack_configured():
                return False
            
            # Busca canal vinculado
            linked_channel = await run.io_bound(get_linked_channel_for_case, self.case_slug)
            
            if not linked_channel:
                return False
            
            self.channel_id = linked_channel.get('channel_id')
            self.channel_name = linked_channel.get('channel_name')
            
            if not self.channel_id:
                return False
            
            # Busca token do usuário
            token = await run.io_bound(get_slack_token_for_user, self.user_id)
            
            if not token:
                return False
            
            # Busca mensagens da API
            api = SlackAPI(token)
            messages_data = api.get_all_channel_messages(self.channel_id, limit=limit)
            
            # Carrega usuários e converte para modelos
            self.messages = []
            for msg_data in messages_data:
                user_id_msg = msg_data.get('user')
                
                # Carrega usuário se não estiver no cache
                if user_id_msg and user_id_msg not in self.user_cache:
                    user_data = api.get_user_info(user_id_msg)
                    if user_data:
                        self.user_cache[user_id_msg] = SlackUser.from_api_data(user_data)
                
                message = SlackMessage.from_api_data(msg_data, self.channel_id, self.user_cache)
                self.messages.append(message)
                
                # Salva no cache local
                await run.io_bound(save_message_to_cache, self.channel_id, msg_data)
            
            self._is_loading = False
            return True
            
        except Exception as e:
            print(f"Erro ao carregar mensagens: {e}")
            self._is_loading = False
            return False
    
    def render(self) -> ui.element:
        """
        Renderiza componente completo na UI.
        
        Returns:
            Elemento NiceGUI do componente
        """
        ui.add_head_html(SLACK_UI_CSS)
        
        container = ui.column().classes('slack-thread-container w-full')
        
        # Header do canal
        with container:
            with ui.row().classes('slack-channel-header w-full'):
                if self.channel_name:
                    ui.label(f'#{self.channel_name}').classes('text-lg font-bold')
                else:
                    ui.label('Slack').classes('text-lg font-bold')
                
                with ui.row().classes('gap-2'):
                    ui.button('Atualizar', icon='refresh', on_click=self.refresh).props('flat size=sm')
            
            # Container de mensagens
            self.messages_container = ui.column().classes('w-full gap-2')
            
            # Estado inicial
            self.status_label = ui.label('Carregando mensagens...').classes('slack-loading')
        
        # Carrega mensagens inicialmente
        asyncio.create_task(self._initial_load())
        
        return container
    
    async def _initial_load(self):
        """Carrega mensagens na inicialização."""
        success = await self.load_messages()
        await self._update_display()
        
        if not success:
            self.status_label.text = 'Nenhum canal Slack vinculado ou token não configurado.'
    
    async def _update_display(self):
        """Atualiza exibição das mensagens."""
        self.status_label.visible = False
        self.messages_container.clear()
        
        if not self.messages:
            with self.messages_container:
                ui.label('Nenhuma mensagem encontrada.').classes('slack-empty-state')
            return
        
        with self.messages_container:
            for message in self.messages:
                html = render_slack_message(message, self.user_cache)
                ui.html(html)
    
    async def refresh(self):
        """Recarrega mensagens."""
        success = await self.load_messages()
        await self._update_display()
        
        if success:
            ui.notify('Mensagens atualizadas!', type='positive')
        else:
            ui.notify('Erro ao atualizar mensagens.', type='negative')


def create_channel_link_modal(case_slug: str, user_id: str, on_linked: Optional[Callable] = None):
    """
    Cria modal para vincular canal do Slack a um caso.
    
    Args:
        case_slug: Slug do caso
        user_id: ID do usuário logado
        on_linked: Callback executado quando canal é vinculado
        
    Returns:
        Dialog do NiceGUI
    """
    
    with ui.dialog() as dialog, ui.card().classes('p-6 w-96'):
        ui.label('Vincular Canal Slack').classes('text-xl font-bold mb-4')
        
        # Verifica se token está configurado
        token = get_slack_token_for_user(user_id)
        
        if not token:
            ui.label('Token do Slack não configurado. Configure primeiro nas configurações.').classes('text-red-500')
            with ui.row().classes('mt-4 justify-end'):
                ui.button('Fechar', on_click=dialog.close)
            return dialog
        
        # Campo de busca
        search_input = ui.input('Buscar canal', placeholder='Digite o nome do canal...')
        search_results = ui.column().classes('mt-4 max-h-64 overflow-y-auto')
        
        async def search_channels():
            """Busca canais do Slack."""
            try:
                query = search_input.value
                if not query:
                    search_results.clear()
                    return
                
                search_results.clear()
                
                with search_results:
                    ui.label('Buscando...').classes('text-gray-500')
                
                api = SlackAPI(token)
                channels = api.search_channels(query)
                
                search_results.clear()
                
                if not channels:
                    with search_results:
                        ui.label('Nenhum canal encontrado.').classes('text-gray-500')
                    return
                
                with search_results:
                    for channel_data in channels[:10]:  # Limita a 10 resultados
                        channel = SlackChannel.from_api_data(channel_data)
                        
                        def link_channel(ch=channel):
                            async def do_link():
                                success = await run.io_bound(
                                    link_channel_to_case,
                                    case_slug,
                                    ch.id,
                                    ch.name,
                                    user_id
                                )
                                if success:
                                    ui.notify(f'Canal #{ch.name} vinculado!', type='positive')
                                    dialog.close()
                                    if on_linked:
                                        on_linked()
                                else:
                                    ui.notify('Erro ao vincular canal.', type='negative')
                            
                            return do_link
                        
                        with ui.card().classes('p-3 cursor-pointer hover:bg-gray-100'):
                            ui.label(ch.display_name).classes('font-semibold')
                            if ch.topic:
                                ui.label(ch.topic).classes('text-sm text-gray-600')
                            ui.button('Vincular', on_click=link_channel()).props('flat size=sm').classes('mt-2')
            
            except Exception as e:
                print(f"Erro ao buscar canais: {e}")
                ui.notify('Erro ao buscar canais.', type='negative')
        
        search_input.on('keydown.enter', search_channels)
        ui.button('Buscar', icon='search', on_click=search_channels).classes('mt-2')
        
        with ui.row().classes('mt-4 justify-end'):
            ui.button('Cancelar', on_click=dialog.close)
    
    return dialog

