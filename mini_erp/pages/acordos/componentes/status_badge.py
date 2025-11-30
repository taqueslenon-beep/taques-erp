"""
status_badge.py - Componente de badge de status para acordos.
"""

from nicegui import ui
from typing import Optional


def status_badge(status: Optional[str] = None) -> ui.badge:
    """
    Renderiza badge de status com cor apropriada.
    
    Args:
        status: Status do acordo (Rascunho, Ativo, Arquivado, Cancelado)
    
    Returns:
        Componente ui.badge
    """
    if not status:
        status = 'Rascunho'
    
    status_lower = status.lower()
    
    # Define cor baseada no status
    if 'rascunho' in status_lower:
        color = 'grey'
    elif 'ativo' in status_lower:
        color = 'green'
    elif 'arquivado' in status_lower:
        color = 'blue'
    elif 'cancelado' in status_lower:
        color = 'red'
    else:
        color = 'grey'
    
    return ui.badge(status).props(f'color={color}')

