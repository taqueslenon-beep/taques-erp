"""
database.py - Operações de banco de dados para o módulo de Processos.

Este módulo contém:
- Funções wrapper para operações CRUD via core
- Sincronização de processos com casos
- Acesso a listas de dados
"""

from typing import List, Dict, Any, Optional

# Imports do core para operações de banco
from ...core import (
    get_processes_list,
    get_cases_list,
    get_clients_list,
    get_opposing_parties_list,
    save_data,
    sync_processes_cases,
    data,
    save_process as save_process_to_firestore,
)


# =============================================================================
# FUNÇÕES DE ACESSO A DADOS
# =============================================================================

def get_all_processes() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os processos.
    
    Returns:
        Lista de dicionários com dados dos processos
    """
    return get_processes_list()


def get_all_cases() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os casos.
    
    Returns:
        Lista de dicionários com dados dos casos
    """
    return get_cases_list()


def get_all_clients() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os clientes.
    
    Returns:
        Lista de dicionários com dados dos clientes
    """
    return get_clients_list()


def get_all_opposing_parties() -> List[Dict[str, Any]]:
    """
    Retorna lista de todas as partes contrárias.
    
    Returns:
        Lista de dicionários com dados das partes contrárias
    """
    return get_opposing_parties_list()


def get_process_by_index(idx: int) -> Optional[Dict[str, Any]]:
    """
    Retorna um processo pelo índice.
    
    Args:
        idx: Índice do processo na lista
    
    Returns:
        Dicionário do processo ou None se índice inválido
    """
    processes = get_processes_list()
    if 0 <= idx < len(processes):
        return processes[idx]
    return None


# =============================================================================
# FUNÇÕES DE CRIAÇÃO E ATUALIZAÇÃO
# =============================================================================

def save_process(process_data: Dict[str, Any], edit_index: Optional[int] = None) -> str:
    """
    Salva ou atualiza um processo.
    
    Args:
        process_data: Dados do processo a salvar
        edit_index: Índice para edição (None para novo processo)
    
    Returns:
        Mensagem de sucesso
    """
    # Obtém o doc_id (_id) do processo
    # Prioridade: _id do process_data > _id do processo existente > None (novo processo)
    doc_id = process_data.get('_id')
    
    if not doc_id and edit_index is not None:
        processes = get_processes_list()
        if 0 <= edit_index < len(processes):
            existing_process = processes[edit_index]
            doc_id = existing_process.get('_id')
    
    if doc_id:
        message = 'Processo atualizado!'
    else:
        message = f'Processo "{process_data.get("title", "")}" cadastrado!'
    
    # Salva no Firestore usando a função do core
    # A função save_process_to_firestore gerencia a persistência corretamente
    save_process_to_firestore(process_data, doc_id=doc_id, sync=True)
    
    return message


def update_process_field(idx: int, field: str, value: Any) -> bool:
    """
    Atualiza um campo específico de um processo.
    
    Args:
        idx: Índice do processo
        field: Nome do campo a atualizar
        value: Novo valor
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        processes[idx][field] = value
        data['processes'] = processes
        save_data()
        return True
    
    return False


def delete_process(idx: int) -> Optional[str]:
    """
    Exclui um processo pelo índice.
    
    Args:
        idx: Índice do processo a excluir
    
    Returns:
        Título do processo excluído ou None se falhou
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        process_title = processes[idx].get('title', 'Processo')
        processes.pop(idx)
        data['processes'] = processes
        sync_processes_cases()
        save_data()
        return process_title
    
    return None


# =============================================================================
# FUNÇÕES DE ACESSO A PROCESSOS
# =============================================================================

def update_process_access(idx: int, access_type: str, field: str, value: bool) -> bool:
    """
    Atualiza campo de acesso de um processo.
    
    Args:
        idx: Índice do processo
        access_type: Tipo de acesso ('lawyer', 'technicians', 'client')
        field: Campo ('requested' ou 'granted')
        value: Novo valor
    
    Returns:
        True se atualizado com sucesso
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        field_name = f'access_{access_type}_{field}'
        processes[idx][field_name] = value
        
        # Se concedido, automaticamente marca como solicitado
        if field == 'granted' and value:
            processes[idx][f'access_{access_type}_requested'] = True
        
        data['processes'] = processes
        save_data()
        return True
    
    return False


def update_process_access_comment(idx: int, access_type: str, comment: str) -> bool:
    """
    Atualiza comentário de acesso de um processo.
    
    Args:
        idx: Índice do processo
        access_type: Tipo de acesso ('lawyer', 'technicians', 'client')
        comment: Texto do comentário
    
    Returns:
        True se atualizado com sucesso
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        field_name = f'access_{access_type}_comment'
        processes[idx][field_name] = comment
        data['processes'] = processes
        save_data()
        return True
    
    return False


# =============================================================================
# FUNÇÕES DE SINCRONIZAÇÃO
# =============================================================================

def sync_all() -> None:
    """
    Sincroniza processos com casos.
    """
    sync_processes_cases()


def save_all() -> None:
    """
    Salva todos os dados.
    """
    save_data()


# =============================================================================
# FUNÇÕES DE OPÇÕES PARA SELECTS
# =============================================================================

def get_client_options() -> List[str]:
    """
    Retorna lista de nomes de clientes para select.
    
    Returns:
        Lista de nomes de clientes
    """
    return [c['name'] for c in get_clients_list()]


def get_opposing_options() -> List[str]:
    """
    Retorna lista de nomes de partes contrárias para select.
    
    Returns:
        Lista de nomes de partes contrárias
    """
    return [op['name'] for op in get_opposing_parties_list()]


def get_case_options() -> List[str]:
    """
    Retorna lista de títulos de casos para select.
    
    Returns:
        Lista de títulos de casos
    """
    return [c['title'] for c in get_cases_list()]


