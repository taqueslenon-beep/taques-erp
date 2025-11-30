"""
business_logic.py - Lógica de negócio para o módulo de Processos.

Este módulo contém:
- Validações de processos e cenários
- Funções de filtro
- Agrupamento de processos por caso
- Transformações de dados
"""

from typing import List, Dict, Any, Tuple, Optional

from .models import FINALIZED_STATUSES
from .database import get_all_processes, get_all_clients, get_all_opposing_parties
from .utils import get_short_name


# =============================================================================
# VALIDAÇÕES
# =============================================================================

def validate_process(
    title: str,
    selected_cases: List[str],
    selected_clients: Optional[List[str]] = None,
    parent_ids: Optional[List[str]] = None,
    current_process_id: Optional[str] = None,
    process_type: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Valida dados de um processo antes de salvar.
    
    Args:
        title: Título do processo
        selected_cases: Lista de casos vinculados
        selected_clients: Lista de clientes (opcional)
        parent_ids: Lista de IDs dos processos pais (opcional)
        current_process_id: ID do processo sendo editado (para evitar auto-vínculo)
        process_type: Tipo do processo ('Futuro' ou 'Existente') - opcional
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if not title:
        return False, 'Título do processo é obrigatório!'
    
    # Processos futuros podem não ter casos vinculados ainda
    if not selected_cases and process_type != 'Futuro':
        return False, 'Adicione pelo menos um caso vinculado!'
    
    # Validação de cliente removida para flexibilidade
    # if not selected_clients:
    #     return False, 'Adicione pelo menos um cliente!'
    
    # Validação de processos pai
    if parent_ids:
        # Valida auto-vínculo (processo não pode ser pai de si mesmo)
        if current_process_id and current_process_id in parent_ids:
            return False, 'Um processo não pode ser vinculado a si mesmo!'
        
        # Valida ciclos (processo A → processo B → processo A)
        cycle_error = validate_parent_cycles(parent_ids, current_process_id)
        if cycle_error:
            return False, cycle_error
    
    return True, ''


def validate_parent_cycles(parent_ids: List[str], current_process_id: Optional[str] = None) -> Optional[str]:
    """
    Valida se há ciclos na hierarquia de processos pai.
    
    Args:
        parent_ids: Lista de IDs dos processos pais
        current_process_id: ID do processo sendo editado
    
    Returns:
        Mensagem de erro se houver ciclo, None caso contrário
    """
    if not parent_ids or not current_process_id:
        return None
    
    from .database import get_all_processes
    
    # Busca todos os processos para construir grafo
    all_processes = get_all_processes()
    process_map = {p.get('_id'): p for p in all_processes if p.get('_id')}
    
    # Verifica se algum processo pai tem o processo atual como ancestral
    visited = set()
    
    def has_ancestor(process_id: str, target_id: str) -> bool:
        """
        Verifica se process_id tem target_id como ancestral (direto ou indireto).
        """
        if process_id == target_id:
            return True
        
        if process_id in visited:
            return False
        
        visited.add(process_id)
        
        process = process_map.get(process_id)
        if not process:
            return False
        
        # Busca processos pais (suporta parent_ids e parent_id para compatibilidade)
        parent_ids_list = process.get('parent_ids', [])
        if not parent_ids_list:
            old_parent_id = process.get('parent_id')
            if old_parent_id:
                parent_ids_list = [old_parent_id]
        
        for parent_id in parent_ids_list:
            if has_ancestor(parent_id, target_id):
                return True
        
        return False
    
    # Verifica cada processo pai
    for parent_id in parent_ids:
        visited.clear()
        if has_ancestor(parent_id, current_process_id):
            parent_title = process_map.get(parent_id, {}).get('title', parent_id)
            return f'Ciclo detectado! O processo "{parent_title}" já é descendente deste processo.'
    
    return None


def validate_scenario(title: str) -> Tuple[bool, str]:
    """
    Valida dados de um cenário antes de salvar.
    
    Args:
        title: Título do cenário
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if not title:
        return False, 'Título do cenário é obrigatório!'
    
    return True, ''


def validate_protocol(title: str) -> Tuple[bool, str]:
    """
    Valida dados de um protocolo antes de salvar.
    
    Args:
        title: Título do protocolo
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if not title:
        return False, 'Título do protocolo é obrigatório!'
    
    return True, ''


# =============================================================================
# FUNÇÕES DE TIPO E STATUS
# =============================================================================

def get_process_type(process: Dict[str, Any]) -> str:
    """
    Retorna o tipo do processo, com 'Existente' como padrão.
    
    Args:
        process: Dicionário do processo
    
    Returns:
        Tipo do processo ('Existente' ou 'Futuro')
    """
    return process.get('process_type', 'Existente')


def is_finalized_status(status: Optional[str]) -> bool:
    """
    Verifica se o status indica processo finalizado.
    
    Args:
        status: Status do processo
    
    Returns:
        True se o status indica finalização
    """
    return status in FINALIZED_STATUSES


def should_show_result_field(status: Optional[str]) -> bool:
    """
    Verifica se deve mostrar campo de resultado baseado no status.
    
    Args:
        status: Status do processo
    
    Returns:
        True se deve mostrar o campo de resultado
    """
    return status in FINALIZED_STATUSES


# =============================================================================
# FUNÇÕES DE FILTRO
# =============================================================================

def filter_processes(
    processes: List[Tuple[int, Dict[str, Any]]],
    process_type: str,
    search_query: str = '',
    filter_nucleo: Optional[str] = None,
    filter_area: Optional[str] = None,
    filter_system: Optional[str] = None,
    filter_client: Optional[str] = None,
    filter_opposing: Optional[str] = None,
    filter_case: Optional[str] = None,
    filter_status: Optional[str] = None,
) -> List[Tuple[int, Dict[str, Any]]]:
    """
    Aplica filtros a uma lista de processos.
    
    Args:
        processes: Lista de tuplas (índice, processo)
        process_type: Tipo de processo ('Existente' ou 'Futuro')
        search_query: Texto de busca por título
        filter_nucleo: Filtro por núcleo
        filter_area: Filtro por área
        filter_system: Filtro por sistema
        filter_client: Filtro por cliente
        filter_opposing: Filtro por parte contrária
        filter_case: Filtro por caso
        filter_status: Filtro por status
    
    Returns:
        Lista filtrada de tuplas (índice, processo)
    """
    filtered = []
    
    for idx, process in processes:
        # Filtro por tipo de processo (Existente/Futuro)
        if get_process_type(process) != process_type:
            continue
        
        # Pesquisa por título
        if search_query:
            title = process.get('title', '').lower()
            if search_query.lower() not in title:
                continue
        
        # Filtro por núcleo
        if filter_nucleo and process.get('nucleo') != filter_nucleo:
            continue
        
        # Filtro por área
        if filter_area and process.get('area') != filter_area:
            continue
        
        # Filtro por sistema
        if filter_system and process.get('system') != filter_system:
            continue
        
        # Filtro por cliente
        if filter_client and filter_client != '—':
            if filter_client not in process.get('clients', []):
                continue
        
        # Filtro por parte contrária
        if filter_opposing and filter_opposing != '—':
            if filter_opposing not in process.get('opposing_parties', []):
                continue
        
        # Filtro por caso vinculado
        if filter_case and filter_case != '—':
            if filter_case not in process.get('cases', []):
                continue
        
        # Filtro por status
        if filter_status and process.get('status') != filter_status:
            continue
        
        filtered.append((idx, process))
    
    return filtered


def filter_processes_by_type_and_system(
    process_type: str,
    system_filter: Optional[str] = None
) -> List[Tuple[int, Dict[str, Any]]]:
    """
    Filtra processos por tipo e sistema (para visualização por caso).
    
    Args:
        process_type: Tipo de processo ('Existente' ou 'Futuro')
        system_filter: Filtro de sistema (opcional)
    
    Returns:
        Lista de tuplas (índice, processo) filtrada
    """
    processes = get_all_processes()
    filtered = []
    
    for idx, process in enumerate(processes):
        if get_process_type(process) != process_type:
            continue
        
        # Filtro por sistema
        if system_filter and process.get('system') != system_filter:
            continue
        
        filtered.append((idx, process))
    
    return filtered


# =============================================================================
# AGRUPAMENTO
# =============================================================================

def group_processes_by_case(
    processes: List[Tuple[int, Dict[str, Any]]]
) -> Tuple[Dict[str, List[Tuple[int, Dict[str, Any]]]], List[Tuple[int, Dict[str, Any]]]]:
    """
    Agrupa processos por caso vinculado.
    
    Args:
        processes: Lista de tuplas (índice, processo)
    
    Returns:
        Tupla (dict de processos por caso, lista de processos sem caso)
    """
    processes_by_case: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    processes_without_case: List[Tuple[int, Dict[str, Any]]] = []
    
    for idx, process in processes:
        cases = process.get('cases', [])
        if cases:
            for case_title in cases:
                if case_title not in processes_by_case:
                    processes_by_case[case_title] = []
                processes_by_case[case_title].append((idx, process))
        else:
            processes_without_case.append((idx, process))
    
    return processes_by_case, processes_without_case


# =============================================================================
# TRANSFORMAÇÃO DE DADOS PARA TABELA
# =============================================================================

def build_table_row(
    idx: int,
    process: Dict[str, Any],
    clients_list: List[Dict[str, Any]],
    opposing_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Constrói linha de dados para tabela de processos.
    
    Args:
        idx: Índice do processo
        process: Dados do processo
        clients_list: Lista de clientes para obter nomes curtos
        opposing_list: Lista de partes contrárias para obter nomes curtos
    
    Returns:
        Dicionário com dados formatados para a tabela
    """
    process_cases_list = process.get('cases', [])
    clients_raw = process.get('clients', [])
    short_clients_list = sorted([get_short_name(c, clients_list) for c in clients_raw])
    
    opposing_raw = process.get('opposing_parties', [])
    short_opposing_list = [get_short_name(op, opposing_list) for op in opposing_raw]
    
    return {
        'idx': idx,
        'title': process.get('title', ''),
        'number': process.get('number', '-'),
        'nucleo': process.get('nucleo', '-'),
        'area': process.get('area', '-'),
        'system': process.get('system', '-'),
        'clients': ', '.join(short_clients_list) if short_clients_list else '-',
        'short_clients_list': short_clients_list,
        'opposing': ', '.join(short_opposing_list) if short_opposing_list else '-',
        'cases': ', '.join(process_cases_list) if process_cases_list else '-',
        'cases_list': process_cases_list,
        'status': process.get('status', 'Em andamento'),
        'link': process.get('link', '')
    }


def build_access_table_row(idx: int, process: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói linha de dados para tabela de acesso.
    
    Args:
        idx: Índice do processo
        process: Dados do processo
    
    Returns:
        Dicionário com dados de acesso formatados para a tabela
    """
    return {
        'idx': idx,
        'area': process.get('area', '-'),
        'title': process.get('title', ''),
        'number': process.get('number', '-'),
        'system': process.get('system', '-'),
        # Advogado
        'lawyer_requested': process.get('access_lawyer_requested', False),
        'lawyer_granted': process.get('access_lawyer_granted', False),
        'lawyer_comment': process.get('access_lawyer_comment', ''),
        # Técnicos
        'technicians_requested': process.get('access_technicians_requested', False),
        'technicians_granted': process.get('access_technicians_granted', False),
        'technicians_comment': process.get('access_technicians_comment', ''),
        # Cliente
        'client_requested': process.get('access_client_requested', False),
        'client_granted': process.get('access_client_granted', False),
        'client_comment': process.get('access_client_comment', ''),
    }


# =============================================================================
# CONSTRUÇÃO DE DADOS DE PROCESSO
# =============================================================================

def build_process_data(
    title: str,
    number: str,
    system: Optional[str],
    link: str,
    nucleo: Optional[str],
    area: Optional[str],
    status: Optional[str],
    result: Optional[str],
    process_type: str,
    data_abertura: Optional[str],  # Aceita: DD/MM/AAAA, MM/AAAA ou AAAA
    clients: List[str],
    opposing_parties: List[str],
    other_parties: List[str],
    cases: List[str],
    relatory_facts: str = '',
    relatory_timeline: str = '',
    relatory_documents: str = '',
    strategy_objectives: str = '',
    legal_thesis: str = '',
    strategy_observations: str = '',
    scenarios: List[Dict[str, Any]] = None,
    protocols: List[Dict[str, Any]] = None,
    access_lawyer: bool = False,
    access_technicians: bool = False,
    access_client: bool = False,
    access_lawyer_comment: str = '',
    access_technicians_comment: str = '',
    access_client_comment: str = '',
    access_lawyer_requested: bool = False,
    access_technicians_requested: bool = False,
    access_client_requested: bool = False,
    parent_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    Constrói dicionário de dados de processo para salvar.
    
    Returns:
        Dicionário completo do processo
    """
    return {
        'title': title,
        'number': number,
        'system': system,
        'link': link,
        'nucleo': nucleo,
        'area': area,
        'status': status,
        'result': result,
        'process_type': process_type,
        'data_abertura': data_abertura,
        'clients': list(clients) if clients else [],  # Garante que seja sempre uma lista, nunca None
        'opposing_parties': list(opposing_parties) if opposing_parties else [],
        'other_parties': list(other_parties) if other_parties else [],
        'cases': list(cases) if cases else [],
        'relatory_facts': relatory_facts,
        'relatory_timeline': relatory_timeline,
        'relatory_documents': relatory_documents,
        'strategy_objectives': strategy_objectives,
        'legal_thesis': legal_thesis,
        'strategy_observations': strategy_observations,
        'scenarios': (scenarios or []).copy(),
        'protocols': (protocols or []).copy(),
        'access_lawyer': access_lawyer,
        'access_technicians': access_technicians,
        'access_client': access_client,
        'access_lawyer_comment': access_lawyer_comment,
        'access_technicians_comment': access_technicians_comment,
        'access_client_comment': access_client_comment,
        'access_lawyer_requested': access_lawyer_requested,
        'access_technicians_requested': access_technicians_requested,
        'access_client_requested': access_client_requested,
        'parent_ids': (parent_ids or []).copy(),
    }


