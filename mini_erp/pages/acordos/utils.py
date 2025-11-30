"""
utils.py - Funções auxiliares específicas do módulo de Acordos.

Funções de formatação e utilitários gerais.
"""

from typing import Dict, Any
from ...core import get_display_name


def make_required_label(text: str) -> str:
    """Adiciona asterisco ao final do label para campos obrigatórios."""
    return f'{text} *'


def format_option_for_search(item: dict) -> str:
    """Formata opção para busca: inclui nome e informações adicionais."""
    name = item.get('title') or item.get('name') or item.get('full_name') or item.get('email', '')
    if item.get('number'):
        return f"{name} ({item['number']})"
    return name


def format_option_for_pessoa(item: dict) -> str:
    """Formata opção para busca de pessoas (compatível com processo)."""
    # Usa get_display_name para obter nome de exibição
    display = get_display_name(item)
    
    # Adiciona prefixo se for cliente ou parte contrária
    tipo = item.get('_tipo', '')
    if tipo == 'cliente':
        return f"[C] {display}"
    elif tipo == 'parte_contraria':
        return f"[PC] {display}"
    
    # Para pessoas sem tipo específico, usa display name
    return display


def format_option_for_search_pessoa(item: dict) -> str:
    """Formata opção para busca de pessoas (com nome completo para busca)."""
    display = get_display_name(item)
    full_name = item.get('full_name') or item.get('name', '')
    if full_name and full_name != display:
        return f"{display} ({full_name})"
    return display


__all__ = [
    'make_required_label',
    'format_option_for_search',
    'format_option_for_pessoa',
    'format_option_for_search_pessoa',
]

