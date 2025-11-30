"""
aba_partes.py - Aba de Partes do Acordo.

Campos: Clientes, Parte Contrária e Outros Envolvidos.
"""

from nicegui import ui
from typing import Dict, Any, Tuple, Callable
from ...utils import make_required_label, format_option_for_pessoa, format_option_for_search_pessoa
from ...database import listar_pessoas_como_clientes, listar_todas_pessoas
from .....core import get_display_name


def render_aba_partes(state: Dict[str, Any]) -> Tuple[ui.select, ui.column, ui.select, ui.column, ui.select, ui.column, Callable, Callable, Callable]:
    """
    Renderiza aba de partes do acordo.
    
    Args:
        state: Dicionário de estado do formulário
    
    Returns:
        Tupla (clientes_sel, clientes_chips, parte_contraria_sel, parte_contraria_chips, outros_sel, outros_chips, refresh_clientes_chips, refresh_parte_contraria_chip, refresh_outros_chips)
    """
    with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
        ui.label('👥 Partes do Acordo').classes('text-lg font-bold mb-3')
        with ui.column().classes('w-full gap-4'):
            # Clientes (múltiplo)
            clientes_list = listar_pessoas_como_clientes()
            clientes_options = [format_option_for_pessoa(c) for c in clientes_list]
            
            def refresh_clientes_chips(container):
                """Atualiza chips de clientes com validação de DOM."""
                try:
                    if not container:
                        return
                    container.clear()
                    with container:
                        with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                            for cliente_id in state['selected_clientes']:
                                cliente = next((c for c in clientes_list if (c.get('_id') == cliente_id or get_display_name(c) == cliente_id)), None)
                                if cliente:
                                    display = format_option_for_pessoa(cliente)
                                    with ui.badge(display).classes('pr-1').style('background-color: #4CAF50; color: white;'):
                                        ui.button(
                                            icon='close', 
                                            on_click=lambda cid=cliente_id: remove_cliente(cid, clientes_chips)
                                        ).props('flat dense round size=xs color=white')
                except Exception:
                    pass
            
            def remove_cliente(cliente_id, container):
                if cliente_id in state['selected_clientes']:
                    state['selected_clientes'].remove(cliente_id)
                    refresh_clientes_chips(container)
            
            def add_cliente(select, container):
                val = select.value
                if val and val != '-':
                    cliente = next((c for c in clientes_list if format_option_for_pessoa(c) == val), None)
                    if cliente:
                        cliente_id = cliente.get('_id') or get_display_name(cliente)
                        if cliente_id and cliente_id not in state['selected_clientes']:
                            state['selected_clientes'].append(cliente_id)
                            select.value = None
                            refresh_clientes_chips(container)
                        else:
                            ui.notify('Este cliente já está adicionado!', type='warning')
            
            with ui.row().classes('w-full gap-2 items-center'):
                clientes_sel = ui.select(
                    clientes_options or ['-'], 
                    label=make_required_label('Clientes'), 
                    with_input=True
                ).classes('flex-grow').props('dense outlined')
                clientes_sel.tooltip('Selecione os clientes envolvidos no acordo (pode adicionar múltiplos)')
                ui.button(icon='add', on_click=lambda: add_cliente(clientes_sel, clientes_chips)).props('flat dense').style('color: #4CAF50;')
            clientes_chips = ui.column().classes('w-full')
            
            # Parte Contrária (singular)
            todas_pessoas = listar_todas_pessoas()
            pessoas_options = [format_option_for_search_pessoa(p) for p in todas_pessoas]
            
            def refresh_parte_contraria_chip(container):
                """Atualiza chip da parte contrária com validação de DOM."""
                try:
                    if not container:
                        return
                    container.clear()
                    with container:
                        with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                            if state.get('parte_contraria_id'):
                                pessoa = next((p for p in todas_pessoas if p.get('_id') == state['parte_contraria_id']), None)
                                if pessoa:
                                    display = format_option_for_pessoa(pessoa)
                                    with ui.badge(display).classes('pr-1').style('background-color: #F44336; color: white;'):
                                        ui.button(
                                            icon='close', 
                                            on_click=lambda: remove_parte_contraria(parte_contraria_chips)
                                        ).props('flat dense round size=xs color=white')
                except Exception:
                    pass
            
            def remove_parte_contraria(container):
                """Remove parte contrária selecionada."""
                state['parte_contraria_id'] = None
                parte_contraria_sel.value = None
                refresh_parte_contraria_chip(container)
            
            def add_parte_contraria(select, container):
                """Adiciona parte contrária selecionada."""
                val = select.value
                if val and val != '-':
                    pessoa = next((p for p in todas_pessoas if format_option_for_search_pessoa(p) == val), None)
                    if pessoa:
                        pessoa_id = pessoa.get('_id') or get_display_name(pessoa)
                        
                        # Valida que não está nos clientes
                        if pessoa_id in state['selected_clientes']:
                            ui.notify('Esta pessoa já está entre os clientes!', type='warning')
                            return
                        
                        # Valida que não está em outros envolvidos
                        if pessoa_id in state['selected_outros_envolvidos']:
                            ui.notify('Esta pessoa já está entre os outros envolvidos!', type='warning')
                            return
                        
                        # Adiciona parte contrária
                        state['parte_contraria_id'] = pessoa_id
                        select.value = None
                        refresh_parte_contraria_chip(container)
                        ui.notify('Parte contrária adicionada!', type='positive')
                    else:
                        ui.notify('Pessoa não encontrada!', type='warning')
                else:
                    ui.notify('Selecione uma parte contrária!', type='warning')
            
            with ui.row().classes('w-full gap-2 items-center'):
                parte_contraria_sel = ui.select(
                    pessoas_options or ['-'], 
                    label=make_required_label('Parte Contrária'),
                    with_input=True
                ).classes('flex-grow').props('dense outlined')
                parte_contraria_sel.tooltip('Selecione a parte contrária do acordo')
                ui.button(icon='add', on_click=lambda: add_parte_contraria(parte_contraria_sel, parte_contraria_chips)).props('flat dense').style('color: #F44336;')
            parte_contraria_chips = ui.column().classes('w-full')
            
            # Outros Envolvidos (múltiplo)
            def refresh_outros_chips(container):
                """Atualiza chips de outros envolvidos com validação de DOM."""
                try:
                    if not container:
                        return
                    container.clear()
                    with container:
                        with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                            for pessoa_id in state['selected_outros_envolvidos']:
                                pessoa = next((p for p in todas_pessoas if (p.get('_id') == pessoa_id or get_display_name(p) == pessoa_id)), None)
                                if pessoa:
                                    display = format_option_for_pessoa(pessoa)
                                    with ui.badge(display).classes('pr-1').style('background-color: #2196F3; color: white;'):
                                        ui.button(
                                            icon='close', 
                                            on_click=lambda pid=pessoa_id: remove_outro(pid, outros_chips)
                                        ).props('flat dense round size=xs color=white')
                except Exception:
                    pass
            
            def remove_outro(pessoa_id, container):
                if pessoa_id in state['selected_outros_envolvidos']:
                    state['selected_outros_envolvidos'].remove(pessoa_id)
                    refresh_outros_chips(container)
            
            def add_outro(select, container):
                val = select.value
                if val and val != '-':
                    pessoa = next((p for p in todas_pessoas if format_option_for_pessoa(p) == val), None)
                    if pessoa:
                        pessoa_id = pessoa.get('_id') or get_display_name(pessoa)
                        # Valida que não está nos clientes
                        if pessoa_id in state['selected_clientes']:
                            ui.notify('Esta pessoa já está entre os clientes!', type='warning')
                            return
                        # Valida que não é a parte contrária
                        if state.get('parte_contraria_id') and pessoa_id == state['parte_contraria_id']:
                            ui.notify('Esta pessoa já está selecionada como parte contrária!', type='warning')
                            return
                        if pessoa_id and pessoa_id not in state['selected_outros_envolvidos']:
                            state['selected_outros_envolvidos'].append(pessoa_id)
                            select.value = None
                            refresh_outros_chips(container)
                        else:
                            ui.notify('Esta pessoa já está adicionada!', type='warning')
            
            with ui.row().classes('w-full gap-2 items-center'):
                outros_sel = ui.select(
                    pessoas_options or ['-'], 
                    label='Outros Envolvidos', 
                    with_input=True
                ).classes('flex-grow').props('dense outlined')
                outros_sel.tooltip('Outras pessoas envolvidas no acordo (opcional)')
                ui.button(icon='add', on_click=lambda: add_outro(outros_sel, outros_chips)).props('flat dense').style('color: #2196F3;')
            outros_chips = ui.column().classes('w-full')
    
    return clientes_sel, clientes_chips, parte_contraria_sel, parte_contraria_chips, outros_sel, outros_chips, refresh_clientes_chips, refresh_parte_contraria_chip, refresh_outros_chips

