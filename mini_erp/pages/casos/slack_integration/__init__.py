"""
Módulo de integração com Slack para exibir mensagens de canais
dentro da página de detalhes de casos jurídicos.
"""

# Importa callback OAuth para registrar rota automaticamente
from . import slack_auth_callback  # noqa: F401

from .slack_config import (
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET,
    SLACK_SIGNING_SECRET,
    SLACK_REDIRECT_URI,
    get_slack_token_for_user,
    save_slack_token_for_user
)

from .slack_api import (
    SlackAPI,
    fetch_channel_messages,
    search_channels
)

from .slack_models import (
    SlackMessage,
    SlackChannel,
    SlackUser
)

from .slack_database import (
    save_slack_token,
    get_slack_token,
    link_channel_to_case,
    get_linked_channel_for_case,
    save_message_to_cache,
    get_cached_messages,
    get_message_by_ts,
    delete_message_from_cache,
    save_audit_log
)

from .slack_events import (
    verify_slack_signature,
    handle_slack_event,
    handle_message_event
)

from .slack_ui import (
    SlackThreadComponent,
    render_slack_message,
    create_channel_link_modal
)

__all__ = [
    'SLACK_CLIENT_ID',
    'SLACK_CLIENT_SECRET',
    'SLACK_SIGNING_SECRET',
    'SLACK_REDIRECT_URI',
    'get_slack_token_for_user',
    'save_slack_token_for_user',
    'SlackAPI',
    'fetch_channel_messages',
    'search_channels',
    'SlackMessage',
    'SlackChannel',
    'SlackUser',
    'save_slack_token',
    'get_slack_token',
    'link_channel_to_case',
    'get_linked_channel_for_case',
    'save_message_to_cache',
    'get_cached_messages',
    'get_message_by_ts',
    'delete_message_from_cache',
    'save_audit_log',
    'verify_slack_signature',
    'handle_slack_event',
    'handle_message_event',
    'SlackThreadComponent',
    'render_slack_message',
    'create_channel_link_modal'
]

