"""
Aba de Protocolos do modal de processo (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any
from mini_erp.core import format_date_br
from ..constants import SISTEMAS_PROCESSUAIS


def render_aba_protocolos(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza a aba de Protocolos do modal.
    
    Args:
        state: Estado do modal
        
    Returns:
        Dicionário com referências aos componentes criados
    """
    # Dialog para protocolo
    with ui.dialog() as prot_dialog, ui.card().classes('p-4 w-96'):
        prot_title_label = ui.label('Novo Protocolo').classes('text-lg font-bold mb-2')
        p_title = ui.input('Título').classes('w-full').props('dense outlined')
        p_date = ui.input('Data').classes('w-full').props('dense outlined type=date')
        p_number = ui.input('Número do protocolo').classes('w-full').props('dense outlined')
        p_system = ui.select(
            [''] + SISTEMAS_PROCESSUAIS,
            label='Sistema processual',
            with_input=True
        ).classes('w-full').props('dense outlined clearable')
        p_obs = ui.textarea('Observações').classes('w-full').props('dense outlined rows=3')
        
        prot_idx_ref = {'val': None}
        
        def save_protocol_local():
            if p_title.value:
                data = {
                    'title': p_title.value,
                    'date': p_date.value,
                    'number': p_number.value,
                    'system': p_system.value,
                    'observations': p_obs.value
                }
                if prot_idx_ref['val'] is not None:
                    state['protocols'][prot_idx_ref['val']] = data
                else:
                    state['protocols'].append(data)
                prot_dialog.close()
                render_protocols.refresh()
        
        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            ui.button('Cancelar', on_click=prot_dialog.close).props('flat')
            prot_save_btn = ui.button('Adicionar', on_click=save_protocol_local).props('color=primary')
        
        def open_prot_dialog(idx=None):
            prot_idx_ref['val'] = idx
            if idx is not None:
                d = state['protocols'][idx]
                prot_title_label.text = 'Editar Protocolo'
                prot_save_btn.text = 'Salvar'
                p_title.value = d.get('title', '')
                p_date.value = d.get('date', '')
                p_number.value = d.get('number', '')
                p_system.value = d.get('system')
                p_obs.value = d.get('observations', '')
            else:
                prot_title_label.text = 'Novo Protocolo'
                prot_save_btn.text = 'Adicionar'
                p_title.value = ''
                p_date.value = ''
                p_number.value = ''
                p_system.value = None
                p_obs.value = ''
            prot_dialog.open()
    
    ui.button('+ Novo Protocolo', on_click=lambda: open_prot_dialog(None)).props('flat dense color=primary')
    
    @ui.refreshable
    def render_protocols():
        if not state.get('protocols', []):
            ui.label('Nenhum protocolo.').classes('text-gray-400 italic text-sm')
            return
        for i, p in enumerate(state['protocols']):
            with ui.card().classes('w-full p-2 mb-2'):
                with ui.row().classes('w-full justify-between'):
                    with ui.column().classes('gap-1'):
                        ui.label(p.get('title', '-')).classes('font-medium text-sm')
                        date_str = format_date_br(p.get('date')) if p.get('date') else '-'
                        number_str = f"Nº {p.get('number')}" if p.get('number') else ''
                        system_str = p.get('system', '') if p.get('system') else ''
                        info_parts = [part for part in [date_str, number_str, system_str] if part]
                        ui.label(' • '.join(info_parts) if info_parts else '-').classes('text-xs text-gray-600')
                        if p.get('observations'):
                            ui.label(p.get('observations')).classes('text-xs text-gray-500 mt-1')
                    with ui.row():
                        ui.button(
                            icon='edit',
                            on_click=lambda idx=i: open_prot_dialog(idx)
                        ).props('flat dense size=sm color=primary')
                        def rm_prot(idx=i):
                            state['protocols'].pop(idx)
                            render_protocols.refresh()
                        ui.button(icon='delete', on_click=rm_prot).props('flat dense size=sm color=red')
    
    render_protocols()
    
    return {
        'render_protocols': render_protocols,
    }

