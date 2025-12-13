"""
modal_prazo.py - Modal para criar/editar prazo.
"""

from nicegui import ui
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from ...core import PRIMARY_COLOR
from .database import (
    criar_prazo,
    atualizar_prazo,
    buscar_usuarios_para_select,
    buscar_clientes_para_select,
    buscar_casos_para_select,
)
from .models import (
    STATUS_OPCOES,
    STATUS_LABELS,
    TIPOS_RECORRENCIA,
    TIPOS_RECORRENCIA_LABELS,
    OPCOES_SEMANA,
    OPCOES_SEMANA_LABELS,
    OPCOES_DIA_SEMANA,
    OPCOES_DIA_SEMANA_LABELS,
)
from ...auth import get_current_user


def validar_data_br(data_str: str) -> bool:
    """
    Valida formato de data brasileira DD/MM/AAAA.
    
    Args:
        data_str: String com data em formato DD/MM/AAAA
    
    Returns:
        True se válida, False caso contrário
    """
    import re
    
    if not data_str or not isinstance(data_str, str):
        return False
    
    # Verificar formato
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', data_str.strip()):
        return False
    
    try:
        dia, mes, ano = data_str.strip().split('/')
        dia, mes, ano = int(dia), int(mes), int(ano)
        
        # Validar ranges
        if mes < 1 or mes > 12:
            return False
        if ano < 1900 or ano > 2100:
            return False
        
        # Dias por mês (simplificado - não considera anos bissextos)
        dias_mes = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        if dia < 1 or dia > dias_mes[mes - 1]:
            return False
        
        return True
    except Exception:
        return False


def converter_data_br_para_timestamp(data_str: str) -> Optional[float]:
    """
    Converte data no formato DD/MM/AAAA para timestamp.
    
    Args:
        data_str: Data no formato DD/MM/AAAA
    
    Returns:
        Timestamp (float) ou None se inválida
    """
    if not validar_data_br(data_str):
        return None
    
    try:
        dia, mes, ano = data_str.strip().split('/')
        dt = datetime(int(ano), int(mes), int(dia))
        return dt.timestamp()
    except Exception:
        return None


def converter_timestamp_para_data_br(timestamp: Optional[float]) -> str:
    """
    Converte timestamp para data no formato DD/MM/AAAA.
    
    Args:
        timestamp: Timestamp (float) ou None
    
    Returns:
        Data formatada como DD/MM/AAAA ou string vazia
    """
    if not timestamp:
        return ''
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return ''


def render_prazo_dialog(
    on_success: Optional[Callable] = None,
    prazo_inicial: Optional[Dict] = None,
    usuarios_opcoes: Optional[Dict[str, str]] = None,
    clientes_opcoes: Optional[Dict[str, str]] = None,
    casos_opcoes: Optional[Dict[str, str]] = None
):
    """
    Renderiza dialog para criar ou editar prazo.

    Args:
        on_success: Callback executado após salvar
        prazo_inicial: Dicionário com dados do prazo para edição (None para novo)
        usuarios_opcoes: Opções de usuários (se None, busca do banco)
        clientes_opcoes: Opções de clientes (se None, busca do banco)
        casos_opcoes: Opções de casos (se None, busca do banco)

    Returns:
        tuple: (dialog, open_function)
    """

    # Determinar se é edição ou criação
    is_edicao = prazo_inicial is not None
    prazo_id = prazo_inicial.get('_id') if is_edicao else None

    # Estado do formulário - preencher com dados iniciais se for edição
    config_recorrencia_inicial = prazo_inicial.get('config_recorrencia', {}) if is_edicao else {}
    dia_semana_inicial = config_recorrencia_inicial.get('dia_semana_especifico', {})

    state = {
        'titulo': prazo_inicial.get('titulo', '') if is_edicao else '',
        'responsaveis': prazo_inicial.get('responsaveis', []) if is_edicao else [],
        'clientes': prazo_inicial.get('clientes', []) if is_edicao else [],
        'casos': prazo_inicial.get('casos', []) if is_edicao else [],
        'prazo_fatal': converter_timestamp_para_data_br(
            prazo_inicial.get('prazo_fatal')
        ) if is_edicao else '',
        'status': prazo_inicial.get('status', 'pendente') if is_edicao else 'pendente',
        'recorrente': prazo_inicial.get('recorrente', False) if is_edicao else False,
        'tipo_recorrencia': config_recorrencia_inicial.get('tipo', 'mensal') if is_edicao else 'mensal',
        'dia_especifico': config_recorrencia_inicial.get('dia_especifico') if is_edicao else None,
        'ultimo_dia_mes': config_recorrencia_inicial.get('ultimo_dia_mes', False) if is_edicao else False,
        'semana_especifica': dia_semana_inicial.get('semana', 'primeira') if is_edicao else 'primeira',
        'dia_semana': dia_semana_inicial.get('dia', 'segunda') if is_edicao else 'segunda',
        'observacoes': prazo_inicial.get('observacoes', '') if is_edicao else '',
    }

    # Usar opções passadas ou buscar do banco (com cache)
    if usuarios_opcoes is None:
        usuarios_opcoes = buscar_usuarios_para_select()
    if clientes_opcoes is None:
        clientes_opcoes = buscar_clientes_para_select()
    if casos_opcoes is None:
        casos_opcoes = buscar_casos_para_select()

    # Fallback se não houver usuários
    if not usuarios_opcoes:
        usuarios_opcoes = {'-': 'Nenhum usuário cadastrado'}

    # Dialog principal
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl p-0 overflow-hidden'):
        with ui.column().classes('w-full gap-0'):
            # Cabeçalho
            titulo_dialog = ui.label(
                'Editar Prazo' if is_edicao else 'Novo Prazo'
            ).classes('text-xl font-bold p-4 bg-gray-50 border-b')
            
            # Conteúdo (scrollável)
            with ui.column().classes('w-full p-6 gap-4 overflow-auto').style('max-height: 70vh;'):
                
                # Título
                titulo_input = ui.input(
                    label='Título *',
                    placeholder='Digite o título do prazo',
                    value=state['titulo']
                ).classes('w-full').props('outlined dense')
                
                # Responsáveis (múltiplo) - usando mesma lógica de casos_page.py
                ui.label('Responsável(is) *').classes('text-sm font-medium text-gray-700')
                responsaveis_select = ui.select(
                    options=usuarios_opcoes,
                    label='Selecione o(s) responsável(eis)',
                    value=state['responsaveis'],
                    with_input=True,
                    multiple=True
                ).classes('w-full').props('use-chips clearable outlined dense')
                
                # Clientes (múltiplo)
                ui.label('Clientes').classes('text-sm font-medium text-gray-700 mt-2')
                clientes_select = ui.select(
                    options=clientes_opcoes,
                    label='Selecione os clientes',
                    value=state['clientes'],
                    with_input=True,
                    multiple=True
                ).classes('w-full').props('use-chips clearable outlined dense')

                # Casos (múltiplo)
                ui.label('Casos').classes('text-sm font-medium text-gray-700 mt-2')
                casos_select = ui.select(
                    options=casos_opcoes,
                    label='Selecione os casos',
                    value=state['casos'],
                    with_input=True,
                    multiple=True
                ).classes('w-full').props('use-chips clearable outlined dense')
                
                # Prazo Fatal
                prazo_fatal_input = ui.input(
                    label='Prazo Fatal *',
                    placeholder='DD/MM/AAAA',
                    value=state['prazo_fatal']
                ).classes('w-full').props('outlined dense')
                prazo_fatal_input.validation = {'Data inválida': validar_data_br}
                
                # Status
                status_options = {op: STATUS_LABELS.get(op, op) for op in STATUS_OPCOES}
                status_select = ui.select(
                    status_options,
                    label='Status',
                    value=state['status']
                ).classes('w-full').props('outlined dense')
                
                # Recorrente (switch)
                recorrente_switch = ui.switch(
                    'Recorrente',
                    value=state['recorrente']
                ).classes('w-full')
                
                # Seção de Recorrência (condicional)
                # Variáveis para armazenar referências dos campos de recorrência
                refs_recorrencia = {
                    'tipo_select': None,
                    'dia_especifico_input': None,
                    'ultimo_dia_checkbox': None,
                    'semana_select': None,
                    'dia_semana_select': None,
                }
                
                recorrencia_container = ui.column().classes('w-full gap-4')
                
                def render_secao_recorrencia():
                    """Renderiza seção de recorrência baseado no switch."""
                    recorrencia_container.clear()
                    # Limpar referências
                    for key in refs_recorrencia:
                        refs_recorrencia[key] = None
                    
                    if recorrente_switch.value:
                        with recorrencia_container:
                            ui.label('Configuração de Recorrência').classes(
                                'text-sm font-bold text-gray-700'
                            )
                            
                            # Tipo de recorrência
                            tipo_options = {
                                op: TIPOS_RECORRENCIA_LABELS.get(op, op)
                                for op in TIPOS_RECORRENCIA
                            }
                            tipo_recorrencia_select = ui.select(
                                tipo_options,
                                label='Tipo de Recorrência',
                                value=state['tipo_recorrencia']
                            ).classes('w-full').props('outlined dense')
                            refs_recorrencia['tipo_select'] = tipo_recorrencia_select
                            
                            # Container para opções específicas
                            opcoes_especificas_container = ui.column().classes('w-full gap-2')
                            
                            def render_opcoes_especificas():
                                """Renderiza opções específicas baseado no tipo."""
                                opcoes_especificas_container.clear()
                                tipo = tipo_recorrencia_select.value if tipo_recorrencia_select else state['tipo_recorrencia']
                                
                                if tipo in ['mensal', 'anual']:
                                    with opcoes_especificas_container:
                                        with ui.row().classes('w-full gap-4 items-center'):
                                            dia_especifico_input = ui.number(
                                                label='Dia específico (1-31)',
                                                value=state.get('dia_especifico'),
                                                min=1,
                                                max=31
                                            ).classes('flex-1').props('outlined dense')
                                            refs_recorrencia['dia_especifico_input'] = dia_especifico_input
                                            
                                            ultimo_dia_checkbox = ui.checkbox(
                                                'Último dia do mês',
                                                value=state.get('ultimo_dia_mes', False)
                                            ).classes('flex-1')
                                            refs_recorrencia['ultimo_dia_checkbox'] = ultimo_dia_checkbox
                                
                                elif tipo == 'semanal':
                                    with opcoes_especificas_container:
                                        semana_options = {
                                            op: OPCOES_SEMANA_LABELS.get(op, op)
                                            for op in OPCOES_SEMANA
                                        }
                                        semana_select = ui.select(
                                            semana_options,
                                            label='Qual semana',
                                            value=state.get('semana_especifica', 'primeira')
                                        ).classes('w-full').props('outlined dense')
                                        refs_recorrencia['semana_select'] = semana_select
                                        
                                        dia_semana_options = {
                                            op: OPCOES_DIA_SEMANA_LABELS.get(op, op)
                                            for op in OPCOES_DIA_SEMANA
                                        }
                                        dia_semana_select = ui.select(
                                            dia_semana_options,
                                            label='Qual dia da semana',
                                            value=state.get('dia_semana', 'segunda')
                                        ).classes('w-full').props('outlined dense')
                                        refs_recorrencia['dia_semana_select'] = dia_semana_select
                            
                            # Renderizar opções específicas inicialmente
                            render_opcoes_especificas()
                            
                            # Atualizar quando tipo mudar
                            tipo_recorrencia_select.on(
                                'update:model-value',
                                lambda: render_opcoes_especificas()
                            )
                
                # Renderizar seção de recorrência inicialmente
                render_secao_recorrencia()
                
                # Atualizar quando switch mudar
                recorrente_switch.on('update:model-value', lambda: render_secao_recorrencia())
                
                # Observações
                observacoes_input = ui.textarea(
                    label='Observações',
                    placeholder='Digite observações adicionais',
                    value=state['observacoes']
                ).classes('w-full').props('outlined dense rows=3')
            
            # Rodapé com botões
            with ui.row().classes('w-full gap-4 p-4 justify-end border-t bg-gray-50'):
                def on_cancel():
                    """Cancela e fecha o dialog."""
                    dialog.close()
                
                def on_save():
                    """Salva o prazo."""
                    # Validar título
                    if not titulo_input.value or not titulo_input.value.strip():
                        ui.notify('Título é obrigatório!', type='warning')
                        return
                    
                    # Validar responsáveis (pelo menos 1 obrigatório)
                    responsaveis_selecionados = responsaveis_select.value or []
                    if not responsaveis_selecionados or len(responsaveis_selecionados) == 0:
                        ui.notify('Selecione pelo menos um responsável!', type='warning')
                        return
                    
                    # Validar prazo fatal
                    if not prazo_fatal_input.value or not validar_data_br(prazo_fatal_input.value):
                        ui.notify('Prazo fatal inválido! Use o formato DD/MM/AAAA', type='warning')
                        return
                    
                    # Converter data para timestamp
                    prazo_fatal_ts = converter_data_br_para_timestamp(
                        prazo_fatal_input.value
                    )
                    if not prazo_fatal_ts:
                        ui.notify('Erro ao converter data do prazo fatal', type='negative')
                        return
                    
                    # Preparar dados do prazo
                    prazo_data = {
                        'titulo': titulo_input.value.strip(),
                        'responsaveis': responsaveis_select.value or [],
                        'clientes': clientes_select.value or [],
                        'casos': casos_select.value or [],
                        'prazo_fatal': prazo_fatal_ts,
                        'status': status_select.value or 'pendente',
                        'recorrente': recorrente_switch.value or False,
                        'observacoes': observacoes_input.value or '',
                    }
                    
                    # Configuração de recorrência (se recorrente)
                    if recorrente_switch.value:
                        tipo = refs_recorrencia['tipo_select'].value if refs_recorrencia['tipo_select'] else state['tipo_recorrencia']
                        config_recorrencia = {
                            'tipo': tipo,
                        }
                        
                        if tipo in ['mensal', 'anual']:
                            if refs_recorrencia['dia_especifico_input']:
                                dia = refs_recorrencia['dia_especifico_input'].value
                                if dia and 1 <= dia <= 31:
                                    config_recorrencia['dia_especifico'] = int(dia)
                            
                            if refs_recorrencia['ultimo_dia_checkbox']:
                                config_recorrencia['ultimo_dia_mes'] = refs_recorrencia['ultimo_dia_checkbox'].value
                        
                        elif tipo == 'semanal':
                            semana = refs_recorrencia['semana_select'].value if refs_recorrencia['semana_select'] else 'primeira'
                            dia_semana = refs_recorrencia['dia_semana_select'].value if refs_recorrencia['dia_semana_select'] else 'segunda'
                            
                            config_recorrencia['dia_semana_especifico'] = {
                                'semana': semana,
                                'dia': dia_semana,
                            }
                        
                        prazo_data['config_recorrencia'] = config_recorrencia
                    
                    # Adicionar criado_por se for novo
                    if not is_edicao:
                        usuario_atual = get_current_user()
                        if usuario_atual:
                            prazo_data['criado_por'] = usuario_atual.get('uid') or usuario_atual.get('email', '')
                    
                    try:
                        # Salvar no banco
                        if is_edicao and prazo_id:
                            sucesso = atualizar_prazo(prazo_id, prazo_data)
                            if not sucesso:
                                raise Exception('Erro ao atualizar prazo')
                        else:
                            prazo_id_novo = criar_prazo(prazo_data)
                            prazo_data['_id'] = prazo_id_novo
                        
                        # Chamar callback se fornecido
                        if on_success:
                            on_success(prazo_data)
                        
                        ui.notify(
                            'Prazo salvo com sucesso!' if is_edicao else 'Prazo criado com sucesso!',
                            type='positive'
                        )
                        
                        # Fechar dialog
                        dialog.close()
                        
                    except Exception as e:
                        print(f"Erro ao salvar prazo: {e}")
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao salvar prazo: {str(e)}', type='negative')
                
                ui.button('Cancelar', icon='close', on_click=on_cancel).props('flat')
                ui.button('Salvar', icon='save', on_click=on_save).props('color=primary')
    
    def open_dialog():
        """Abre o dialog."""
        dialog.open()

    return dialog, open_dialog

