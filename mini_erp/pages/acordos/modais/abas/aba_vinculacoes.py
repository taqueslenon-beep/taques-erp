"""
aba_vinculacoes.py - Aba de Vinculações do Acordo.

Campos: Casos e Processos Vinculados.
"""

from nicegui import ui
from typing import Dict, Any, Tuple, Callable
from ...utils import make_required_label, format_option_for_search
from ...database import listar_casos, listar_processos


def render_aba_vinculacoes(state: Dict[str, Any]) -> Tuple[ui.select, ui.column, ui.select, ui.column, Callable, Callable]:
    """
    Renderiza aba de vinculações do acordo.
    
    Args:
        state: Dicionário de estado do formulário
    
    Returns:
        Tupla (casos_sel, casos_chips, processos_sel, processos_chips, refresh_casos_chips, refresh_processos_chips)
    """
    with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
        ui.label('🔗 Vinculações').classes('text-lg font-bold mb-3')
        with ui.column().classes('w-full gap-4'):
            # Casos Vinculados
            casos_list = listar_casos()
            casos_options = [format_option_for_search(c) for c in casos_list]
            
            def refresh_casos_chips(container):
                """Atualiza chips de casos com validação de DOM."""
                try:
                    if not container:
                        return
                    container.clear()
                    with container:
                        with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                            for caso_id in state['selected_casos']:
                                caso = next((c for c in casos_list if (c.get('_id') == caso_id or c.get('slug') == caso_id)), None)
                                if caso:
                                    title = caso.get('title', 'Sem título')
                                    with ui.badge(title).classes('pr-1').style('background-color: #9C27B0; color: white;'):
                                        ui.button(
                                            icon='close', 
                                            on_click=lambda cid=caso_id: remove_caso(cid, casos_chips)
                                        ).props('flat dense round size=xs color=white')
                except Exception:
                    pass
            
            def remove_caso(caso_id, container):
                if caso_id in state['selected_casos']:
                    state['selected_casos'].remove(caso_id)
                    refresh_casos_chips(container)
            
            def add_caso(select, container):
                val = select.value
                if val and val != '-':
                    caso = next((c for c in casos_list if format_option_for_search(c) == val), None)
                    if caso:
                        caso_id = caso.get('_id') or caso.get('slug')
                        if caso_id and caso_id not in state['selected_casos']:
                            state['selected_casos'].append(caso_id)
                            select.value = None
                            refresh_casos_chips(container)
                        else:
                            ui.notify('Este caso já está adicionado!', type='warning')
            
            with ui.row().classes('w-full gap-2 items-center'):
                casos_sel = ui.select(
                    casos_options or ['-'], 
                    label=make_required_label('Casos Vinculados'), 
                    with_input=True
                ).classes('flex-grow').props('dense outlined')
                casos_sel.tooltip('Selecione os casos relacionados a este acordo')
                ui.button(icon='add', on_click=lambda: add_caso(casos_sel, casos_chips)).props('flat dense').style('color: #9C27B0;')
            casos_chips = ui.column().classes('w-full')
            
            # Processos Vinculados
            processos_list = listar_processos()
            processos_options = []
            for proc in processos_list:
                title = proc.get('title', 'Sem título')
                number = proc.get('number', '')
                if number:
                    processos_options.append(f"{title} | {proc.get('_id', '')}")
                else:
                    processos_options.append(f"{title} | {proc.get('_id', '')}")
            
            def refresh_processos_chips(container):
                """Atualiza chips de processos com validação de DOM."""
                try:
                    if not container:
                        return
                    container.clear()
                    with container:
                        with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                            for proc_id in state['selected_processos']:
                                proc = next((p for p in processos_list if p.get('_id') == proc_id), None)
                                if proc:
                                    title = proc.get('title', 'Sem título')
                                    number = proc.get('number', '')
                                    display = f"{title}" + (f" ({number})" if number else "")
                                    with ui.badge(display).classes('pr-1').style('background-color: #FF9800; color: white;'):
                                        ui.button(
                                            icon='close', 
                                            on_click=lambda pid=proc_id: remove_processo(pid, processos_chips)
                                        ).props('flat dense round size=xs color=white')
                except Exception:
                    pass
            
            def remove_processo(proc_id, container):
                if proc_id in state['selected_processos']:
                    state['selected_processos'].remove(proc_id)
                    refresh_processos_chips(container)
            
            def add_processo(select, container):
                val = select.value
                if val and val != '-':
                    if ' | ' in val:
                        proc_id = val.split(' | ')[-1].strip()
                        if proc_id and proc_id not in state['selected_processos']:
                            state['selected_processos'].append(proc_id)
                            select.value = None
                            refresh_processos_chips(container)
                        else:
                            ui.notify('Este processo já está adicionado!', type='warning')
            
            with ui.row().classes('w-full gap-2 items-center'):
                processos_sel = ui.select(
                    processos_options or ['-'], 
                    label=make_required_label('Processos Vinculados'), 
                    with_input=True
                ).classes('flex-grow').props('dense outlined')
                processos_sel.tooltip('Selecione os processos relacionados a este acordo')
                ui.button(icon='add', on_click=lambda: add_processo(processos_sel, processos_chips)).props('flat dense').style('color: #FF9800;')
            processos_chips = ui.column().classes('w-full')
    
    return casos_sel, casos_chips, processos_sel, processos_chips, refresh_casos_chips, refresh_processos_chips

