"""
Aba de Dados Jurídicos do modal de processo (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any
from .helpers import make_required_label
from ..constants import (
    SISTEMAS_PROCESSUAIS, AREAS_PROCESSO, STATUS_PROCESSO, 
    ESTADOS, NUCLEOS_PROCESSO, TIPOS_PROCESSO_AMBIENTAL, TIPO_AMBIENTAL_PADRAO
)


def _migrar_status(status_antigo: str) -> str:
    """Migra status antigos para os novos valores."""
    mapeamento = {
        'Ativo': 'Em andamento',
        'Suspenso': 'Em monitoramento',
        'Arquivado': 'Concluído',
        'Baixado': 'Concluído',
        'Encerrado': 'Concluído',
    }
    status_novo = mapeamento.get(status_antigo, status_antigo)
    if status_novo not in STATUS_PROCESSO:
        status_novo = 'Em andamento'
    return status_novo


def _migrar_estado(estado_antigo: str) -> str:
    """Migra estados antigos para os novos valores."""
    if estado_antigo not in ESTADOS:
        return 'Santa Catarina'
    return estado_antigo


def render_aba_dados_juridicos(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza a aba de Dados Jurídicos do modal.
    
    Args:
        dados: Dados do processo (se edição)
        
    Returns:
        Dicionário com referências aos campos criados
    """
    # Migrar valores antigos
    status_valor = _migrar_status(dados.get('status', 'Em andamento'))
    estado_valor = _migrar_estado(dados.get('estado', 'Santa Catarina'))
    
    with ui.column().classes('w-full gap-4'):
        # Núcleo do escritório
        nucleo_select = ui.select(
            NUCLEOS_PROCESSO,
            label='Núcleo',
            value=dados.get('nucleo', 'Ambiental')
        ).classes('w-full').props('outlined dense')
        
        # Container para tipo de processo ambiental (condicional)
        tipo_ambiental_container = ui.column().classes('w-full gap-2')
        tipo_ambiental_select = None
        
        with tipo_ambiental_container:
            tipo_ambiental_select = ui.select(
                TIPOS_PROCESSO_AMBIENTAL,
                label='Tipo de processo na matéria ambiental',
                value=dados.get('tipo_ambiental', TIPO_AMBIENTAL_PADRAO)
            ).classes('w-full').props('outlined dense')
        
        # Função para mostrar/esconder campo tipo ambiental
        def toggle_tipo_ambiental():
            if nucleo_select.value == 'Ambiental':
                tipo_ambiental_container.set_visibility(True)
            else:
                tipo_ambiental_container.set_visibility(False)
                if tipo_ambiental_select:
                    tipo_ambiental_select.value = TIPO_AMBIENTAL_PADRAO
        
        # Configura evento e estado inicial
        nucleo_select.on_value_change(lambda e: toggle_tipo_ambiental())
        toggle_tipo_ambiental()  # Aplica estado inicial
        
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
            value=status_valor
        ).classes('w-full').props('outlined dense')
        
        # Estado
        estado_select = ui.select(
            ESTADOS,
            label='Estado',
            value=estado_valor
        ).classes('w-full').props('outlined dense')
    
    return {
        'nucleo_select': nucleo_select,
        'tipo_ambiental_select': tipo_ambiental_select,
        'system_select': system_select,
        'area_select': area_select,
        'status_select': status_select,
        'estado_select': estado_select,
    }

