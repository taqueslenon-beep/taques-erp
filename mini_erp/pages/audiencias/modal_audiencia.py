"""
Modal para criar/editar audiências.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from nicegui import ui
from .models import MODALIDADES_AUDIENCIA, STATUS_AUDIENCIA
from .database import (
    criar_audiencia,
    atualizar_audiencia,
    buscar_clientes_para_select,
    buscar_usuarios_para_select,
)


def render_modal_audiencia(
    on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
    audiencia_inicial: Optional[Dict[str, Any]] = None
):
    """
    Renderiza modal para criar/editar audiência.
    
    Args:
        on_success: Callback chamado após salvar com sucesso
        audiencia_inicial: Dados da audiência para edição (None para criar nova)
    
    Returns:
        Tupla (dialog, função_abrir)
    """
    is_edicao = audiencia_inicial is not None
    titulo_modal = 'Editar Audiência' if is_edicao else 'Nova Audiência'
    
    # Carregar opções para selects
    clientes_opcoes = buscar_clientes_para_select()
    usuarios_opcoes = buscar_usuarios_para_select()
    
    # Garantir que há opções de usuários (fallback)
    if not usuarios_opcoes:
        print("[WARNING] Nenhum usuário encontrado. Usando opções padrão.")
        usuarios_opcoes = {
            'lenon_taques': 'Lenon Taques',
            'gilberto_taques': 'Gilberto Taques'
        }
    else:
        print(f"[DEBUG] Usuários carregados no modal: {usuarios_opcoes}")
    
    # Valores iniciais
    modalidade = audiencia_inicial.get('modalidade', 'presencial') if is_edicao else 'presencial'
    status = audiencia_inicial.get('status', 'em_aberto') if is_edicao else 'em_aberto'
    responsavel_id = audiencia_inicial.get('responsavel_id') if is_edicao else None
    
    # Converter timestamps para data/hora
    data_hora_inicio_ts = audiencia_inicial.get('data_hora_inicio') if is_edicao else None
    data_hora_fim_ts = audiencia_inicial.get('data_hora_fim') if is_edicao else None
    
    if data_hora_inicio_ts:
        dt_inicio = datetime.fromtimestamp(data_hora_inicio_ts)
        data_inicial = dt_inicio.strftime('%Y-%m-%d')
        hora_inicio_inicial = dt_inicio.strftime('%H:%M')
    else:
        data_inicial = datetime.now().strftime('%Y-%m-%d')
        hora_inicio_inicial = '10:00'
    
    if data_hora_fim_ts:
        dt_fim = datetime.fromtimestamp(data_hora_fim_ts)
        hora_fim_inicial = dt_fim.strftime('%H:%M')
    else:
        hora_fim_inicial = '11:00'
    
    titulo = audiencia_inicial.get('titulo', '') if is_edicao else ''
    clientes_ids = audiencia_inicial.get('clientes_ids', []) if is_edicao else []
    
    with ui.dialog().props('maximized') as dialog, ui.card().classes('w-full h-full'):
        with ui.column().classes('w-full h-full gap-4 p-6'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label(titulo_modal).classes('text-2xl font-bold')
                ui.button(icon='close', on_click=dialog.close).props('flat round dense')
            
            # Scroll area para formulário
            with ui.scroll_area().classes('flex-1 w-full'):
                with ui.column().classes('w-full gap-6 max-w-4xl'):
                    # Título da audiência
                    titulo_input = ui.input(
                        label='Título da Audiência',
                        value=titulo,
                        placeholder='Ex: Audiência de Conciliação'
                    ).classes('w-full').props('outlined')
                    
                    # Data da audiência
                    data_input = ui.input(
                        label='Data da Audiência',
                        value=data_inicial
                    ).classes('w-full').props('outlined type=date')
                    
                    # Hora de início e Hora fim
                    with ui.row().classes('w-full gap-4'):
                        hora_inicio_input = ui.input(
                            label='Hora de Início',
                            value=hora_inicio_inicial
                        ).classes('flex-1').props('outlined type=time')
                        
                        hora_fim_input = ui.input(
                            label='Hora Fim (previsão)',
                            value=hora_fim_inicial
                        ).classes('flex-1').props('outlined type=time')
                    
                    # Modalidade
                    modalidade_select = ui.select(
                        label='Modalidade',
                        options=MODALIDADES_AUDIENCIA,
                        value=modalidade
                    ).classes('w-full')
                    
                    # Responsável
                    responsavel_select = ui.select(
                        label='Responsável',
                        options=usuarios_opcoes,
                        value=responsavel_id,
                        with_input=True
                    ).classes('w-full')
                    
                    # Clientes (múltiplos)
                    clientes_select = ui.select(
                        label='Clientes',
                        options=clientes_opcoes,
                        value=clientes_ids,
                        multiple=True,
                        with_input=True
                    ).classes('w-full')
                    
                    # Status
                    status_select = ui.select(
                        label='Status',
                        options=STATUS_AUDIENCIA,
                        value=status
                    ).classes('w-full')
            
            # Footer com botões
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                
                def salvar_audiencia():
                    """Salva audiência no banco."""
                    try:
                        # Validações
                        if not titulo_input.value:
                            ui.notify('Título é obrigatório', type='warning')
                            return
                        
                        if not data_input.value:
                            ui.notify('Data é obrigatória', type='warning')
                            return
                        
                        if not hora_inicio_input.value:
                            ui.notify('Hora de início é obrigatória', type='warning')
                            return
                        
                        if not hora_fim_input.value:
                            ui.notify('Hora fim é obrigatória', type='warning')
                            return
                        
                        # Montar timestamps da data/hora início e fim
                        dt_inicio_str = f"{data_input.value} {hora_inicio_input.value}"
                        dt_inicio = datetime.strptime(dt_inicio_str, '%Y-%m-%d %H:%M')
                        data_hora_inicio_ts = dt_inicio.timestamp()
                        
                        dt_fim_str = f"{data_input.value} {hora_fim_input.value}"
                        dt_fim = datetime.strptime(dt_fim_str, '%Y-%m-%d %H:%M')
                        data_hora_fim_ts = dt_fim.timestamp()
                        
                        # Montar dados
                        dados = {
                            'titulo': titulo_input.value,
                            'data_hora_inicio': data_hora_inicio_ts,
                            'data_hora_fim': data_hora_fim_ts,
                            'modalidade': modalidade_select.value,
                            'responsavel_id': responsavel_select.value,
                            'clientes_ids': clientes_select.value or [],
                            'status': status_select.value,
                        }
                        
                        # Criar ou atualizar
                        if is_edicao:
                            audiencia_id = str(audiencia_inicial['_id'])
                            sucesso = atualizar_audiencia(audiencia_id, dados)
                            mensagem = 'Audiência atualizada com sucesso!'
                        else:
                            audiencia_id = criar_audiencia(dados)
                            sucesso = audiencia_id is not None
                            mensagem = 'Audiência criada com sucesso!'
                            dados['_id'] = audiencia_id
                        
                        if sucesso:
                            ui.notify(mensagem, type='positive')
                            dialog.close()
                            if on_success:
                                on_success(dados)
                        else:
                            ui.notify('Erro ao salvar audiência', type='negative')
                    
                    except Exception as e:
                        print(f"[ERROR] Erro ao salvar audiência: {e}")
                        ui.notify(f'Erro: {str(e)}', type='negative')
                
                ui.button('Salvar', on_click=salvar_audiencia).props('color=primary')
    
    return dialog, dialog.open
