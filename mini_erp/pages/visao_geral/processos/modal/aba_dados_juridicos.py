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
    if not status_antigo:
        return 'Em andamento'
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
    if not estado_antigo or estado_antigo not in ESTADOS:
        return 'Santa Catarina'
    return estado_antigo


def _migrar_nucleo(nucleo_antigo: str) -> str:
    """Migra núcleo para valores válidos."""
    if not nucleo_antigo or nucleo_antigo not in NUCLEOS_PROCESSO:
        return 'Ambiental'
    return nucleo_antigo


def _migrar_tipo_ambiental(tipo_antigo: str) -> str:
    """Migra tipo ambiental para valores válidos."""
    if not tipo_antigo or tipo_antigo not in TIPOS_PROCESSO_AMBIENTAL:
        return TIPO_AMBIENTAL_PADRAO
    return tipo_antigo


def _migrar_sistema_processual(sistema_antigo: str) -> str:
    """Migra sistema processual para valores válidos."""
    if not sistema_antigo:
        return ''
    if sistema_antigo not in SISTEMAS_PROCESSUAIS:
        return ''
    return sistema_antigo


def _migrar_area(area_antiga: str) -> str:
    """Migra área para valores válidos."""
    if not area_antiga:
        return ''
    if area_antiga not in AREAS_PROCESSO:
        return ''
    return area_antiga


def render_aba_dados_juridicos(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza a aba de Dados Jurídicos do modal.
    
    Args:
        dados: Dados do processo (se edição)
        
    Returns:
        Dicionário com referências aos campos criados
    """
    # Migrar valores antigos para evitar "Invalid value"
    status_valor = _migrar_status(dados.get('status', '') or '')
    estado_valor = _migrar_estado(dados.get('estado', '') or '')
    nucleo_valor = _migrar_nucleo(dados.get('nucleo', '') or '')
    tipo_ambiental_valor = _migrar_tipo_ambiental(dados.get('tipo_ambiental', '') or '')
    sistema_valor = _migrar_sistema_processual(dados.get('sistema_processual', '') or '')
    area_valor = _migrar_area(dados.get('area', '') or '')
    
    with ui.column().classes('w-full gap-4'):
        # Núcleo do escritório
        nucleo_select = ui.select(
            NUCLEOS_PROCESSO,
            label='Núcleo',
            value=nucleo_valor
        ).classes('w-full').props('outlined dense')
        
        # Container para tipo de processo ambiental (condicional)
        tipo_ambiental_container = ui.column().classes('w-full gap-2')
        tipo_ambiental_select = None
        
        with tipo_ambiental_container:
            tipo_ambiental_select = ui.select(
                TIPOS_PROCESSO_AMBIENTAL,
                label='Tipo de processo na matéria ambiental',
                value=tipo_ambiental_valor
            ).classes('w-full').props('outlined dense')
        
        # Função para mostrar/esconder campo tipo ambiental
        def toggle_tipo_ambiental():
            """
            Mostra/esconde campo de tipo ambiental baseado no núcleo selecionado.
            
            CORREÇÃO: Adicionado try-except para evitar erro de MutationObserver.
            """
            try:
                if nucleo_select and hasattr(nucleo_select, 'value'):
                    if nucleo_select.value == 'Ambiental':
                        tipo_ambiental_container.set_visibility(True)
                    else:
                        tipo_ambiental_container.set_visibility(False)
                        if tipo_ambiental_select:
                            tipo_ambiental_select.value = TIPO_AMBIENTAL_PADRAO
            except (AttributeError, TypeError):
                # Ignora erros de MutationObserver ou componente destruído
                pass
            except Exception as ex:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro ao alternar tipo ambiental: {ex}")
        
        # Configura evento e estado inicial com tratamento de erro
        try:
            nucleo_select.on_value_change(lambda e: toggle_tipo_ambiental())
            toggle_tipo_ambiental()  # Aplica estado inicial
        except Exception as ex:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro ao configurar evento on_value_change para núcleo: {ex}")
            # Tenta fallback
            try:
                nucleo_select.on('update:model-value', lambda e: toggle_tipo_ambiental())
                toggle_tipo_ambiental()
            except:
                pass
        
        system_select = ui.select(
            [''] + SISTEMAS_PROCESSUAIS,
            label='Sistema Processual',
            value=sistema_valor
        ).classes('w-full').props('outlined dense clearable')
        
        area_select = ui.select(
            [''] + AREAS_PROCESSO,
            label='Área',
            value=area_valor
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

