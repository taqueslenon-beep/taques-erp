"""
utils_compartilhados.py - Utilitários compartilhados entre seções do módulo de Acordos.

Funções auxiliares usadas por múltiplas partes do módulo.
"""

from typing import Dict, Any, List
from ...core import get_clients_list, get_opposing_parties_list, get_display_name


def formatar_partes_envolvidas(acordo: Dict[str, Any]) -> str:
    """
    Formata todas as partes envolvidas em uma string única.
    
    Args:
        acordo: Dicionário com dados do acordo (deve ter clientes_ids, parte_contraria, outros_envolvidos)
    
    Returns:
        String formatada: "Cliente 1, Cliente 2, Parte Contrária X, Envolvido 1"
    """
    partes = []
    
    # Busca clientes
    clientes_ids = acordo.get('clientes_ids', [])
    if clientes_ids:
        clients_list = get_clients_list()
        for cliente_id in clientes_ids:
            for cliente in clients_list:
                if cliente.get('_id') == cliente_id:
                    partes.append(get_display_name(cliente))
                    break
    
    # Busca parte contrária
    parte_contraria_id = acordo.get('parte_contraria')
    if parte_contraria_id:
        all_people = get_clients_list() + get_opposing_parties_list()
        for pessoa in all_people:
            if pessoa.get('_id') == parte_contraria_id:
                partes.append(get_display_name(pessoa))
                break
    
    # Busca outros envolvidos
    outros_envolvidos_ids = acordo.get('outros_envolvidos', [])
    if outros_envolvidos_ids:
        all_people = get_clients_list() + get_opposing_parties_list()
        for pessoa_id in outros_envolvidos_ids:
            for pessoa in all_people:
                if pessoa.get('_id') == pessoa_id:
                    partes.append(get_display_name(pessoa))
                    break
    
    if not partes:
        return '-'
    
    return ', '.join(partes)


__all__ = [
    'formatar_partes_envolvidas',
]

