"""
search_bar.py - Barra de pesquisa do módulo de Acordos.
"""

from nicegui import ui
from typing import Optional, Callable


def header_acordos(on_novo_acordo: Optional[Callable] = None) -> ui.input:
    """
    Renderiza barra superior com pesquisa e botão de novo acordo.
    
    Args:
        on_novo_acordo: Callback para criar novo acordo
    
    Returns:
        Campo de pesquisa (ui.input)
    """
    with ui.row().classes('w-full items-center gap-2 sm:gap-4 mb-4 flex-wrap'):
        # Campo de busca com ícone de lupa
        with ui.input(placeholder='Pesquisar acordos por título, número...').props('outlined dense clearable').classes('flex-grow w-full sm:w-auto sm:max-w-xl') as search_input:
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
        
        # Botão "+ NOVO ACORDO"
        if on_novo_acordo:
            ui.button('+ NOVO ACORDO', on_click=on_novo_acordo).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')
    
    return search_input

