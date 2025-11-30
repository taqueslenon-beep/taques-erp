"""
botao_novo_acordo.py - Botão para criar novo acordo.
"""

from nicegui import ui
from typing import Optional, Callable


def botao_novo_acordo(on_click: Optional[Callable] = None) -> ui.button:
    """
    Renderiza botão para criar novo acordo.
    
    Args:
        on_click: Callback ao clicar no botão
    
    Returns:
        Componente ui.button
    """
    return ui.button('+ NOVO ACORDO', on_click=on_click, icon='add').props('color=primary').classes('whitespace-nowrap')

