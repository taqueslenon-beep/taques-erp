"""
Modal de criação e edição de processos - Visão Geral do Escritório.
Replica estrutura do modal do Schmidmeier removendo abas de Senhas e Slack.
"""
from nicegui import ui
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from ....core import (
    PRIMARY_COLOR, format_date_br, get_display_name
)
from .database import (
    criar_processo, atualizar_processo, excluir_processo,
    buscar_processo, listar_processos_pais
)
from .models import (
    TIPOS_PROCESSO, STATUS_PROCESSO, RESULTADOS_PROCESSO,
    AREAS_PROCESSO, SISTEMAS_PROCESSUAIS, ESTADOS,
    validar_processo, criar_processo_vazio
)
from ..pessoas.database import listar_pessoas
from ..casos.database import listar_casos

# Constantes para cenários (similares ao Schmidmeier)
SCENARIO_TYPE_OPTIONS = ['🟢 Positivo', '⚪ Neutro', '🔴 Negativo']
SCENARIO_CHANCE_OPTIONS = ['Muito alta', 'Alta', 'Média', 'Baixa', 'Muito baixa']
SCENARIO_IMPACT_OPTIONS = ['Muito bom', 'Bom', 'Moderado', 'Ruim', 'Muito ruim']
SCENARIO_STATUS_OPTIONS = ['Mapeado', 'Em análise', 'Próximo de ocorrer', 'Ocorrido', 'Descartado']

# CSS para sidebar (mesmo do Schmidmeier)
PROCESSES_TABLE_CSS = '''
    .process-sidebar-tabs .q-tab {
        justify-content: flex-start !important;
        flex-direction: row !important;
        padding: 6px 12px !important;
        min-height: 32px !important;
        height: 32px !important;
        font-size: 11px !important;
        color: white !important;
        border-radius: 0 !important;
        text-transform: none !important;
        text-align: left !important;
        align-items: center !important;
    }
    .process-sidebar-tabs .q-tab:hover {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
    }
    .process-sidebar-tabs .q-tab--active {
        background: rgba(255,255,255,0.12) !important;
        color: white !important;
        border-left: 2px solid rgba(255,255,255,0.8) !important;
    }
    .process-sidebar-tabs .q-tab__content {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        width: 100% !important;
    }
    .process-sidebar-tabs .q-tab__icon {
        font-size: 16px !important;
        margin: 0 !important;
        color: white !important;
        align-self: center !important;
        flex-shrink: 0 !important;
    }
    .process-sidebar-tabs .q-tab__label {
        font-weight: 400 !important;
        letter-spacing: 0.2px !important;
        color: white !important;
        text-align: left !important;
        align-self: center !important;
    }
    .process-sidebar-tabs .q-tabs__content {
        overflow: visible !important;
    }
    .process-sidebar-tabs .q-tab__indicator {
        display: none !important;
    }
'''


def make_required_label(text: str) -> str:
    """Adiciona asterisco ao final do label para campos obrigatórios."""
    return f'{text} *'


def get_short_name(full_name: str, source_list: List[Dict[str, Any]]) -> str:
    """Retorna nome de exibição usando get_display_name."""
    if not full_name or not source_list:
        return full_name.split()[0] if full_name else full_name
    
    for item in source_list:
        item_name = item.get('name') or item.get('full_name', '')
        item_display = get_display_name(item)
        
        if item_name == full_name or item_display == full_name:
            display_name = get_display_name(item)
            if display_name:
                return display_name
            nome_exibicao = item.get('nome_exibicao', '').strip()
            if nome_exibicao:
                return nome_exibicao
    
    return full_name.split()[0] if full_name else full_name


def format_option_for_search(item: Dict[str, Any]) -> str:
    """Formata opção para busca: exibe nome de exibição."""
    display_name = get_display_name(item)
    if display_name:
        return display_name
    return item.get('name', '') or item.get('full_name', '')


def get_option_value(formatted_option: str, source_list: List[Dict[str, Any]]) -> str:
    """Extrai o nome completo de uma opção formatada."""
    if '(' in formatted_option:
        return formatted_option.split(' (')[0]
    return formatted_option


def get_scenario_type_style(tipo: Optional[str]) -> tuple:
    """Retorna cor baseada no tipo de cenário."""
    if 'Positivo' in str(tipo):
        return 'green', '#22c55e'
    if 'Negativo' in str(tipo):
        return 'red', '#ef4444'
    return 'grey', '#9ca3af'


def should_show_result_field(status: str) -> bool:
    """Verifica se deve mostrar campo de resultado baseado no status."""
    return status in ['Concluído', 'Concluído com pendências', 'Baixado', 'Encerrado']


def abrir_dialog_processo(processo: Optional[dict] = None, on_save: Optional[Callable] = None):
    """
    Abre dialog para criar ou editar um processo.
    Replica estrutura do modal do Schmidmeier.
    
    Args:
        processo: Dicionário com dados do processo (None para criar novo)
        on_save: Callback executado após salvar com sucesso
    """
    is_edicao = processo is not None
    dados = processo.copy() if processo else criar_processo_vazio()
    
    # Estado local
    state = {
        'is_editing': is_edicao,
        'process_id': dados.get('_id') if is_edicao else None,
        'processo_pai_id': dados.get('processo_pai_id', '') or '',  # Singular na Visão Geral
        'scenarios': [],  # Cenários serão carregados do campo scenarios se existir
        'protocols': dados.get('protocols', []) if isinstance(dados.get('protocols'), list) else [],
        'selected_clients': dados.get('clientes', []) if isinstance(dados.get('clientes'), list) else [],
        'selected_opposing': dados.get('parte_contraria', '') if isinstance(dados.get('parte_contraria'), str) else (dados.get('parte_contraria', []) if isinstance(dados.get('parte_contraria'), list) else []),
        'selected_others': [],
        'selected_cases': [dados.get('caso_titulo')] if dados.get('caso_titulo') else [],
    }
    
    # Converter parte contrária de string para lista se necessário
    if isinstance(state['selected_opposing'], str) and state['selected_opposing']:
        state['selected_opposing'] = [state['selected_opposing']]
    
    # Carregar dados auxiliares
    todas_pessoas = listar_pessoas()
    todos_casos = listar_casos()
    
    # CSS do modal
    ui.add_head_html(f'<style>{PROCESSES_TABLE_CSS}</style>')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden relative').style('height: 80vh; max-height: 80vh;'):
        with ui.row().classes('w-full h-full gap-0'):
            # Sidebar com abas
            with ui.column().classes('h-full shrink-0 justify-between').style(f'width: 170px; background: {PRIMARY_COLOR};'):
                with ui.column().classes('w-full gap-0'):
                    dialog_title = ui.label('NOVO PROCESSO' if not is_edicao else 'EDITAR PROCESSO').classes(
                        'text-xs font-medium px-3 py-2 text-white/80 uppercase tracking-wide'
                    )
                    
                    with ui.tabs().props('vertical dense no-caps inline-label').classes('w-full process-sidebar-tabs') as tabs:
                        tab_basic = ui.tab('Dados básicos', icon='description')
                        tab_legal = ui.tab('Dados jurídicos', icon='gavel')
                        tab_relatory = ui.tab('Relatório', icon='article')
                        tab_strategy = ui.tab('Estratégia', icon='lightbulb')
                        tab_scenarios = ui.tab('Cenários', icon='analytics')
                        tab_protocols = ui.tab('Protocolos', icon='history')
            
            # Content
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_basic).classes('w-full h-full p-4 bg-transparent'):
                    
                    # ============================================================
                    # TAB 1: DADOS BÁSICOS
                    # ============================================================
                    with ui.tab_panel(tab_basic):
                        with ui.column().classes('w-full gap-4'):
                            
                            # Mapeamento de cores para tags
                            TAG_COLORS = {
                                'clients': '#4CAF50',
                                'opposing': '#F44336',
                                'others': '#2196F3',
                                'cases': '#9C27B0'
                            }
                            
                            # Helper para refresh chips
                            def refresh_chips(container, items, tag_type, source_list):
                                container.clear()
                                safe_source = source_list or []
                                chip_color = TAG_COLORS.get(tag_type, '#6B7280')
                                with container:
                                    with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                        for item in items:
                                            short = get_short_name(item, safe_source) if safe_source else item
                                            with ui.badge(short).classes('pr-1').style(f'background-color: {chip_color}; color: white;'):
                                                ui.button(
                                                    icon='close',
                                                    on_click=lambda i=item: remove_item(items, i, container, tag_type, source_list)
                                                ).props('flat dense round size=xs color=white')
                            
                            def remove_item(list_ref, item, container, tag_type, source_list):
                                if item in list_ref:
                                    list_ref.remove(item)
                                    refresh_chips(container, list_ref, tag_type, source_list)
                            
                            def add_item(select, list_ref, container, tag_type, source_list):
                                val = select.value
                                if val and val != '-' and val not in list_ref:
                                    full_name = get_option_value(val, source_list) if source_list else val
                                    display_name = full_name
                                    if source_list:
                                        for person in source_list:
                                            person_full_name = person.get('full_name') or person.get('name', '')
                                            if person_full_name == full_name:
                                                display_name = get_display_name(person)
                                                break
                                    if display_name not in list_ref:
                                        list_ref.append(display_name)
                                        select.value = None
                                        refresh_chips(container, list_ref, tag_type, source_list)
                            
                            # Helper para processos pais (na Visão Geral suporta apenas um processo pai)
                            def refresh_parent_chips(container, processo_pai_id):
                                container.clear()
                                if not processo_pai_id:
                                    return
                                
                                all_procs = listar_processos_pais()
                                proc = next((p for p in all_procs if p.get('_id') == processo_pai_id), None)
                                
                                with container:
                                    with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                        if proc:
                                            title = proc.get('titulo') or proc.get('numero') or 'Sem título'
                                            number = proc.get('numero', '')
                                            display = f"{title}" + (f" ({number})" if number else "")
                                            with ui.badge(display).classes('pr-1').style('background-color: #FF9800; color: white;'):
                                                ui.button(
                                                    icon='close',
                                                    on_click=lambda: remove_parent_process(parent_process_chips)
                                                ).props('flat dense round size=xs color=white')
                            
                            def remove_parent_process(container):
                                state['processo_pai_id'] = ''
                                refresh_parent_chips(container, '')
                            
                            def add_parent_process(select, container):
                                val = select.value
                                if val and val != '— Nenhum (processo raiz) —' and val != '-':
                                    if ' | ' in val:
                                        process_id = val.split(' | ')[-1].strip()
                                        if process_id == state.get('process_id'):
                                            ui.notify('Um processo não pode ser vinculado a si mesmo!', type='warning')
                                            return
                                        state['processo_pai_id'] = process_id
                                        select.value = None
                                        refresh_parent_chips(container, process_id)
                            
                            # SEÇÃO 1 - Identificação do Processo
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('📋 Identificação do Processo').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-4'):
                                    with ui.row().classes('w-full gap-4 items-start'):
                                        title_input = ui.input(make_required_label('Título do Processo')).classes('flex-grow').props('outlined dense')
                                        number_input = ui.input(make_required_label('Número do Processo')).classes('w-48').props('outlined dense')
                                    
                                    with ui.row().classes('w-full gap-4 items-center'):
                                        link_input = ui.input('Link do Processo').classes('flex-grow').props('outlined dense')
                                        
                                        def open_link():
                                            link = link_input.value.strip()
                                            if link:
                                                if not link.startswith(('http://', 'https://')):
                                                    link = 'https://' + link
                                                ui.run_javascript(f'window.open("{link}", "_blank")')
                                        
                                        open_link_btn = ui.button('Abrir', icon='open_in_new', on_click=open_link).props('dense size=sm color=primary')
                                        
                                        def update_button_state():
                                            if link_input.value and link_input.value.strip():
                                                open_link_btn.props(remove='disabled')
                                            else:
                                                open_link_btn.props(add='disabled')
                                        
                                        link_input.on('input', update_button_state)
                                        update_button_state()
                                    
                                    type_select = ui.select(
                                        TIPOS_PROCESSO,
                                        label=make_required_label('Tipo de processo'),
                                        value=dados.get('tipo', 'Judicial')
                                    ).classes('w-full').props('outlined dense')
                                    
                                    # Data de Abertura
                                    with ui.row().classes('items-center gap-2'):
                                        data_abertura_input = ui.input(
                                            'Data de Abertura',
                                            placeholder='Ex: 2008, 09/2008, 05/09/2008',
                                            value=dados.get('data_abertura', '')
                                        ).classes('w-56').props('outlined dense')
                                        
                                        def validate_approximate_date(value: str) -> bool:
                                            if not value or value.strip() == '':
                                                return True
                                            value = value.strip()
                                            if len(value) == 4 and value.isdigit():
                                                return 1900 <= int(value) <= 2100
                                            if len(value) == 7 and '/' in value:
                                                parts = value.split('/')
                                                if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) == 4:
                                                    try:
                                                        return 1 <= int(parts[0]) <= 12 and 1900 <= int(parts[1]) <= 2100
                                                    except ValueError:
                                                        return False
                                            if len(value) == 10 and value.count('/') == 2:
                                                try:
                                                    datetime.strptime(value, '%d/%m/%Y')
                                                    return True
                                                except ValueError:
                                                    return False
                                            return False
                                        
                                        data_abertura_input.validation = {'Formato inválido': validate_approximate_date}
                                        
                                        # Menu popup para seleção de data
                                        with ui.menu().props('anchor="bottom left" self="top left"') as date_menu:
                                            with ui.card().classes('p-4 w-72'):
                                                ui.label('📅 Data Aproximada').classes('text-base font-bold mb-2')
                                                
                                                date_type_sel = ui.select(
                                                    options={
                                                        'full': '📆 Data completa',
                                                        'month_year': '📅 Mês e ano',
                                                        'year_only': '📋 Apenas ano'
                                                    },
                                                    value='full',
                                                    label='Precisão'
                                                ).classes('w-full mb-2').props('outlined dense')
                                                
                                                day_sel = ui.select(
                                                    options=[str(i).zfill(2) for i in range(1, 32)],
                                                    label='Dia',
                                                    value='01'
                                                ).classes('w-full mb-2').props('outlined dense')
                                                
                                                month_opts = {
                                                    '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março',
                                                    '04': 'Abril', '05': 'Maio', '06': 'Junho',
                                                    '07': 'Julho', '08': 'Agosto', '09': 'Setembro',
                                                    '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
                                                }
                                                month_sel = ui.select(
                                                    options=month_opts,
                                                    label='Mês',
                                                    value='01'
                                                ).classes('w-full mb-2').props('outlined dense')
                                                
                                                year_opts = [str(y) for y in range(datetime.now().year, 1949, -1)]
                                                year_sel = ui.select(
                                                    options=year_opts,
                                                    label='Ano',
                                                    value=str(datetime.now().year)
                                                ).classes('w-full mb-3').props('outlined dense')
                                                
                                                def on_type_change():
                                                    t = date_type_sel.value
                                                    day_sel.visible = (t == 'full')
                                                    month_sel.visible = (t in ['full', 'month_year'])
                                                
                                                date_type_sel.on_value_change(on_type_change)
                                                
                                                def apply_selected_date():
                                                    t = date_type_sel.value
                                                    if t == 'full':
                                                        data_abertura_input.value = f"{day_sel.value}/{month_sel.value}/{year_sel.value}"
                                                    elif t == 'month_year':
                                                        data_abertura_input.value = f"{month_sel.value}/{year_sel.value}"
                                                    else:
                                                        data_abertura_input.value = year_sel.value
                                                    date_menu.close()
                                                
                                                with ui.row().classes('w-full justify-end gap-2'):
                                                    ui.button('Cancelar', on_click=date_menu.close).props('flat dense')
                                                    ui.button('OK', on_click=apply_selected_date).props('color=primary dense')
                                        
                                        ui.button(icon='edit_calendar', on_click=date_menu.open).props('flat dense round').tooltip('Selecionar data aproximada')
                            
                            # SEÇÃO 2 - Partes Envolvidas
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('👥 Partes Envolvidas').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-4'):
                                    # Clientes
                                    client_options = [format_option_for_search(c) for c in todas_pessoas]
                                    with ui.row().classes('w-full gap-4'):
                                        with ui.column().classes('flex-1 gap-2'):
                                            with ui.row().classes('w-full gap-2 items-center'):
                                                client_sel = ui.select(
                                                    client_options or ['-'],
                                                    label=make_required_label('Clientes'),
                                                    with_input=True
                                                ).classes('flex-grow').props('dense outlined')
                                                ui.button(
                                                    icon='add',
                                                    on_click=lambda: add_item(client_sel, state['selected_clients'], client_chips, 'clients', todas_pessoas)
                                                ).props('flat dense').style('color: #4CAF50;')
                                            client_chips = ui.column().classes('w-full')
                                        
                                        # Parte Contrária
                                        opposing_options = [format_option_for_search(p) for p in todas_pessoas]
                                        with ui.column().classes('flex-1 gap-2'):
                                            with ui.row().classes('w-full gap-2 items-center'):
                                                opposing_sel = ui.select(
                                                    opposing_options or ['-'],
                                                    label='Parte Contrária',
                                                    with_input=True
                                                ).classes('flex-grow').props('dense outlined')
                                                ui.button(
                                                    icon='add',
                                                    on_click=lambda: add_item(opposing_sel, state['selected_opposing'], opposing_chips, 'opposing', todas_pessoas)
                                                ).props('flat dense').style('color: #F44336;')
                                            opposing_chips = ui.column().classes('w-full')
                                    
                                    # Outros Envolvidos
                                    with ui.column().classes('w-full gap-2'):
                                        with ui.row().classes('w-full gap-2 items-center'):
                                            others_sel = ui.select(
                                                opposing_options or ['-'],
                                                label='Outros Envolvidos',
                                                with_input=True
                                            ).classes('flex-grow').props('dense outlined')
                                            ui.button(
                                                icon='add',
                                                on_click=lambda: add_item(others_sel, state['selected_others'], others_chips, 'others', todas_pessoas)
                                            ).props('flat dense').style('color: #2196F3;')
                                        others_chips = ui.column().classes('w-full')
                            
                            # SEÇÃO 3 - Vínculos
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('🔗 Vínculos').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-2'):
                                    parent_process_chips = ui.column().classes('w-full')
                                    
                                    # Processo Pai (na Visão Geral suporta apenas um)
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        parent_process_sel = ui.select(
                                            options=['— Nenhum (processo raiz) —'],
                                            label='Processo Pai (opcional)',
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined use-input filter-input')
                                        ui.button(
                                            icon='add',
                                            on_click=lambda: add_parent_process(parent_process_sel, parent_process_chips)
                                        ).props('flat dense').style('color: #FF9800;')
                                    
                                    # Casos Vinculados
                                    case_options = [c.get('titulo', '') for c in todos_casos if c.get('titulo')]
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        cases_sel = ui.select(
                                            case_options or ['-'],
                                            label='Casos Vinculados',
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined')
                                        ui.button(
                                            icon='add',
                                            on_click=lambda: add_item(cases_sel, state['selected_cases'], cases_chips, 'cases', None)
                                        ).props('flat dense').style('color: #9C27B0;')
                                    cases_chips = ui.column().classes('w-full')
                            
                            # Renderizar chips iniciais será feito após definir todas as variáveis
                    
                    # ============================================================
                    # TAB 2: DADOS JURÍDICOS
                    # ============================================================
                    with ui.tab_panel(tab_legal):
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
                            
                            # Estado e Comarca (campos adicionais da Visão Geral)
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
                    
                    # ============================================================
                    # TAB 3: RELATÓRIO
                    # ============================================================
                    with ui.tab_panel(tab_relatory):
                        with ui.column().classes('w-full gap-5'):
                            ui.label('Resumo dos Fatos').classes('text-sm font-semibold text-gray-700')
                            relatory_facts_input = ui.editor(
                                value=dados.get('relatory_facts', '') if is_edicao else '',
                                placeholder='Descreva os principais fatos do processo...'
                            ).classes('w-full').style('height: 200px')
                            
                            ui.label('Histórico / Linha do Tempo').classes('text-sm font-semibold text-gray-700')
                            relatory_timeline_input = ui.editor(
                                value=dados.get('relatory_timeline', '') if is_edicao else '',
                                placeholder='Descreva a sequência cronológica dos eventos...'
                            ).classes('w-full').style('height: 200px')
                            
                            ui.label('Documentos Relevantes').classes('text-sm font-semibold text-gray-700')
                            relatory_documents_input = ui.editor(
                                value=dados.get('relatory_documents', '') if is_edicao else '',
                                placeholder='Liste os documentos importantes do processo...'
                            ).classes('w-full').style('height: 200px')
                    
                    # ============================================================
                    # TAB 4: ESTRATÉGIA
                    # ============================================================
                    with ui.tab_panel(tab_strategy):
                        with ui.column().classes('w-full gap-5'):
                            ui.label('Objetivos').classes('text-sm font-semibold text-gray-700')
                            objectives_input = ui.editor(
                                value=dados.get('strategy_objectives', '') if is_edicao else '',
                                placeholder='Descreva os objetivos...'
                            ).classes('w-full').style('height: 200px')
                            
                            ui.label('Teses a serem trabalhadas').classes('text-sm font-semibold text-gray-700')
                            thesis_input = ui.editor(
                                value=dados.get('legal_thesis', '') if is_edicao else '',
                                placeholder='Descreva as teses...'
                            ).classes('w-full').style('height: 200px')
                            
                            ui.label('Observações').classes('text-sm font-semibold text-gray-700')
                            observations_input = ui.editor(
                                value=(dados.get('strategy_observations', '') or dados.get('observacoes', '')) if is_edicao else '',
                                placeholder='Observações...'
                            ).classes('w-full').style('height: 200px')
                    
                    # ============================================================
                    # TAB 5: CENÁRIOS
                    # ============================================================
                    with ui.tab_panel(tab_scenarios):
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
                    
                    # ============================================================
                    # TAB 6: PROTOCOLOS
                    # ============================================================
                    with ui.tab_panel(tab_protocols):
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
            
            # Footer Actions
            with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10').style('background: rgba(249, 250, 251, 0.95); border-radius: 8px 0 0 0;'):
                
                def do_delete():
                    if state['is_editing'] and state.get('process_id'):
                        if excluir_processo(state['process_id']):
                            ui.notify(f'Processo excluído!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao excluir processo.', type='negative')
                    else:
                        ui.notify('Não foi possível identificar o processo para exclusão.', type='warning')
                
                delete_btn = ui.button('EXCLUIR', icon='delete', on_click=do_delete).props('color=red').classes('hidden font-bold shadow-lg' if not is_edicao else 'font-bold shadow-lg')
                
                def do_save():
                    # Coletar dados do formulário
                    selected_cases_ids = []
                    caso_titulo = ''
                    if state['selected_cases']:
                        # Buscar ID do caso pelo título
                        caso_obj = next((c for c in todos_casos if c.get('titulo') in state['selected_cases']), None)
                        if caso_obj:
                            selected_cases_ids = [caso_obj.get('_id')]
                            caso_titulo = caso_obj.get('titulo', '')
                    
                    processo_pai_id = state.get('processo_pai_id', '') or ''
                    processo_pai_titulo = ''
                    if processo_pai_id:
                        proc_obj = buscar_processo(processo_pai_id)
                        if proc_obj:
                            processo_pai_titulo = proc_obj.get('titulo', '')
                    
                    # Normalizar parte contrária
                    parte_contraria = ''
                    if isinstance(state['selected_opposing'], list):
                        parte_contraria = ', '.join(state['selected_opposing']) if state['selected_opposing'] else ''
                    else:
                        parte_contraria = str(state['selected_opposing']) if state['selected_opposing'] else ''
                    
                    novos_dados = {
                        'titulo': title_input.value.strip() if title_input.value else '',
                        'numero': number_input.value.strip() if number_input.value else '',
                        'tipo': type_select.value or 'Judicial',
                        'sistema_processual': system_select.value or '',
                        'area': area_select.value or '',
                        'estado': estado_select.value or '',
                        'comarca': comarca_input.value.strip() if comarca_input.value else '',
                        'vara': vara_input.value.strip() if vara_input.value else '',
                        'caso_id': selected_cases_ids[0] if selected_cases_ids else '',
                        'caso_titulo': caso_titulo,
                        'clientes': state['selected_clients'].copy(),
                        'clientes_nomes': [
                            get_display_name(next((p for p in todas_pessoas if get_display_name(p) == cid or p.get('_id') == cid), {}))
                            for cid in state['selected_clients']
                        ],
                        'parte_contraria': parte_contraria,
                        'processo_pai_id': processo_pai_id,
                        'processo_pai_titulo': processo_pai_titulo,
                        'status': status_select.value or 'Ativo',
                        'resultado': result_select.value if result_select.value and result_select.value != 'Pendente' else 'Pendente',
                        'data_abertura': data_abertura_input.value.strip() if data_abertura_input.value else '',
                        'observacoes': observations_input.value or '',
                        # Campos de cenários (adaptados para o modelo da Visão Geral)
                        # Se houver cenários na lista, extrai os textos
                        'cenario_melhor': '',
                        'cenario_intermediario': '',
                        'cenario_pior': '',
                        # Mantém também a lista de cenários para compatibilidade
                        'scenarios': state.get('scenarios', []),
                        # Campos de relatório (para compatibilidade futura)
                        'relatory_facts': relatory_facts_input.value or '',
                        'relatory_timeline': relatory_timeline_input.value or '',
                        'relatory_documents': relatory_documents_input.value or '',
                        # Campos de estratégia
                        'strategy_objectives': objectives_input.value or '',
                        'legal_thesis': thesis_input.value or '',
                        'strategy_observations': observations_input.value or '',
                        # Protocolos (armazenados como JSON)
                        'protocols': state.get('protocols', []),
                    }
                    
                    # Validação
                    valido, erro = validar_processo(novos_dados)
                    if not valido:
                        ui.notify(erro, type='negative')
                        return
                    
                    # Salvar
                    try:
                        if is_edicao:
                            sucesso = atualizar_processo(state['process_id'], novos_dados)
                            msg = 'Processo atualizado com sucesso!'
                        else:
                            processo_id = criar_processo(novos_dados)
                            sucesso = processo_id is not None
                            msg = 'Processo criado com sucesso!'
                        
                        if sucesso:
                            ui.notify(msg, type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao salvar processo.', type='negative')
                    except Exception as e:
                        print(f"Erro ao salvar processo: {e}")
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao salvar: {str(e)}', type='negative')
                
                ui.button('SALVAR', icon='save', on_click=do_save).props('color=primary').classes('font-bold shadow-lg')
    
    # Carregar dados iniciais APÓS sair do contexto do dialog (quando dialog for aberto)
    def load_initial_data_after_open():
        """Carrega dados iniciais após o dialog ser aberto."""
        if is_edicao:
            try:
                # Preencher campos básicos
                title_input.value = dados.get('titulo', '')
                number_input.value = dados.get('numero', '')
                link_input.value = dados.get('link', '')
                type_select.value = dados.get('tipo', 'Judicial')
                data_abertura_input.value = dados.get('data_abertura', '')
                system_select.value = dados.get('sistema_processual', '')
                area_select.value = dados.get('area', '')
                estado_select.value = dados.get('estado', 'Santa Catarina')
                comarca_input.value = dados.get('comarca', '')
                vara_input.value = dados.get('vara', '')
                status_select.value = dados.get('status', 'Ativo')
                result_select.value = dados.get('resultado', 'Pendente')
                
                # Carregar cenários
                if dados.get('scenarios') and isinstance(dados.get('scenarios'), list):
                    state['scenarios'] = dados.get('scenarios')
                else:
                    state['scenarios'] = []
                    if dados.get('cenario_melhor'):
                        state['scenarios'].append({'title': 'Melhor Cenário', 'type': '🟢 Positivo', 'obs': dados.get('cenario_melhor')})
                    if dados.get('cenario_intermediario'):
                        state['scenarios'].append({'title': 'Cenário Intermediário', 'type': '⚪ Neutro', 'obs': dados.get('cenario_intermediario')})
                    if dados.get('cenario_pior'):
                        state['scenarios'].append({'title': 'Pior Cenário', 'type': '🔴 Negativo', 'obs': dados.get('cenario_pior')})
                
                # Carregar protocolos
                if dados.get('protocols') and isinstance(dados.get('protocols'), list):
                    state['protocols'] = dados.get('protocols')
                
                # Renderizar chips após um pequeno delay para garantir que elementos existam
                def render_chips_delayed():
                    try:
                        refresh_chips(client_chips, state['selected_clients'], 'clients', todas_pessoas)
                        if isinstance(state['selected_opposing'], list):
                            refresh_chips(opposing_chips, state['selected_opposing'], 'opposing', todas_pessoas)
                        refresh_chips(others_chips, state['selected_others'], 'others', todas_pessoas)
                        refresh_chips(cases_chips, state['selected_cases'], 'cases', None)
                        if state.get('processo_pai_id'):
                            refresh_parent_chips(parent_process_chips, state['processo_pai_id'])
                        
                        # Atualizar renderizações
                        render_scenarios.refresh()
                        render_protocols.refresh()
                        toggle_result()
                    except Exception as e:
                        print(f"[DIALOG] Erro ao renderizar chips: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Usa timer para garantir que elementos estão no DOM
                ui.timer(0.1, render_chips_delayed, once=True)
                
            except Exception as e:
                print(f"[DIALOG] Erro ao carregar dados iniciais: {e}")
                import traceback
                traceback.print_exc()
        
        # Carregar opções de processos pais (sempre)
        try:
            all_procs = listar_processos_pais()
            parent_options = []
            current_id = state.get('process_id')
            
            for p in all_procs:
                proc_id = p.get('_id')
                if proc_id and proc_id != current_id:
                    title = p.get('titulo') or p.get('numero') or 'Sem título'
                    number = p.get('numero', '')
                    display = f"{title}" + (f" ({number})" if number else "") + f" | {proc_id}"
                    parent_options.append(display)
            
            parent_process_sel.options = parent_options if parent_options else ['— Nenhum (processo raiz) —']
        except Exception as e:
            print(f"[DIALOG] Erro ao carregar processos pais: {e}")
            parent_process_sel.options = ['— Nenhum (processo raiz) —']
    
    # Executa após dialog ser aberto usando timer
    ui.timer(0.2, load_initial_data_after_open, once=True)
    
    dialog.open()


def confirmar_exclusao(processo: dict, on_confirm: Optional[Callable] = None):
    """
    Dialog de confirmação de exclusão de processo.
    
    Args:
        processo: Dicionário com dados do processo a excluir
        on_confirm: Callback executado ao confirmar exclusão
    """
    titulo = processo.get('titulo', 'Processo')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('warning', color='negative', size='32px')
            ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800')
        
        ui.label(f'Deseja realmente excluir o processo "{titulo}"?').classes('text-gray-600 mb-2')
        ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')
            
            def executar_exclusao():
                dialog.close()
                if on_confirm:
                    on_confirm()
            
            ui.button('Excluir', on_click=executar_exclusao).props('color=negative')
    
    dialog.open()
