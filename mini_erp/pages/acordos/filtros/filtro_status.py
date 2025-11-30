"""
filtro_status.py - Filtro de status para acordos.
"""

from nicegui import ui
from typing import Dict, List, Optional, Callable


def filtro_status(
    filter_status: Dict[str, str],
    options: List[str],
    on_change: Optional[Callable] = None
) -> ui.select:
    """
    Renderiza filtro de status.
    
    Args:
        filter_status: Dicionário com estado do filtro (mutável)
        options: Lista de opções de status
        on_change: Callback quando filtro muda
    
    Returns:
        Componente ui.select
    """
    select = ui.select(
        options,
        label='Status',
        value=filter_status.get('status', '')
    ).props('clearable dense outlined').classes('w-full sm:w-auto min-w-[100px] sm:min-w-[140px]')
    select.style('font-size: 12px; border-color: #d1d5db;')
    
    def on_change_internal():
        filter_status['status'] = select.value if select.value else ''
        if on_change:
            on_change()
    
    select.on('update:model-value', on_change_internal)
    return select

