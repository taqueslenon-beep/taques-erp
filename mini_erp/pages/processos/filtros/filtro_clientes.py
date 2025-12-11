"""
filtro_clientes.py - Filtro por clientes e partes.

Filtra processos por clientes, parte e parte contrária.
"""

from typing import List, Dict, Any


def aplicar_filtro_clientes(rows: List[Dict[str, Any]], valor_filtro: str) -> List[Dict[str, Any]]:
    """
    Aplica filtro de clientes aos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
        valor_filtro: Valor do filtro de clientes
    
    Returns:
        Lista filtrada de processos
    """
    if not valor_filtro or not valor_filtro.strip():
        return rows
    
    client_filter_value = valor_filtro.strip().lower()
    filtrados = [
        r for r in rows 
        if any(
            str(c).strip().lower() == client_filter_value 
            for c in (r.get('clients_list') or [])
        )
    ]
    
    return filtrados


def aplicar_filtro_parte_contraria(rows: List[Dict[str, Any]], valor_filtro: str) -> List[Dict[str, Any]]:
    """
    Aplica filtro de parte contrária aos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
        valor_filtro: Valor do filtro de parte contrária
    
    Returns:
        Lista filtrada de processos
    """
    if not valor_filtro or not valor_filtro.strip():
        return rows
    
    opposing_filter_value = valor_filtro.strip().lower()
    filtrados = [
        r for r in rows 
        if any(
            str(c).strip().lower() == opposing_filter_value 
            for c in (r.get('opposing_list') or [])
        )
    ]
    
    return filtrados


def obter_opcoes_clientes(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Extrai opções únicas de clientes dos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
    
    Returns:
        Lista de clientes únicos, ordenados
    """
    clients = set()
    for r in rows:
        clients_list = r.get('clients_list', []) or []
        for c in clients_list:
            if c and str(c).strip() and str(c).strip() != 'NA':
                clients.add(str(c).strip())
    
    return [''] + sorted(clients)


def obter_opcoes_parte_contraria(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Extrai opções únicas de parte contrária dos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
    
    Returns:
        Lista de partes contrárias únicas, ordenadas
    """
    opposing = set()
    for r in rows:
        opposing_list = r.get('opposing_list', []) or []
        for o in opposing_list:
            if o and str(o).strip() and str(o).strip() != 'NA':
                opposing.add(str(o).strip())
    
    return [''] + sorted(opposing)







