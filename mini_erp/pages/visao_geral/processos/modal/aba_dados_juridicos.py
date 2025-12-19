"""
Aba de Dados Jurídicos do modal de processo (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any
from .helpers import make_required_label, should_show_result_field
from ..constants import SISTEMAS_PROCESSUAIS, AREAS_PROCESSO, STATUS_PROCESSO, RESULTADOS_PROCESSO, ESTADOS


def render_aba_dados_juridicos(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza a aba de Dados Jurídicos do modal.
    
    Args:
        dados: Dados do processo (se edição)
        
    Returns:
        Dicionário com referências aos campos criados
    """
    with ui.column().classes('w-full gap-4'):
        system_select = ui.select(
            [''] + SISTEMAS_PROCESSUAIS,
            label='Sistema Processual',
            value=dados.get('sistema_processual', '')
        ).classes('w-full').props('outlined dense clearable')
        
        area_select = ui.select(
            [''] + AREAS_PROCESSO,
            label='Área',
            value=dados.get('area', '')
        ).classes('w-full').props('outlined dense clearable')
        
        status_select = ui.select(
            STATUS_PROCESSO,
            label=make_required_label('Status'),
            value=dados.get('status', 'Ativo')
        ).classes('w-full').props('outlined dense')
        
        # Campo resultado (condicional)
        result_container = ui.column().classes('w-full gap-2 hidden')
        with result_container:
            result_select = ui.select(
                RESULTADOS_PROCESSO,
                label='Resultado do processo',
                value=dados.get('resultado', 'Pendente')
            ).classes('w-full').props('dense outlined')
        
        def toggle_result(e=None):
            val = status_select.value
            if should_show_result_field(val):
                result_container.classes(remove='hidden')
            else:
                result_container.classes(add='hidden')
                result_select.value = None
        
        status_select.on_value_change(toggle_result)
        
        # Estado e Comarca
        with ui.row().classes('w-full gap-4'):
            estado_select = ui.select(
                [''] + ESTADOS,
                label='Estado',
                value=dados.get('estado', 'Santa Catarina')
            ).classes('flex-1').props('outlined dense clearable')
            
            comarca_input = ui.input(
                'Comarca',
                value=dados.get('comarca', '')
            ).classes('flex-1').props('outlined dense')
        
        vara_input = ui.input(
            'Vara',
            value=dados.get('vara', '')
        ).classes('w-full').props('outlined dense')
    
    return {
        'system_select': system_select,
        'area_select': area_select,
        'status_select': status_select,
        'result_select': result_select,
        'result_container': result_container,
        'estado_select': estado_select,
        'comarca_input': comarca_input,
        'vara_input': vara_input,
        'toggle_result': toggle_result,
    }

