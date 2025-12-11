"""
Funções utilitárias para o módulo Painel.
Formatadores, normalizadores e helpers de dados.
"""
from typing import Any


def get_short_name(full_name: str, source_list: list) -> str:
    """
    Retorna sigla/apelido ou primeiro nome de uma pessoa/empresa.
    Prioridade: nickname > alias > primeiro nome.
    """
    if not full_name:
        return full_name
    
    for item in source_list:
        if item.get('name') == full_name:
            if item.get('nickname'):
                return item['nickname']
            if item.get('alias'):
                return item['alias']
            return full_name.split()[0] if full_name else full_name
    
    return full_name.split()[0] if full_name else full_name


def format_currency(value: float) -> str:
    """Formata valor como moeda BRL."""
    return f'R$ {value:,.2f}'


def format_percentage(value: float, total: float) -> str:
    """Formata valor como percentual."""
    if total == 0:
        return '0%'
    return f'{(value / total) * 100:.1f}%'


def get_case_type(case: dict) -> str:
    """
    Retorna o tipo do caso (Antigo/Novo/Futuro).
    Compatível com dados antigos que usavam is_new_case.
    """
    ct = case.get('case_type')
    if ct in ['Antigo', 'Novo', 'Futuro']:
        return ct
    # Compatibilidade com dados antigos
    if case.get('is_new_case', False):
        return 'Novo'
    return 'Antigo'


def safe_float(value: Any, default: float = 0.0) -> float:
    """Converte valor para float de forma segura."""
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Converte valor para int de forma segura."""
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default










