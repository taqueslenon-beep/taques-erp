"""
botao_editar_acordo.py - Botão para editar acordo.
"""

from nicegui import ui
from typing import Optional, Callable


def botao_editar_acordo(on_click: Optional[Callable] = None) -> ui.button:
    """
    Renderiza botão para editar acordo.
    
    Args:
        on_click: Callback ao clicar no botão
    
    Returns:
        Componente ui.button
    """
    return ui.button('Editar', on_click=on_click, icon='edit').props('flat dense')

