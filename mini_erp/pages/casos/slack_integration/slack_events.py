"""
Handler de eventos webhook do Slack (Event Subscriptions).

Este módulo gerencia:
- Validação de assinatura de webhooks
- Processamento de eventos do Slack
- Atualização de cache de mensagens em tempo real
"""

import hmac
import hashlib
import time
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .slack_config import SLACK_SIGNING_SECRET
from .slack_database import (
    save_message_to_cache,
    get_linked_channel_for_case,
    get_cached_messages
)
from .slack_models import SlackMessage


def verify_slack_signature(timestamp: str, body: str, signature: str) -> bool:
    """
    Verifica assinatura do webhook do Slack para garantir autenticidade.
    
    O Slack usa HMAC SHA256 para assinar requisições. A assinatura é calculada
    concatenando a versão ('v0'), timestamp e body, depois calculando HMAC.
    
    Args:
        timestamp: Timestamp da requisição (header X-Slack-Request-Timestamp)
        body: Corpo da requisição (string raw)
        signature: Assinatura recebida (header X-Slack-Signature)
        
    Returns:
        True se a assinatura é válida, False caso contrário
    """
    if not SLACK_SIGNING_SECRET:
        print("AVISO: SLACK_SIGNING_SECRET não configurado, validando sem verificação")
        return True
    
    # Verifica timestamp (rejeita requisições muito antigas, evita replay attacks)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        
        # Rejeita se diferença maior que 5 minutos
        if abs(current_time - request_time) > 300:
            print(f"AVISO: Timestamp muito antigo: {request_time}, atual: {current_time}")
            return False
    except (ValueError, TypeError):
        return False
    
    # Calcula assinatura esperada
    sig_basestring = f"v0:{timestamp}:{body}"
    computed_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Compara assinaturas usando comparação segura (evita timing attacks)
    return hmac.compare_digest(computed_signature, signature)


def handle_message_event(event: Dict[str, Any], channel_id: str) -> bool:
    """
    Processa evento de nova mensagem do Slack.
    
    Quando uma nova mensagem é enviada em um canal vinculado a um caso,
    atualiza o cache local.
    
    Args:
        event: Dados do evento (do webhook)
        channel_id: ID do canal onde a mensagem foi enviada
        
    Returns:
        True se processado com sucesso
    """
    try:
        # Ignora mensagens de bots se necessário
        subtype = event.get('subtype')
        if subtype in ['bot_message', 'channel_join', 'channel_leave']:
            # Pode processar se quiser, mas geralmente não são relevantes
            pass
        
        # Adiciona channel_id se não estiver presente
        message_data = event.copy()
        if 'channel' not in message_data:
            message_data['channel'] = channel_id
        
        # Salva no cache
        save_message_to_cache(channel_id, message_data, cache_ttl_hours=24)
        
        # TODO: Notificar clientes conectados via WebSocket se implementado
        
        return True
    except Exception as e:
        print(f"Erro ao processar evento de mensagem: {e}")
        return False


def handle_slack_event(event_type: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler principal para eventos do Slack.
    
    Processa diferentes tipos de eventos recebidos via webhook:
    - message: Nova mensagem em canal
    - message.changed: Mensagem editada
    - message.deleted: Mensagem deletada
    - channel_created, channel_deleted, etc.
    
    Args:
        event_type: Tipo do evento (ex: 'message', 'message.changed')
        event: Dados do evento
        
    Returns:
        Dicionário com resultado do processamento
    """
    try:
        channel_id = event.get('channel')
        
        if not channel_id:
            return {'success': False, 'error': 'channel_id não encontrado no evento'}
        
        # Verifica se o canal está vinculado a algum caso
        # (por enquanto, processa todos os canais, mas pode filtrar depois)
        
        if event_type == 'message':
            success = handle_message_event(event, channel_id)
            return {
                'success': success,
                'processed': True,
                'event_type': event_type
            }
        
        elif event_type == 'message.changed':
            # Mensagem editada - atualiza cache
            message_data = event.get('message', {})
            if message_data:
                message_data['channel'] = channel_id
                save_message_to_cache(channel_id, message_data, cache_ttl_hours=24)
            return {'success': True, 'processed': True, 'event_type': event_type}
        
        elif event_type == 'message.deleted':
            # Mensagem deletada - remove do cache se necessário
            # Por enquanto, apenas marca como deletada (não remove)
            ts = event.get('deleted_ts')
            if ts:
                # TODO: Implementar remoção ou marcação de mensagem deletada
                pass
            return {'success': True, 'processed': True, 'event_type': event_type}
        
        else:
            # Evento não suportado (apenas log, não erro)
            return {
                'success': True,
                'processed': False,
                'event_type': event_type,
                'message': 'Tipo de evento não processado'
            }
    
    except Exception as e:
        print(f"Erro ao processar evento Slack: {e}")
        return {'success': False, 'error': str(e)}


def process_webhook_request(request_body: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Processa requisição webhook completa do Slack.
    
    Esta função deve ser chamada pelo endpoint HTTP que recebe webhooks.
    
    Args:
        request_body: Corpo da requisição (string raw)
        headers: Headers HTTP (deve conter X-Slack-Signature e X-Slack-Request-Timestamp)
        
    Returns:
        Dicionário com resultado do processamento
    """
    try:
        # Verifica assinatura
        signature = headers.get('X-Slack-Signature', '')
        timestamp = headers.get('X-Slack-Request-Timestamp', '')
        
        if not verify_slack_signature(timestamp, request_body, signature):
            return {'success': False, 'error': 'Assinatura inválida'}
        
        # Parse do body
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON inválido: {str(e)}'}
        
        # Verifica tipo de requisição
        request_type = data.get('type')
        
        if request_type == 'url_verification':
            # Slack envia este tipo para verificar URL do webhook
            challenge = data.get('challenge')
            return {
                'success': True,
                'type': 'challenge',
                'challenge': challenge
            }
        
        elif request_type == 'event_callback':
            # Evento real do Slack
            event = data.get('event', {})
            event_type = event.get('type')
            
            if event_type:
                result = handle_slack_event(event_type, event)
                return {
                    'success': result.get('success', False),
                    'processed': result.get('processed', False),
                    'event_type': event_type
                }
            else:
                return {'success': False, 'error': 'Tipo de evento não especificado'}
        
        else:
            return {
                'success': False,
                'error': f'Tipo de requisição não suportado: {request_type}'
            }
    
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return {'success': False, 'error': str(e)}





