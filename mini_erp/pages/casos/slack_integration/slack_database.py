"""
Operações de banco de dados para integração Slack no Firestore.

Este módulo gerencia:
- Armazenamento de tokens criptografados
- Vinculação de canais a casos
- Cache de mensagens
- Logs de auditoria
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from ....core import get_db


# =============================================================================
# GERENCIAMENTO DE TOKENS
# =============================================================================

def save_slack_token(user_id: str, access_token: str, refresh_token: Optional[str] = None,
                     encrypted: bool = False) -> bool:
    """
    Salva token do Slack no Firestore.
    
    IMPORTANTE: Em produção, o token deve ser criptografado antes de salvar.
    Por enquanto, armazena em texto plano (DEVE SER CORRIGIDO).
    
    Args:
        user_id: ID do usuário (Firebase UID)
        access_token: Token de acesso
        refresh_token: Token de refresh (opcional)
        encrypted: Se True, indica que o token já está criptografado
        
    Returns:
        True se salvo com sucesso
    """
    try:
        db = get_db()
        doc_ref = db.collection('slack_tokens').document(user_id)
        
        data = {
            'access_token': access_token,  # TODO: Criptografar antes de salvar
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'encrypted': encrypted
        }
        
        if refresh_token:
            data['refresh_token'] = refresh_token
        
        doc_ref.set(data)
        return True
    except Exception as e:
        print(f"Erro ao salvar token Slack: {e}")
        return False


def get_slack_token(user_id: str) -> Optional[str]:
    """
    Recupera token do Slack para um usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Token de acesso ou None se não encontrado
    """
    try:
        db = get_db()
        doc_ref = db.collection('slack_tokens').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            token = data.get('access_token')
            # TODO: Descriptografar token se necessário
            return token
        
        return None
    except Exception as e:
        print(f"Erro ao recuperar token Slack: {e}")
        return None


def delete_slack_token(user_id: str) -> bool:
    """
    Remove token do Slack para um usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        True se removido com sucesso
    """
    try:
        db = get_db()
        doc_ref = db.collection('slack_tokens').document(user_id)
        doc_ref.delete()
        return True
    except Exception as e:
        print(f"Erro ao deletar token Slack: {e}")
        return False


# =============================================================================
# VINCULAÇÃO DE CANAIS A CASOS
# =============================================================================

def link_channel_to_case(case_slug: str, channel_id: str, channel_name: str,
                         user_id: str) -> bool:
    """
    Vincula um canal do Slack a um caso jurídico.
    
    Args:
        case_slug: Slug do caso
        channel_id: ID do canal no Slack
        channel_name: Nome do canal
        user_id: ID do usuário que fez a vinculação (para auditoria)
        
    Returns:
        True se vinculado com sucesso
    """
    try:
        db = get_db()
        doc_ref = db.collection('case_slack_channels').document(case_slug)
        
        data = {
            'case_slug': case_slug,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'linked_by': user_id,
            'linked_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        doc_ref.set(data)
        
        # Registra auditoria
        save_audit_log('channel_linked', {
            'case_slug': case_slug,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'user_id': user_id
        })
        
        return True
    except Exception as e:
        print(f"Erro ao vincular canal ao caso: {e}")
        return False


def get_linked_channel_for_case(case_slug: str) -> Optional[Dict[str, Any]]:
    """
    Obtém canal vinculado a um caso.
    
    Args:
        case_slug: Slug do caso
        
    Returns:
        Dicionário com dados do canal ou None se não vinculado
    """
    try:
        db = get_db()
        doc_ref = db.collection('case_slack_channels').document(case_slug)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        
        return None
    except Exception as e:
        print(f"Erro ao buscar canal vinculado: {e}")
        return None


def unlink_channel_from_case(case_slug: str, user_id: str) -> bool:
    """
    Remove vinculação de canal de um caso.
    
    Args:
        case_slug: Slug do caso
        user_id: ID do usuário que fez a remoção (para auditoria)
        
    Returns:
        True se removido com sucesso
    """
    try:
        db = get_db()
        doc_ref = db.collection('case_slack_channels').document(case_slug)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            
            # Registra auditoria
            save_audit_log('channel_unlinked', {
                'case_slug': case_slug,
                'channel_id': data.get('channel_id'),
                'channel_name': data.get('channel_name'),
                'user_id': user_id
            })
            
            doc_ref.delete()
            return True
        
        return False
    except Exception as e:
        print(f"Erro ao desvincular canal: {e}")
        return False


# =============================================================================
# CACHE DE MENSAGENS
# =============================================================================

def save_message_to_cache(channel_id: str, message: Dict[str, Any],
                         cache_ttl_hours: int = 24) -> bool:
    """
    Salva mensagem no cache local.
    
    Args:
        channel_id: ID do canal
        message: Dados da mensagem
        cache_ttl_hours: Tempo de vida do cache em horas
        
    Returns:
        True se salvo com sucesso
    """
    try:
        db = get_db()
        
        # Usa ts (timestamp) como ID único da mensagem
        message_id = message.get('ts', '').replace('.', '_')  # Firestore não aceita pontos em IDs
        doc_ref = db.collection('slack_messages_cache').document(message_id)
        
        data = {
            'channel_id': channel_id,
            'message': message,
            'cached_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=cache_ttl_hours)
        }
        
        doc_ref.set(data)
        return True
    except Exception as e:
        print(f"Erro ao salvar mensagem no cache: {e}")
        return False


def get_cached_messages(channel_id: str, limit: int = 50,
                       exclude_expired: bool = True) -> List[Dict[str, Any]]:
    """
    Recupera mensagens do cache para um canal.
    
    Args:
        channel_id: ID do canal
        limit: Número máximo de mensagens
        exclude_expired: Se True, exclui mensagens expiradas
        
    Returns:
        Lista de mensagens ordenadas por timestamp (mais antigas primeiro)
    """
    try:
        db = get_db()
        query = db.collection('slack_messages_cache').where('channel_id', '==', channel_id)
        
        if exclude_expired:
            query = query.where('expires_at', '>', datetime.now())
        
        docs = query.order_by('cached_at', direction='DESCENDING').limit(limit).stream()
        
        messages = []
        for doc in docs:
            data = doc.to_dict()
            message = data.get('message')
            if message:
                messages.append(message)
        
        # Ordena por timestamp (mais antigas primeiro)
        messages.sort(key=lambda m: float(m.get('ts', 0)))
        
        return messages
    except Exception as e:
        print(f"Erro ao recuperar mensagens do cache: {e}")
        return []


def get_message_by_ts(channel_id: str, ts: str) -> Optional[Dict[str, Any]]:
    """
    Busca mensagem específica por timestamp.
    
    Args:
        channel_id: ID do canal
        ts: Timestamp da mensagem
        
    Returns:
        Dados da mensagem ou None se não encontrada
    """
    try:
        db = get_db()
        message_id = ts.replace('.', '_')
        doc_ref = db.collection('slack_messages_cache').document(message_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            if data.get('channel_id') == channel_id:
                return data.get('message')
        
        return None
    except Exception as e:
        print(f"Erro ao buscar mensagem por ts: {e}")
        return None


def delete_message_from_cache(ts: str) -> bool:
    """
    Remove mensagem do cache.
    
    Args:
        ts: Timestamp da mensagem
        
    Returns:
        True se removido com sucesso
    """
    try:
        db = get_db()
        message_id = ts.replace('.', '_')
        doc_ref = db.collection('slack_messages_cache').document(message_id)
        doc_ref.delete()
        return True
    except Exception as e:
        print(f"Erro ao deletar mensagem do cache: {e}")
        return False


def clear_expired_cache() -> int:
    """
    Remove mensagens expiradas do cache.
    
    Returns:
        Número de mensagens removidas
    """
    try:
        db = get_db()
        query = db.collection('slack_messages_cache').where('expires_at', '<=', datetime.now())
        docs = query.stream()
        
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        return count
    except Exception as e:
        print(f"Erro ao limpar cache expirado: {e}")
        return 0


# =============================================================================
# AUDITORIA
# =============================================================================

def save_audit_log(action: str, details: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """
    Salva log de auditoria para ações relacionadas ao Slack.
    
    Args:
        action: Tipo de ação (ex: 'channel_linked', 'token_saved')
        details: Detalhes da ação
        user_id: ID do usuário (opcional)
        
    Returns:
        True se salvo com sucesso
    """
    try:
        db = get_db()
        doc_ref = db.collection('slack_audit_logs').document()
        
        data = {
            'action': action,
            'details': details,
            'user_id': user_id,
            'timestamp': datetime.now()
        }
        
        doc_ref.set(data)
        return True
    except Exception as e:
        print(f"Erro ao salvar log de auditoria: {e}")
        return False


def get_audit_logs(case_slug: Optional[str] = None, user_id: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
    """
    Recupera logs de auditoria.
    
    Args:
        case_slug: Filtrar por caso (opcional)
        user_id: Filtrar por usuário (opcional)
        limit: Número máximo de logs
        
    Returns:
        Lista de logs ordenados por timestamp (mais recentes primeiro)
    """
    try:
        db = get_db()
        query = db.collection('slack_audit_logs')
        
        if case_slug:
            query = query.where('details.case_slug', '==', case_slug)
        
        if user_id:
            query = query.where('user_id', '==', user_id)
        
        docs = query.order_by('timestamp', direction='DESCENDING').limit(limit).stream()
        
        logs = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            logs.append(data)
        
        return logs
    except Exception as e:
        print(f"Erro ao recuperar logs de auditoria: {e}")
        return []

