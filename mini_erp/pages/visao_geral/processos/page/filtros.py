"""
Componentes de filtros para a página de processos (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any, Callable, Optional
from ..constants import AREAS_PROCESSO, STATUS_PROCESSO


def criar_barra_pesquisa(filtros: Dict[str, Any], refresh_callback: Optional[Callable] = None) -> ui.input:
    """
    Cria barra de pesquisa de processos.
    
    Args:
        filtros: Dicionário de estado dos filtros
        refresh_callback: Função para atualizar a tabela
        
    Returns:
        Componente ui.input da pesquisa
    """
    with ui.input(placeholder='Pesquisar processos por título, número...').props('outlined dense clearable').classes('flex-grow w-full sm:w-auto sm:max-w-xl') as search_input:
        with search_input.add_slot('prepend'):
            ui.icon('search').classes('text-gray-400')
    
    def on_search_change():
        filtros['busca'] = search_input.value if search_input.value else ''
        if refresh_callback:
            refresh_callback()
    
    search_input.on('update:model-value', on_search_change)
    return search_input


def criar_filtros(filtros: Dict[str, Any], refresh_callback: Optional[Callable] = None) -> Dict[str, ui.select]:
    """
    Cria componentes de filtro (área e status).
    
    Args:
        filtros: Dicionário de estado dos filtros
        refresh_callback: Função para atualizar a tabela
        
    Returns:
        Dicionário com os componentes de filtro criados
    """
    ui.label('Filtros:').classes('text-gray-600 font-medium text-sm w-full sm:w-auto')
    
    # Filtro por área
    area_options = [''] + [a for a in AREAS_PROCESSO if a]
    area_select = ui.select(area_options, label='Área', value='').props('clearable dense outlined').classes('w-full sm:w-auto min-w-[100px] sm:min-w-[120px]')
    area_select.style('font-size: 12px; border-color: #d1d5db;')
    
    def on_area_change():
        filtros['area'] = area_select.value if area_select.value else None
        if refresh_callback:
            refresh_callback()
    
    area_select.on('update:model-value', on_area_change)
    
    # Filtro por status
    status_options = [''] + [s for s in STATUS_PROCESSO if s]
    status_select = ui.select(status_options, label='Status', value='').props('clearable dense outlined').classes('w-full sm:w-auto min-w-[100px] sm:min-w-[140px]')
    status_select.style('font-size: 12px; border-color: #d1d5db;')
    
    def on_status_change():
        filtros['status'] = status_select.value if status_select.value else None
        if refresh_callback:
            refresh_callback()
    
    status_select.on('update:model-value', on_status_change)
    
    return {
        'area': area_select,
        'status': status_select
    }


def criar_botao_limpar_filtros(
    filtros: Dict[str, Any],
    search_input: ui.input,
    filtro_components: Dict[str, ui.select],
    refresh_callback: Optional[Callable] = None
) -> ui.button:
    """
    Cria botão para limpar todos os filtros.
    
    Args:
        filtros: Dicionário de estado dos filtros
        search_input: Campo de pesquisa
        filtro_components: Dicionário com componentes de filtro
        refresh_callback: Função para atualizar a tabela
        
    Returns:
        Componente ui.button
    """
    def limpar_filtros():
        filtros['busca'] = ''
        filtros['area'] = None
        filtros['status'] = None
        search_input.value = ''
        filtro_components['area'].value = ''
        filtro_components['status'].value = ''
        if refresh_callback:
            refresh_callback()
    
    return ui.button('Limpar', icon='clear_all', on_click=limpar_filtros).props('flat dense').classes('text-xs text-gray-600 w-full sm:w-auto')


def filtrar_rows(rows: list, filtros: Dict[str, Any]) -> list:
    """
    Aplica filtros aos processos.
    
    Args:
        rows: Lista de processos (rows da tabela)
        filtros: Dicionário com filtros ativos
        
    Returns:
        Lista filtrada de processos
    """
    filtered = rows
    
    # Filtro de pesquisa (título/número)
    if filtros.get('busca'):
        term = filtros['busca'].lower()
        filtered = [r for r in filtered if term in (r.get('title_raw') or r.get('title') or '').lower() or term in (r.get('number') or '').lower()]
    
    # Filtro de área
    if filtros.get('area'):
        filtered = [r for r in filtered if (r.get('area') or '').strip() == filtros['area'].strip()]
    
    # Filtro de status
    if filtros.get('status'):
        filtered = [r for r in filtered if (r.get('status') or '').strip() == filtros['status'].strip()]
    
    return filtered



