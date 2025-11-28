"""
Módulo de lógica de negócio para o módulo Pessoas.
Contém funções de agrupamento, transformação de dados e operações complexas.
"""
from typing import List, Dict, Any, Tuple
from ...core import get_full_name, get_display_name, digits_only
from .database import get_clients_list, get_opposing_parties_list
from .validators import normalize_client_type_for_display
from .models import CLIENT_GROUP_CONFIG


def get_people_options_for_partners() -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
    """
    Retorna lista de pessoas (Clientes e Outros Envolvidos) para dropdown de sócios.
    
    Returns:
        Tupla (people_options_dict, people_data_dict):
        - people_options_dict: {label: value} para uso em select
        - people_data_dict: {label: {full_data}} para acesso completo aos dados
    """
    people = []
    for c in get_clients_list():
        people.append({
            'label': f"[C] {get_full_name(c)}",
            'value': get_full_name(c),
            'type': 'client',
            'cpf': digits_only(c.get('cpf') or c.get('cpf_cnpj') or c.get('document', ''))
        })
    for op in get_opposing_parties_list():
        people.append({
            'label': f"[PC] {get_full_name(op)}",
            'value': get_full_name(op),
            'type': 'opposing_party',
            'cpf': digits_only(op.get('cpf_cnpj') or op.get('document', ''))
        })
    return {p['label']: p['value'] for p in people}, {p['label']: p for p in people}


def get_all_people_options() -> List[str]:
    """
    Retorna lista simples de pessoas para dropdown de vínculos.
    
    Returns:
        Lista de strings no formato "[C] Nome" ou "[PC] Nome"
    """
    people = []
    for c in get_clients_list():
        people.append(f"[C] {get_full_name(c)}")
    for op in get_opposing_parties_list():
        people.append(f"[PC] {get_full_name(op)}")
    return people


def group_clients_by_type() -> List[Tuple[str, List[Tuple[int, Dict[str, Any]]]]]:
    """
    Agrupa clientes por tipo (PJ primeiro, depois PF) e ordena alfabeticamente.
    
    Returns:
        Lista de tuplas (group_title, [(original_index, client_dict), ...])
    """
    grouped = []
    
    for group_info in CLIENT_GROUP_CONFIG:
        internal_type = group_info['type']
        group_title = group_info['title']
        
        # Coleta clientes do tipo (normalizando tipos antes de filtrar)
        group_clients = [
            (idx, c) for idx, c in enumerate(get_clients_list()) 
            if normalize_client_type_for_display(c) == internal_type
        ]
        
        # Ordena alfabeticamente por nome completo
        group_clients.sort(key=lambda x: get_full_name(x[1]).upper())
        
        grouped.append((group_title, group_clients))
    
    return grouped


def process_partners_from_rows(partners_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processa linhas de sócios do formulário e retorna lista de sócios.
    
    Args:
        partners_rows: Lista de dicionários com dados das linhas de sócios
        
    Returns:
        Lista de dicionários com dados dos sócios processados
    """
    partners = []
    people_options, people_data = get_people_options_for_partners()
    
    for row in partners_rows:
        partner_label = row.get('select') and row['select'].value
        partner_share_val = row.get('share') and row['share'].value.strip() or ''
        
        if partner_label:
            # Extrai dados da pessoa selecionada
            if partner_label in people_data:
                person_info = people_data[partner_label]
                partners.append({
                    'full_name': person_info['value'],
                    'cpf': person_info.get('cpf', ''),
                    'share': partner_share_val or '',
                    'type': person_info['type']
                })
            else:
                # Fallback: usa dados já armazenados no row_data ou extrai do label
                partners.append({
                    'full_name': row.get('person_name', partner_label.replace('[C] ', '').replace('[PC] ', '')),
                    'cpf': row.get('person_cpf', ''),
                    'share': partner_share_val or '',
                    'type': row.get('person_type', 'unknown')
                })
    
    return partners


def clean_person_name_from_label(person_label: str) -> str:
    """
    Remove prefixos [C] ou [PC] do nome da pessoa.
    
    Args:
        person_label: Label com prefixo (ex: "[C] João Silva")
        
    Returns:
        Nome limpo (ex: "João Silva")
    """
    if person_label.startswith('[C] '):
        return person_label[4:]
    elif person_label.startswith('[PC] '):
        return person_label[5:]
    return person_label


def validate_bond_not_self(person_label: str, client_name: str) -> bool:
    """
    Valida que o vínculo não está sendo criado com a própria pessoa.
    
    Args:
        person_label: Label da pessoa (com prefixo)
        client_name: Nome do cliente que está criando o vínculo
        
    Returns:
        True se válido (não é auto-vínculo), False caso contrário
    """
    clean_person_name = clean_person_name_from_label(person_label)
    return clean_person_name != client_name


def check_bond_exists(client: Dict[str, Any], person_name: str) -> bool:
    """
    Verifica se um vínculo já existe para a pessoa especificada.
    
    Args:
        client: Dicionário com dados do cliente
        person_name: Nome da pessoa (sem prefixo)
        
    Returns:
        True se vínculo já existe, False caso contrário
    """
    existing_bonds = client.get('bonds', [])
    for bond in existing_bonds:
        if bond.get('person') == person_name:
            return True
    return False


def create_bond_data(person_label: str, bond_type: str) -> Dict[str, Any]:
    """
    Cria estrutura de dados de vínculo a partir dos inputs do formulário.
    
    Args:
        person_label: Label da pessoa (com prefixo [C] ou [PC])
        bond_type: Tipo do vínculo
        
    Returns:
        Dicionário com dados do vínculo
    """
    person_name = clean_person_name_from_label(person_label)
    source = person_label.split(']')[0] + ']' if ']' in person_label else ''
    
    return {
        'person': person_name,
        'type': bond_type,
        'source': source
    }


def prepare_client_row_data(client: Dict[str, Any], original_index: int) -> Dict[str, Any]:
    """
    Prepara dados de uma linha de cliente para exibição em tabela.
    
    Args:
        client: Dicionário com dados do cliente
        original_index: Índice original do cliente na lista
        
    Returns:
        Dicionário com dados formatados para a tabela
    """
    return {
        'id': original_index,  # mantém índice original para eventos edit/delete
        'full_name': get_full_name(client),
        'display_name': get_display_name(client),
        'cpf_cnpj': client.get('cpf_cnpj') or client.get('document', ''),
    }


def prepare_opposing_row_data(opposing: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Prepara dados de uma linha de outro envolvido para exibição em tabela.
    
    Args:
        opposing: Dicionário com dados do outro envolvido
        index: Índice do outro envolvido na lista
        
    Returns:
        Dicionário com dados formatados para a tabela
    """
    return {
        'id': index,
        'full_name': get_full_name(opposing),
        'display_name': get_display_name(opposing),
        'entity_type': opposing.get('entity_type', 'PF'),
        'cpf_cnpj': opposing.get('cpf_cnpj') or opposing.get('document', ''),
    }

