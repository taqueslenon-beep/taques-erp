"""
Funções auxiliares para o modal de processo (Visão Geral).
"""
from typing import List, Dict, Any, Optional, Tuple
from mini_erp.core import get_display_name


def make_required_label(text: str) -> str:
    """Adiciona asterisco ao final do label para campos obrigatórios."""
    return f'{text} *'


def get_short_name(full_name: str, source_list: List[Dict[str, Any]]) -> str:
    """Retorna nome de exibição usando get_display_name."""
    if not full_name or not source_list:
        return full_name.split()[0] if full_name else full_name
    
    for item in source_list:
        item_name = item.get('name') or item.get('full_name', '')
        item_display = get_display_name(item)
        
        if item_name == full_name or item_display == full_name:
            display_name = get_display_name(item)
            if display_name:
                return display_name
            nome_exibicao = item.get('nome_exibicao', '').strip()
            if nome_exibicao:
                return nome_exibicao
    
    return full_name.split()[0] if full_name else full_name


def format_option_for_search(item: Dict[str, Any]) -> str:
    """Formata opção para busca: exibe nome de exibição."""
    display_name = get_display_name(item)
    if display_name:
        return display_name
    return item.get('name', '') or item.get('full_name', '')


def get_option_value(formatted_option: str, source_list: List[Dict[str, Any]]) -> str:
    """Extrai o nome completo de uma opção formatada."""
    if '(' in formatted_option:
        return formatted_option.split(' (')[0]
    return formatted_option


def get_scenario_type_style(tipo: Optional[str]) -> Tuple[str, str]:
    """Retorna cor baseada no tipo de cenário."""
    if 'Positivo' in str(tipo):
        return 'green', '#22c55e'
    if 'Negativo' in str(tipo):
        return 'red', '#ef4444'
    return 'grey', '#9ca3af'


def should_show_result_field(status: str) -> bool:
    """Verifica se deve mostrar campo de resultado baseado no status."""
    return status in ['Concluído', 'Concluído com pendências', 'Baixado', 'Encerrado']

