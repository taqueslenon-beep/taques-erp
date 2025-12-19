"""
Aba de Cenários do modal de processo (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any
from .helpers import get_scenario_type_style
from ..constants import SCENARIO_TYPE_OPTIONS, SCENARIO_CHANCE_OPTIONS, SCENARIO_IMPACT_OPTIONS, SCENARIO_STATUS_OPTIONS


def render_aba_cenarios(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza a aba de Cenários do modal.
    
    Args:
        state: Estado do modal
        
    Returns:
        Dicionário com referências aos componentes criados
    """
    # Dialog de cenário
    with ui.dialog() as scen_dialog, ui.card().classes('p-4 w-96'):
        scen_idx_ref = {'val': None}
        ui.label('Cenário').classes('text-lg font-bold mb-2')
        s_title = ui.input('Título').classes('w-full').props('dense outlined')
        s_type = ui.select(SCENARIO_TYPE_OPTIONS, label='Tipo').classes('w-full').props('dense outlined')
        s_status = ui.select(SCENARIO_STATUS_OPTIONS, label='Status').classes('w-full').props('dense outlined')
        s_impact = ui.select(SCENARIO_IMPACT_OPTIONS, label='Impacto').classes('w-full').props('dense outlined')
        s_chance = ui.select(SCENARIO_CHANCE_OPTIONS, label='Chance').classes('w-full').props('dense outlined')
        s_obs = ui.textarea('Observações').classes('w-full').props('dense outlined rows=2')
        
        def save_scenario():
            if s_title.value:
                data = {
                    'title': s_title.value,
                    'type': s_type.value,
                    'status': s_status.value,
                    'impact': s_impact.value,
                    'chance': s_chance.value,
                    'obs': s_obs.value
                }
                if scen_idx_ref['val'] is not None:
                    state['scenarios'][scen_idx_ref['val']] = data
                else:
                    state['scenarios'].append(data)
                scen_dialog.close()
                render_scenarios.refresh()
        
        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            ui.button('Cancelar', on_click=scen_dialog.close).props('flat')
            ui.button('Salvar', on_click=save_scenario).props('color=primary')
        
        def open_scen_dialog(idx=None):
            scen_idx_ref['val'] = idx
            if idx is not None:
                d = state['scenarios'][idx]
                s_title.value = d.get('title', '')
                s_type.value = d.get('type')
                s_status.value = d.get('status')
                s_impact.value = d.get('impact')
                s_chance.value = d.get('chance')
                s_obs.value = d.get('obs', '')
            else:
                s_title.value = ''
                s_type.value = None
                s_status.value = None
                s_impact.value = None
                s_chance.value = None
                s_obs.value = ''
            scen_dialog.open()
    
    ui.button('+ Novo Cenário', on_click=lambda: open_scen_dialog(None)).props('flat dense color=primary')
    
    @ui.refreshable
    def render_scenarios():
        if not state.get('scenarios', []):
            ui.label('Nenhum cenário.').classes('text-gray-400 italic text-sm')
            return
        for i, s in enumerate(state['scenarios']):
            tipo = s.get('type', '⚪ Neutro')
            _, cor_hex = get_scenario_type_style(tipo)
            with ui.card().classes('w-full p-3 mb-2').style(f'border-left: 3px solid {cor_hex};'):
                with ui.row().classes('w-full justify-between'):
                    with ui.column():
                        ui.label(s.get('title', '-')).classes('font-medium')
                        ui.label(tipo).style(f'color: {cor_hex}').classes('text-xs')
                    with ui.row():
                        ui.button(
                            icon='edit',
                            on_click=lambda idx=i: open_scen_dialog(idx)
                        ).props('flat dense size=sm color=primary')
                        def rm_scen(idx=i):
                            state['scenarios'].pop(idx)
                            render_scenarios.refresh()
                        ui.button(icon='delete', on_click=rm_scen).props('flat dense size=sm color=red')
    
    render_scenarios()
    
    return {
        'render_scenarios': render_scenarios,
    }

