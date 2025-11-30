"""
filtros_manager.py - Gerenciador de filtros do módulo de Acordos.

Orquestra todos os filtros e gerencia estado compartilhado.
"""

from nicegui import ui
from typing import Dict, List, Optional, Callable
from .filtro_status import filtro_status


def filtros_acordos(
    filter_status: Dict[str, str],
    filter_options: Dict[str, List[str]],
    on_filter_change: Optional[Callable] = None,
    on_clear: Optional[Callable] = None
) -> Dict[str, ui.select]:
    """
    Renderiza seção de filtros.
    
    Args:
        filter_status: Dicionário com estado dos filtros
        filter_options: Opções disponíveis para cada filtro
        on_filter_change: Callback quando filtro muda
        on_clear: Callback para limpar filtros
    
    Returns:
        Dicionário com os selects de filtro
    """
    selects = {}
    
    with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
        ui.label('Filtros:').classes('text-gray-600 font-medium text-sm w-full sm:w-auto')
        
        # Filtro de Status
        selects['status'] = filtro_status(
            filter_status=filter_status,
            options=filter_options.get('status', ['']),
            on_change=on_filter_change
        )
        
        # Botão Limpar
        if on_clear:
            ui.button('Limpar', icon='clear_all', on_click=on_clear).props('flat dense').classes('text-xs text-gray-600 w-full sm:w-auto')
    
    return selects

