"""
Módulo de acesso a dados para o módulo Pessoas.
Wrappers para operações CRUD do core.py com cache invalidation.
"""
from typing import List, Dict, Any, Optional
from ...core import (
    get_clients_list as core_get_clients_list,
    get_opposing_parties_list as core_get_opposing_parties_list,
    save_client as core_save_client,
    delete_client as core_delete_client,
    save_opposing_party as core_save_opposing_party,
    delete_opposing_party as core_delete_opposing_party,
    invalidate_cache as core_invalidate_cache,
    get_leads_list as core_get_leads_list,
    save_lead as core_save_lead,
    delete_lead as core_delete_lead,
)


def get_clients_list() -> List[Dict[str, Any]]:
    """
    Obtém lista de clientes do Firestore.
    
    Returns:
        Lista de clientes
    """
    return core_get_clients_list()


def get_opposing_parties_list() -> List[Dict[str, Any]]:
    """
    Obtém lista de outros envolvidos do Firestore.
    
    Returns:
        Lista de outros envolvidos
    """
    return core_get_opposing_parties_list()


def save_client(client: Dict[str, Any]) -> None:
    """
    Salva um cliente no Firestore.
    
    Args:
        client: Dicionário com dados do cliente
    """
    core_save_client(client)


def delete_client(client: Dict[str, Any]) -> None:
    """
    Remove um cliente do Firestore.
    
    Args:
        client: Dicionário com dados do cliente a remover
    """
    core_delete_client(client)


def save_opposing_party(opposing: Dict[str, Any]) -> None:
    """
    Salva um outro envolvido no Firestore.
    
    Args:
        opposing: Dicionário com dados do outro envolvido
    """
    core_save_opposing_party(opposing)


def delete_opposing_party(opposing: Dict[str, Any]) -> None:
    """
    Remove um outro envolvido do Firestore.
    
    Args:
        opposing: Dicionário com dados do outro envolvido a remover
    """
    core_delete_opposing_party(opposing)


def invalidate_cache(collection_name: Optional[str] = None) -> None:
    """
    Invalida o cache de uma coleção específica ou de todas.
    
    Args:
        collection_name: Nome da coleção a invalidar (None para todas)
    """
    core_invalidate_cache(collection_name)
    # Se invalidar 'pessoas', também invalida cache de leads
    if collection_name == 'pessoas' or collection_name is None:
        core_invalidate_cache('pessoas_leads')


def get_client_by_index(index: int) -> Optional[Dict[str, Any]]:
    """
    Obtém um cliente pelo índice na lista.
    
    Args:
        index: Índice do cliente na lista
        
    Returns:
        Dicionário com dados do cliente ou None se índice inválido
    """
    clients = get_clients_list()
    if 0 <= index < len(clients):
        return clients[index]
    return None


def get_client_by_name(full_name: str) -> Optional[Dict[str, Any]]:
    """
    Busca um cliente pelo nome completo.
    
    Args:
        full_name: Nome completo do cliente
        
    Returns:
        Dicionário com dados do cliente ou None se não encontrado
    """
    clients = get_clients_list()
    for client in clients:
        client_full_name = client.get('full_name') or client.get('name', '')
        if client_full_name == full_name:
            return client
    return None


def get_opposing_party_by_index(index: int) -> Optional[Dict[str, Any]]:
    """
    Obtém um outro envolvido pelo índice na lista.
    
    Args:
        index: Índice do outro envolvido na lista
        
    Returns:
        Dicionário com dados do outro envolvido ou None se índice inválido
    """
    opposing_parties = get_opposing_parties_list()
    if 0 <= index < len(opposing_parties):
        return opposing_parties[index]
    return None


def get_opposing_party_by_name(full_name: str) -> Optional[Dict[str, Any]]:
    """
    Busca um outro envolvido pelo nome completo.
    
    Args:
        full_name: Nome completo do outro envolvido
        
    Returns:
        Dicionário com dados do outro envolvido ou None se não encontrado
    """
    opposing_parties = get_opposing_parties_list()
    for opposing in opposing_parties:
        opposing_full_name = opposing.get('full_name') or opposing.get('name', '')
        if opposing_full_name == full_name:
            return opposing
    return None


# =============================================================================
# FUNÇÕES DE LEADS
# =============================================================================

def get_leads_list() -> List[Dict[str, Any]]:
    """
    Obtém lista de leads do Firestore.
    
    Returns:
        Lista de leads
    """
    return core_get_leads_list()


def save_lead(lead: Dict[str, Any]) -> None:
    """
    Salva um lead no Firestore.
    
    Args:
        lead: Dicionário com dados do lead
    """
    core_save_lead(lead)


def delete_lead(lead: Dict[str, Any]) -> None:
    """
    Remove um lead do Firestore.
    
    Args:
        lead: Dicionário com dados do lead a remover
    """
    core_delete_lead(lead)

