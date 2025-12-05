"""
Módulo principal de páginas para o módulo de Casos.

Contém as três páginas NiceGUI principais:
- casos(): Lista de casos (/casos)
- case_detail(): Detalhes do caso (/casos/{case_slug})
- case_swot(): Matriz SWOT (/casos/{case_slug}/matriz-swot)
"""

from datetime import datetime
from nicegui import ui
import asyncio

# Imports do core
from ...core import (
    layout, PRIMARY_COLOR, slugify, save_data, sync_processes_cases,
    get_cases_list, get_clients_list, get_processes_list, get_opposing_parties_list, format_date_br,
    get_processes_by_case, save_process as save_process_core, delete_process as delete_process_core, get_db,
    get_client_options_for_select, get_client_id_by_name, get_client_name_by_id,
    extract_client_name_from_formatted_option, format_client_option_for_select,
    save_case as save_case_core
)
from ...auth import is_authenticated

# Imports dos módulos locais
from .models import (
    STATE_OPTIONS, STATE_FLAG_URLS,
    CASE_TYPE_OPTIONS, CASE_TYPE_EMOJIS, CASE_TYPE_PREFIX,
    CASE_CATEGORY_OPTIONS,
    MONTH_OPTIONS, YEAR_OPTIONS,
    STATUS_OPTIONS, PARTE_CONTRARIA_OPTIONS,
    filter_state
)

from .business_logic import (
    get_case_type,
    get_case_sort_key,
    get_cases_by_type,
    calculate_case_number,
    generate_case_title,
    get_filtered_cases,
    create_new_case_dict
)

from .database import (
    remove_case,
    renumber_cases_of_type,
    renumber_all_cases,
    save_case,
    save_process
)

from .utils import (
    get_short_name_helper,
    get_state_flag_html,
    format_option_for_search,
    get_option_value,
    export_cases_to_pdf
)

from .ui_components import (
    create_rich_text_editor,
    render_cases_list,
    case_view_toggle,
    CASE_CARD_CSS
)
from .business_logic import deduplicate_cases_by_title

# Importar componentes padrão de processos
from ..processos.ui_components import BODY_SLOT_AREA, BODY_SLOT_STATUS, TABELA_PROCESSOS_CSS
# Importar modal de edição de processos
from ..processos.modais.modal_processo import render_process_dialog

# --- NEW IMPORT ---
# Import this module to ensure the @ui.page('/casos/admin/duplicatas') route is registered
from .casos_duplicatas_admin import casos_duplicatas_admin


@ui.page('/casos')
def casos():
    """Página principal de listagem de casos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # ==========================================================================
    # OTIMIZAÇÃO: Carrega todos os dados UMA ÚNICA VEZ no início
    # ==========================================================================
    _cases = deduplicate_cases_by_title(get_cases_list())
    _clients = get_clients_list()
    _opposing = get_opposing_parties_list()
    
    # Função auxiliar para obter sigla/apelido
    def get_short_name(full_name: str, source_list: list) -> str:
        return get_short_name_helper(full_name, source_list)
    
    # Resetar filtros ao entrar na página
    filter_state['search'] = ''
    filter_state['status'] = None
    filter_state['client'] = None
    filter_state['state'] = None
    filter_state['category'] = None
    filter_state['case_type'] = 'old'
    
    # REMOVIDO: renumber_all_cases() chamado automaticamente
    # Isso estava causando salvamentos desnecessários e possíveis duplicatas
    # A renumeração agora só acontece quando:
    # 1. Um novo caso é criado
    # 2. Um caso é editado (tipo, ano, mês mudam)
    # 3. Explicitamente chamado pelo usuário

    with layout('Casos', breadcrumbs=[('Casos', None)]):
        # --- New Case Dialog ---
        with ui.dialog() as new_case_dialog, ui.card().classes('w-full max-w-lg p-6'):
            ui.label('Novo Caso').classes('text-xl font-bold mb-4 text-primary')
            
            # Form Fields
            case_name = ui.input('Nome do Caso').classes('w-full mb-2')
            
            # Ano e Mês do caso
            with ui.row().classes('w-full gap-2 mb-2'):
                case_year = ui.select(
                    options=YEAR_OPTIONS,
                    label='Ano',
                    value=datetime.now().year,
                    with_input=True
                ).classes('flex-1')
                
                case_month = ui.select(
                    options={m['value']: m['label'] for m in MONTH_OPTIONS},
                    label='Mês',
                    value=datetime.now().month
                ).classes('flex-1')
            
            # Tipo do caso
            case_type_select = ui.select(
                options=CASE_TYPE_OPTIONS,
                label='Tipo de caso',
                value='Antigo'
            ).classes('w-full mb-2')
            
            # Categoria do caso
            case_category_select = ui.select(
                options=CASE_CATEGORY_OPTIONS,
                label='Categoria',
                value='Contencioso',
                with_input=True
            ).classes('w-full mb-2')
            
            status = ui.select(options=STATUS_OPTIONS, label='Status', value='Em andamento').classes('w-full mb-2')
            
            # Estado (UF)
            case_state = ui.select(
                options=[None] + STATE_OPTIONS, 
                label='Estado (UF)', 
                value=None,
                with_input=True
            ).classes('w-full mb-2').props('clearable')
            
            # Parte Contrária
            case_parte_contraria = ui.select(
                options=PARTE_CONTRARIA_OPTIONS,
                label='Parte Contrária',
                value='-',
                with_input=True
            ).classes('w-full mb-2').props('clearable')
            
            # Multi-client selection
            selected_clients = []
            all_clients_selected = {'value': False}
            client_options = [format_option_for_search(c) for c in _clients]
            
            ui.label('Clientes').classes('text-sm text-gray-600 mt-2 mb-1')
            
            with ui.row().classes('w-full gap-2 mb-2'):
                client_select = ui.select(
                    options=client_options, 
                    label='Selecione cliente(s)',
                    with_input=True
                ).classes('flex-grow')
                
                def add_client():
                    if client_select.value:
                        full_name = get_option_value(client_select.value, _clients)
                        if full_name not in selected_clients:
                            selected_clients.append(full_name)
                            client_select.value = None
                            all_clients_selected['value'] = False
                            all_clients_checkbox.value = False
                            client_chips_container.refresh()
                        else:
                            ui.notify('Cliente já adicionado!', type='warning')
                
                ui.button(icon='add', on_click=add_client).props('flat color=primary').classes('mt-4')
            
            def handle_all_clients(checked):
                all_clients_selected['value'] = checked
                if checked:
                    selected_clients.clear()
                    for client in _clients:
                        full_name = client.get('name') or client.get('full_name', '')
                        if full_name and full_name not in selected_clients:
                            selected_clients.append(full_name)
                    ui.notify(f'✅ Todos os clientes adicionados! ({len(selected_clients)})', type='positive')
                else:
                    selected_clients.clear()
                    ui.notify('❌ Clientes removidos!', type='info')
                client_chips_container.refresh()
            
            all_clients_checkbox = ui.checkbox(
                text=f'Todos os Clientes ({len(_clients)})',
                on_change=lambda e: handle_all_clients(e.value)
            ).classes('mt-2').style('font-size: 14px; font-weight: 500;')
            
            @ui.refreshable
            def client_chips_container():
                if all_clients_selected['value'] and selected_clients:
                    with ui.card().classes('px-4 py-2 flex items-center gap-2 mb-2').style(
                        f'background-color: {PRIMARY_COLOR}; color: white; border-radius: 16px; font-weight: bold;'
                    ):
                        ui.icon('check_circle', size='sm').classes('text-white')
                        ui.label(f'Todos os Clientes ({len(selected_clients)})').classes('text-sm')
                elif selected_clients:
                    with ui.row().classes('w-full gap-2 flex-wrap'):
                        for client_name in selected_clients:
                            short_name = get_short_name(client_name, _clients)
                            with ui.card().classes('px-3 py-1 flex items-center gap-2').style(
                                f'background-color: {PRIMARY_COLOR}; color: white; border-radius: 16px;'
                            ):
                                ui.label(short_name).classes('text-sm')
                                
                                def remove_client(name=client_name):
                                    selected_clients.remove(name)
                                    all_clients_selected['value'] = False
                                    all_clients_checkbox.value = False
                                    client_chips_container.refresh()
                                
                                ui.button(icon='close', on_click=remove_client).props(
                                    'flat dense round size=xs color=white'
                                ).classes('ml-1')
                else:
                    ui.label('Nenhum cliente selecionado').classes('text-sm text-gray-400 italic')
            
            client_chips_container()
            
            ui.space().classes('mb-4')
            
            def save_new_case():
                if not case_name.value or not case_year.value:
                    ui.notify('Nome e Ano são obrigatórios!', type='warning')
                    return
                
                new_case = create_new_case_dict(
                    case_name=case_name.value,
                    year=int(case_year.value),
                    month=case_month.value or 1,
                    case_type=case_type_select.value,
                    category=case_category_select.value,
                    status=status.value,
                    state=case_state.value,
                    parte_contraria=case_parte_contraria.value,
                    parte_contraria_options=PARTE_CONTRARIA_OPTIONS,
                    selected_clients=selected_clients
                )
                
                # Garantir ordem cronológica: renumera antes e, para "Novo", logo após salvar
                renumber_cases_of_type(case_type_select.value, force=True)
                save_case(new_case)
                if case_type_select.value == 'Novo':
                    renumber_cases_of_type('Novo', force=True)
                save_data()
                ui.notify('Caso criado com sucesso!')
                render_cases_list.refresh()
                new_case_dialog.close()
                
                # Reset fields
                case_name.value = ''
                case_year.value = datetime.now().year
                case_month.value = datetime.now().month
                case_type_select.value = 'Antigo'
                case_category_select.value = 'Contencioso'
                status.value = 'Em andamento'
                case_state.value = None
                selected_clients.clear()
                client_chips_container.refresh()

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=new_case_dialog.close).props('flat color=grey')
                ui.button('Salvar', on_click=save_new_case).classes('bg-primary text-white')

        # Main Content
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('Visão Geral').classes('text-lg text-gray-500')
            with ui.row().classes('gap-2'):
                def do_export_pdf():
                    export_cases_to_pdf(
                        get_cases_list_func=get_cases_list,
                        get_case_sort_key_func=get_case_sort_key,
                        get_case_type_func=get_case_type,
                        primary_color=PRIMARY_COLOR
                    )
                ui.button(icon='picture_as_pdf', on_click=do_export_pdf).props('flat dense').classes('text-gray-600').tooltip('Exportar PDF')
                ui.button('Novo Caso', icon='add', on_click=new_case_dialog.open).classes('bg-primary text-white shadow-md')

        # Toggle de visualização
        case_view_toggle()

        # Filtros
        with ui.card().classes('w-full p-4 mb-4 bg-gray-50'):
            with ui.row().classes('w-full gap-4 items-end flex-wrap'):
                def on_search_change(e):
                    filter_state['search'] = e.value if e.value else ''
                    render_cases_list.refresh()
                
                ui.input(
                    'Buscar caso...',
                    on_change=on_search_change
                ).props('outlined dense clearable').classes('flex-grow min-w-[200px]').style('max-width: 400px')
                
                def on_status_change(e):
                    filter_state['status'] = e.value if e.value else None
                    render_cases_list.refresh()
                
                ui.select(
                    options=[None] + STATUS_OPTIONS,
                    label='Status',
                    value=None,
                    on_change=on_status_change
                ).props('outlined dense clearable').classes('min-w-[180px]').bind_value_to(filter_state, 'status')
                
                all_clients = [c['name'] for c in _clients]
                
                def on_client_change(e):
                    filter_state['client'] = e.value if e.value else None
                    render_cases_list.refresh()
                
                ui.select(
                    options=[None] + all_clients,
                    label='Cliente',
                    value=None,
                    on_change=on_client_change,
                    with_input=True
                ).props('outlined dense clearable').classes('min-w-[200px]').bind_value_to(filter_state, 'client')
                
                def on_state_change(e):
                    filter_state['state'] = e.value if e.value else None
                    render_cases_list.refresh()
                
                ui.select(
                    options=[None] + STATE_OPTIONS,
                    label='Estado (UF)',
                    value=None,
                    on_change=on_state_change,
                    with_input=True
                ).props('outlined dense clearable').classes('min-w-[150px]').bind_value_to(filter_state, 'state')
                
                def on_category_filter_change(e):
                    filter_state['category'] = e.value if e.value else None
                    render_cases_list.refresh()
                
                ui.select(
                    options=[None] + CASE_CATEGORY_OPTIONS,
                    label='Categoria',
                    value=None,
                    on_change=on_category_filter_change,
                    with_input=True
                ).props('outlined dense clearable').classes('min-w-[150px]').bind_value_to(filter_state, 'category')
                
                def clear_filters():
                    filter_state['search'] = ''
                    filter_state['status'] = None
                    filter_state['client'] = None
                    filter_state['state'] = None
                    filter_state['category'] = None
                    render_cases_list.refresh()
                
                ui.button('Limpar', icon='clear', on_click=clear_filters).props('flat color=grey').classes('ml-auto')

        # Grid de cards
        render_cases_list()

@ui.page('/casos/{case_slug}')
def case_detail(case_slug: str):
    # ==========================================================================
    # OTIMIZAÇÃO: Carrega dados UMA ÚNICA VEZ no início da página
    # ==========================================================================
    _clients = get_clients_list()
    _opposing = get_opposing_parties_list()
    
    # Funções auxiliares para obter sigla/apelido
    def get_short_name(full_name: str, source_list: list) -> str:
        """Retorna sigla/apelido ou primeiro nome"""
        for item in source_list:
            if item.get('name') == full_name:
                # Prioridade: nickname > alias > primeiro nome
                if item.get('nickname'):
                    return item['nickname']
                if item.get('alias'):
                    return item['alias']
                # Se não tem apelido, retorna primeiro nome
                return full_name.split()[0] if full_name else full_name
        # Se não encontrou na lista, retorna primeiro nome
        return full_name.split()[0] if full_name else full_name
    
    def format_option_for_search(item: dict) -> str:
        """Formata opção para busca: inclui nome e sigla/apelido"""
        name = item.get('name', '')
        nickname = item.get('nickname', '')
        if nickname and nickname != name:
            return f"{name} ({nickname})"
        return name
    
    def get_option_value(formatted_option: str, source_list: list) -> str:
        """Extrai o nome completo de uma opção formatada"""
        # Remove a parte entre parênteses se existir
        if '(' in formatted_option:
            return formatted_option.split(' (')[0]
        return formatted_option
    
    case = next((c for c in get_cases_list() if c.get('slug') == case_slug), None)
    if not case:
        ui.label('Caso não encontrado.').classes('text-xl text-red-500 p-8')
        return

    # Sistema de salvamento automático com debounce
    import asyncio
    autosave_state = {'timer': None, 'is_saving': False, 'refresh_callbacks': []}
    
    def register_autosave_refresh(callback):
        """Registra um callback para ser chamado quando o estado de salvamento mudar"""
        autosave_state['refresh_callbacks'].append(callback)
    
    def refresh_all_indicators():
        """Atualiza todos os indicadores de salvamento registrados"""
        for callback in autosave_state['refresh_callbacks']:
            try:
                callback.refresh()
            except:
                pass
    
    async def autosave_with_debounce(delay: float = 2.0):
        """Salva após um delay, cancelando salvamentos anteriores pendentes."""
        if autosave_state['timer']:
            autosave_state['timer'].cancel()
        
        async def delayed_save():
            await asyncio.sleep(delay)
            autosave_state['is_saving'] = True
            save_indicator.refresh()
            refresh_all_indicators()
            
            # Pequeno delay para mostrar o indicador
            await asyncio.sleep(0.3)
            
            # Salva o caso no Firestore
            try:
                from ...core import save_case
                save_case(case)
            except Exception as e:
                print(f'Erro no auto-save: {e}')
            
            save_data()  # Mantém para compatibilidade
            render_cases_list.refresh()
            
            autosave_state['is_saving'] = False
            save_indicator.refresh()
            refresh_all_indicators()
        
        autosave_state['timer'] = asyncio.create_task(delayed_save())
    
    def trigger_autosave():
        """Dispara o salvamento automático."""
        asyncio.create_task(autosave_with_debounce())

    # CSS customizado para tabela de processos
    ui.add_css('''
        .processes-table {
            width: 100% !important;
        }
        .processes-table th, .processes-table td {
            padding: 10px 12px !important;
            font-size: 13px !important;
        }
        .processes-table th {
            font-size: 12px !important;
            font-weight: 600 !important;
            background-color: #f9fafb !important;
        }
        .processes-table tbody tr:nth-child(odd) {
            background-color: #ffffff !important;
        }
        .processes-table tbody tr:nth-child(even) {
            background-color: #e5e7eb !important; /* cinza mais forte para telas de baixa qualidade */
        }
        .processes-table tbody tr {
            border-bottom: 1px solid #111827 !important; /* linhas escuras entre processos */
        }
        .processes-table tbody tr:hover {
            background-color: #f3f4f6 !important;
        }
    ''')

    with layout(f'Caso: {case["title"]}', breadcrumbs=[('Casos', '/casos'), (case['title'], None)]):
        # Indicador de salvamento automático
        @ui.refreshable
        def save_indicator():
            with ui.row().classes('fixed top-4 right-4 z-50'):
                if autosave_state['is_saving']:
                    with ui.card().classes('px-4 py-2 bg-yellow-100 border border-yellow-400 rounded-lg shadow-lg flex items-center gap-2'):
                        ui.spinner('dots', size='sm').classes('text-yellow-600')
                        ui.label('Salvando...').classes('text-yellow-700 text-sm font-medium')
        
        save_indicator()
        
        with ui.dialog() as delete_case_dialog, ui.card().classes('w-full max-w-md p-6'):
            ui.label('Excluir caso').classes('text-xl font-bold mb-3 text-primary')
            ui.label(f'Confirmar exclusão de "{case["title"]}"?').classes('text-sm text-gray-600 mb-4')
            ui.label('Esta ação é permanente.').classes('text-xs text-red-500 mb-4')

            def confirm_delete_current_case(target_case=case):
                if remove_case(target_case):
                    ui.notify('Caso removido!')
                    delete_case_dialog.close()
                    ui.navigate.to('/casos')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=delete_case_dialog.close).props('flat color=grey')
                ui.button('Excluir', on_click=confirm_delete_current_case).classes('bg-red-600 text-white')

        # HEADER: Botão Excluir (título já está no breadcrumb)
        with ui.row().classes('w-full justify-end items-center mb-6'):
            ui.button('🗑️ Excluir Caso', on_click=delete_case_dialog.open).classes('bg-red-600 text-white').props('dense')

        with ui.tabs().classes('w-full bg-white').props('align=left no-caps') as tabs:
            basic_tab = ui.tab('Dados básicos')
            proc_tab = ui.tab('Processos')
            calc_tab = ui.tab('Cálculos')
            report_tab = ui.tab('Relatório geral do caso')
            vistorias_tab = ui.tab('Vistorias')
            strategy_tab = ui.tab('Estratégia geral')
            next_actions_tab = ui.tab('Próximas ações')
            slack_tab = ui.tab('Slack')
            links_tab = ui.tab('Links úteis')
        
        with ui.tab_panels(tabs, value=basic_tab).classes('w-full p-6 bg-white rounded shadow-sm'):
            # Tab 1: Dados básicos
            with ui.tab_panel(basic_tab).classes('w-full'):
                # ========== DADOS BÁSICOS CLEAN ==========
                
                # Campo oculto para atualizar o título automaticamente
                title_display = ui.input(value=case['title']).classes('hidden')
                
                # Função para renumerar e atualizar título
                def update_case_numbering():
                    old_type = get_case_type(case)
                    new_type = edit_case_type.value
                    
                    # Se mudou de tipo, renumerar ambos os tipos
                    if old_type != new_type:
                        renumber_cases_of_type(old_type)
                    renumber_cases_of_type(new_type)
                    
                    # Atualizar exibição do título
                    title_display.value = case.get('title', '')
                    trigger_autosave()  # Salva no Firebase
                
                # Ano e Mês do caso
                def on_year_change(e):
                    case['year'] = str(e.value) if e.value else case.get('year')
                    update_case_numbering()
                
                def on_month_change(e):
                    case['month'] = e.value
                    update_case_numbering()
                
                # Converter ano para inteiro se for string
                current_year_value = case.get('year')
                if isinstance(current_year_value, str) and current_year_value.isdigit():
                    current_year_value = int(current_year_value)
                
                # ========== LINHA 1: Ano + Mês + Status + Tipo ==========
                with ui.row().style('gap: 40px; width: 100%; margin-bottom: 24px;'):
                    with ui.column().style('min-width: 100px;'):
                        ui.label('ANO').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        edit_year = ui.select(
                            options=YEAR_OPTIONS,
                            value=current_year_value,
                            with_input=True,
                            on_change=on_year_change
                        ).classes('w-full').props('dense outlined')
                    
                    with ui.column().style('min-width: 140px;'):
                        ui.label('MÊS').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        edit_month = ui.select(
                            options={m['value']: m['label'] for m in MONTH_OPTIONS},
                            value=case.get('month'),
                            on_change=on_month_change
                        ).classes('w-full').props('dense outlined')
                    
                    with ui.column().style('min-width: 180px;'):
                        ui.label('STATUS').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        
                        def on_status_change(e):
                            case['status'] = e.value
                            trigger_autosave()
                        
                        status_options = ['Em andamento', 'Concluído', 'Concluído com pendências', 'Em monitoramento']
                        edit_status = ui.select(
                            status_options, 
                            value=case.get('status'),
                            on_change=on_status_change
                        ).classes('w-full').props('dense outlined')
                    
                    with ui.column().style('min-width: 120px;'):
                        ui.label('TIPO').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        
                        def on_case_type_change(e):
                            old_type = get_case_type(case)
                            case['case_type'] = e.value
                            case['is_new_case'] = e.value == 'Novo'
                            # Renumerar tipo antigo e novo
                            renumber_cases_of_type(old_type)
                            renumber_cases_of_type(e.value)
                            # Atualizar exibição do título
                            title_display.value = case.get('title', '')
                            trigger_autosave()  # Salva no Firebase
                        
                        initial_case_type = get_case_type(case)
                        edit_case_type = ui.select(
                            CASE_TYPE_OPTIONS,
                            value=initial_case_type,
                            on_change=on_case_type_change
                        ).classes('w-full').props('dense outlined')
                
                # ========== LINHA 2: Categoria + Estado + Parte Contrária ==========
                with ui.row().style('gap: 40px; width: 100%; margin-bottom: 24px;'):
                    with ui.column().style('min-width: 140px;'):
                        ui.label('CATEGORIA').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        
                        def on_category_change(e):
                            case['category'] = e.value
                            trigger_autosave()
                        
                        # Categoria do caso: Contencioso ou Consultivo
                        initial_category = case.get('category')
                        if not initial_category:
                            initial_category = 'Contencioso'
                            case['category'] = 'Contencioso'
                        
                        edit_category = ui.select(
                            CASE_CATEGORY_OPTIONS,
                            value=initial_category,
                            with_input=True,
                            on_change=on_category_change
                        ).classes('w-full').props('dense outlined')
                    
                    with ui.column().style('min-width: 180px;'):
                        ui.label('ESTADO').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        
                        def on_state_edit_change(e):
                            case['state'] = e.value
                            trigger_autosave()
                        
                        edit_state = ui.select(
                            options=[None] + STATE_OPTIONS, 
                            value=case.get('state'),
                            with_input=True,
                            on_change=on_state_edit_change
                        ).classes('w-full').props('dense outlined clearable')
                    
                    with ui.column().style('min-width: 200px;'):
                        ui.label('PARTE CONTRÁRIA').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 6px;')
                        
                        def on_parte_contraria_change(e):
                            parte_contraria_options_dict = {
                                'MP': 'Ministério Público',
                                'OAB': 'OAB',
                                'Defesa': 'Defesa/Réu',
                                'Autor': 'Autor/Demandante',
                                'União': 'União',
                                'Estado': 'Estado',
                                'Município': 'Município',
                                'INSS': 'INSS',
                                'Receita Federal': 'Receita Federal',
                                'Outro': 'Outro',
                                '-': 'Não especificado'
                            }
                            case['parte_contraria'] = e.value or '-'
                            case['parte_contraria_nome'] = parte_contraria_options_dict.get(e.value or '-', '')
                            trigger_autosave()
                        
                        parte_contraria_options = {
                            'MP': 'Ministério Público',
                            'OAB': 'OAB',
                            'Defesa': 'Defesa/Réu',
                            'Autor': 'Autor/Demandante',
                            'União': 'União',
                            'Estado': 'Estado',
                            'Município': 'Município',
                            'INSS': 'INSS',
                            'Receita Federal': 'Receita Federal',
                            'Outro': 'Outro',
                            '-': 'Não especificado'
                        }
                        
                        edit_parte_contraria = ui.select(
                            options=parte_contraria_options,
                            value=case.get('parte_contraria', '-'),
                            with_input=True,
                            on_change=on_parte_contraria_change
                        ).classes('w-full').props('dense outlined clearable')
                
                # ========== SEPARADOR ==========
                ui.separator().style('margin: 20px 0;')
                
                # ========== CLIENTES (clean e compacto) ==========
                # Multi-client editing
                if 'clients' not in case and 'client' in case:
                    case['clients'] = [case['client']] if case.get('client') else []
                elif 'clients' not in case:
                    case['clients'] = []
                
                case_clients = case.get('clients', []).copy()
                edit_all_clients_selected = {'value': False}  # Estado do checkbox "Todos os Clientes"
                client_options = [format_option_for_search(c) for c in _clients]
                
                ui.label('CLIENTES').style('font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 8px;')
                
                # Seletor de cliente compacto
                with ui.row().style('gap: 8px; width: 100%; align-items: center; margin-bottom: 12px;'):
                    edit_client_select = ui.select(
                        options=client_options, 
                        label='Adicionar cliente',
                        with_input=True
                    ).props('dense outlined').style('max-width: 300px;')
                    
                    def add_case_client():
                        if edit_client_select.value:
                            # Extrair nome completo da opção formatada
                            full_name = get_option_value(edit_client_select.value, _clients)
                            if full_name not in case_clients:
                                case_clients.append(full_name)
                                case['clients'] = case_clients.copy()
                                edit_client_select.value = None
                                edit_all_clients_selected['value'] = False
                                edit_all_clients_checkbox.value = False
                                case_client_chips.refresh()
                                trigger_autosave()
                            else:
                                ui.notify('Cliente já adicionado!', type='warning')
                    
                    ui.button(icon='add', on_click=add_case_client).props('flat dense color=primary')
                    
                    # Checkbox "Todos os Clientes" inline
                    def handle_edit_all_clients(checked):
                        """Vincula ou desvincula todos os clientes"""
                        edit_all_clients_selected['value'] = checked
                        if checked:
                            # Adicionar todos os clientes
                            case_clients.clear()
                            for client in _clients:
                                full_name = client.get('name') or client.get('full_name', '')
                                if full_name and full_name not in case_clients:
                                    case_clients.append(full_name)
                            case['clients'] = case_clients.copy()
                            total = len(case_clients)
                            ui.notify(f'✅ Todos os clientes foram adicionados! ({total})', type='positive')
                        else:
                            # Remover todos os clientes
                            case_clients.clear()
                            case['clients'] = []
                            ui.notify('❌ Todos os clientes foram removidos!', type='info')
                        case_client_chips.refresh()
                        trigger_autosave()
                    
                    # Verifica se todos os clientes estão selecionados ao abrir
                    all_client_names = [c.get('name') or c.get('full_name', '') for c in _clients if c.get('name') or c.get('full_name', '')]
                    if set(case_clients) == set(all_client_names) and len(case_clients) > 0:
                        edit_all_clients_selected['value'] = True
                    
                    edit_all_clients_checkbox = ui.checkbox(
                        text=f'Todos ({len(_clients)})',
                        value=edit_all_clients_selected['value'],
                        on_change=lambda e: handle_edit_all_clients(e.value)
                    ).style('font-size: 13px;')
                
                @ui.refreshable
                def case_client_chips():
                    if edit_all_clients_selected['value'] and case_clients:
                        # Mostra texto especial quando "Todos os Clientes" está marcado
                        ui.label(f'🌐 Interesse de Todos os Clientes ({len(case_clients)})').style(
                            'color: #0c5460; font-size: 14px; font-weight: 500; margin-top: 4px;'
                        )
                    elif case_clients:
                        # Exibe nomes dos clientes em texto corrido, separados por vírgula
                        clientes_nomes = [get_short_name(name, _clients) for name in case_clients]
                        clientes_texto = ', '.join(clientes_nomes)
                        
                        with ui.row().style('gap: 4px; align-items: center; flex-wrap: wrap; margin-top: 4px;'):
                            ui.label(clientes_texto).style('color: #333; font-size: 14px; font-weight: 500;')
                    else:
                        ui.label('-').style('color: #ccc; font-size: 14px; margin-top: 4px;')
                
                case_client_chips()


            # Tab 2: Processos
            with ui.tab_panel(proc_tab).classes('w-full'):
                # CSS padrão para tabelas de processos (cores alternadas)
                ui.add_head_html(TABELA_PROCESSOS_CSS)
                
                # ===== CONSTANTES E HELPERS PARA ÁREA DO DIREITO (APENAS NA ABA PROCESSOS) =====
                # Opções padronizadas de área do direito
                PROCESS_AREA_OPTIONS = ['Administrativo', 'Criminal', 'Civil', 'Tributário', 'Técnicos/projetos']
                
                # Mapeamento de área → cor (hex)
                PROCESS_AREA_COLORS = {
                    'Administrativo': '#6b7280',      # gray
                    'Criminal': '#dc2626',            # red
                    'Civil': '#2563eb',               # blue
                    'Tributário': '#7c3aed',           # purple
                    'Técnicos/projetos': '#22c55e'     # light green
                }
                
                # Mapeamento para normalizar valores antigos
                AREA_NORMALIZATION_MAP = {
                    'Ambiental': 'Administrativo',
                    'Cível': 'Civil',
                    'Penal': 'Criminal',
                    'Trabalhista': 'Administrativo',
                    'Empresarial': 'Civil',
                    'Consumidor': 'Civil',
                    'Outro': 'Administrativo',
                    'Técnico/projetos': 'Técnicos/projetos',
                    'Técnicos/projetos': 'Técnicos/projetos',
                }
                
                def normalize_process_area(area: str) -> str:
                    """Normaliza área antiga para valor canônico"""
                    if not area or area == '-':
                        return 'Administrativo'  # padrão
                    area = area.strip()
                    # Verifica se já é um valor canônico
                    if area in PROCESS_AREA_OPTIONS:
                        return area
                    # Tenta normalizar
                    normalized = AREA_NORMALIZATION_MAP.get(area, 'Administrativo')
                    return normalized
                
                def get_process_area_style(area: str) -> str:
                    """Retorna estilo CSS para badge de área"""
                    normalized_area = normalize_process_area(area)
                    color = PROCESS_AREA_COLORS.get(normalized_area, '#6b7280')
                    return f'background-color: {color}; color: white;'
                
                # Funções auxiliares para formatação (padronizadas como na página de processos)
                def _get_priority_name(name: str, people_list: list) -> str:
                    """Busca pessoa na lista e retorna nome com prioridade: sigla > display_name > full_name. Sempre em MAIÚSCULAS."""
                    if not name:
                        return ''
                    person = None
                    for p in people_list:
                        full_name = p.get('full_name') or p.get('name', '')
                        if full_name == name or p.get('_id') == name:
                            person = p
                            break
                    if person:
                        if person.get('nickname'):
                            return person['nickname'].upper()
                        if person.get('display_name'):
                            return person['display_name'].upper()
                        return (person.get('full_name') or person.get('name', '')).upper()
                    return name.upper() if name else ''
                
                def _format_names_list(names_raw, people_list: list) -> list:
                    """Formata lista de nomes aplicando prioridade e MAIÚSCULAS. Retorna lista para exibição vertical."""
                    if not names_raw:
                        return []
                    if isinstance(names_raw, list):
                        formatted = [_get_priority_name(str(n), people_list) for n in names_raw if n]
                        return formatted
                    else:
                        name = _get_priority_name(str(names_raw), people_list)
                        return [name] if name else []
                
                # Container para a tabela de processos
                processes_container = ui.column().classes('w-full')
                
                # Criar instância do modal de edição de processos
                def on_process_saved():
                    """Callback quando processo é salvo - atualiza a lista"""
                    render_linked_processes.refresh()
                
                process_dialog, open_process_modal = render_process_dialog(
                    on_success=on_process_saved
                )
                
                # Definir render_linked_processes ANTES de ser referenciado
                @ui.refreshable
                def render_linked_processes():
                    """Renderiza a tabela de processos vinculados usando estrutura padrão sincronizada"""
                    processes_container.clear()
                    
                    try:
                        # Busca processos diretamente do Firestore (sem cache)
                        case_slug = case.get('slug')
                        linked_processes = get_processes_by_case(case_slug=case_slug, case_title=case.get('title'))
                        
                        # Carrega listas de pessoas para formatação
                        all_people = _clients + _opposing
                        
                        with processes_container:
                            if not linked_processes:
                                with ui.card().classes('w-full p-8 flex justify-center items-center bg-gray-50'):
                                    ui.label('Nenhum processo vinculado a este caso.').classes('text-gray-400 italic')
                            else:
                                # Preparar dados para a tabela (formato padrão)
                                table_rows = []
                                for proc in linked_processes:
                                    # Formata clientes (prioridade + MAIÚSCULAS) - retorna lista
                                    clients_raw = proc.get('clients') or proc.get('client') or []
                                    clients_list = _format_names_list(clients_raw, all_people)
                                    
                                    # Formata partes contrárias (prioridade + MAIÚSCULAS) - retorna lista
                                    opposing_raw = proc.get('opposing_parties') or []
                                    # Se não tiver no processo, usa do caso
                                    if not opposing_raw:
                                        case_opposing = case.get('parte_contraria', '')
                                        if case_opposing and case_opposing != '-':
                                            opposing_raw = [case_opposing]
                                    opposing_list = _format_names_list(opposing_raw, all_people)
                                    
                                    # Extrai casos vinculados - retorna lista (sempre o caso atual)
                                    cases_list = [case.get('title', '')] if case.get('title') else []
                                    
                                    table_rows.append({
                                        '_id': proc.get('_id', ''),
                                        'title': proc.get('title') or proc.get('searchable_title') or '(sem título)',
                                        'number': proc.get('number') or '',
                                        'clients_list': clients_list,
                                        'opposing_list': opposing_list,
                                        'cases_list': cases_list,
                                        'status': proc.get('status') or 'Em andamento',
                                        'area': proc.get('area') or proc.get('area_direito') or '',
                                        'link': proc.get('link') or '',
                                    })
                                
                                # Ordena por título
                                table_rows.sort(key=lambda r: (r.get('title') or '').lower())
                                
                                # Definir colunas da tabela (sincronizado com módulo de Processos - sem coluna Casos e sem Ações)
                                columns = [
                                    {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True, 'style': 'width: 120px; max-width: 120px;'},
                                    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True, 'style': 'width: 280px; max-width: 280px;'},
                                    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 180px;'},
                                    {'name': 'clients', 'label': 'Clientes', 'field': 'clients', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
                                    {'name': 'opposing', 'label': 'Parte Contrária', 'field': 'opposing', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
                                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 150px;'},
                                ]
                                
                                # Criar tabela (sincronizado com módulo de Processos)
                                processes_table = ui.table(
                                    columns=columns,
                                    rows=table_rows,
                                    row_key='_id',
                                    pagination={'rowsPerPage': 10}
                                ).classes('w-full').props('flat bordered dense')
                                
                                # Slot para área usando componente padrão (sincronizado com módulo de Processos)
                                processes_table.add_slot('body-cell-area', BODY_SLOT_AREA)
                                
                                # Slot para título (sincronizado com módulo de Processos - verde como padrão)
                                processes_table.add_slot('body-cell-title', '''
                                    <q-td :props="props" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 280px; padding: 8px 12px; vertical-align: middle;">
                                        <span class="text-sm cursor-pointer font-medium" 
                                              style="line-height: 1.4; color: #223631;"
                                              @click="$parent.$emit('titleClick', props.row)">
                                            {{ props.value }}
                                        </span>
                                    </q-td>
                                ''')
                                
                                # Slot para status usando componente padrão
                                processes_table.add_slot('body-cell-status', BODY_SLOT_STATUS)
                                
                                # Slot para clientes (múltiplos verticalmente - sincronizado com módulo de Processos)
                                processes_table.add_slot('body-cell-clients', '''
                                    <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 8px 8px;">
                                        <div v-if="props.row.clients_list && props.row.clients_list.length > 0" style="display: flex; flex-direction: column; gap: 2px;">
                                            <div v-for="(client, index) in props.row.clients_list" :key="index" class="text-xs text-gray-700" style="line-height: 1.3;">
                                                {{ client }}
                                            </div>
                                        </div>
                                        <span v-else class="text-gray-400">—</span>
                                    </q-td>
                                ''')
                                
                                # Slot para parte contrária (múltiplos verticalmente - sincronizado com módulo de Processos)
                                processes_table.add_slot('body-cell-opposing', '''
                                    <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 8px 8px;">
                                        <div v-if="props.row.opposing_list && props.row.opposing_list.length > 0" style="display: flex; flex-direction: column; gap: 2px;">
                                            <div v-for="(opposing, index) in props.row.opposing_list" :key="index" class="text-xs text-gray-700" style="line-height: 1.3;">
                                                {{ opposing }}
                                            </div>
                                        </div>
                                        <span v-else class="text-gray-400">—</span>
                                    </q-td>
                                ''')
                                
                                # Slot para número com link e botão copiar (idêntico ao módulo de Processos)
                                processes_table.add_slot('body-cell-number', '''
                                    <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
                                        <div style="display: flex; align-items: center; gap: 4px;">
                                            <a v-if="props.row.link && props.value" 
                                               :href="props.row.link" 
                                               target="_blank" 
                                               class="text-blue-600 hover:underline"
                                               style="font-size: 12px;">
                                                {{ props.value }}
                                            </a>
                                            <span v-else-if="props.value" style="font-size: 12px; color: #374151;">
                                                {{ props.value }}
                                            </span>
                                            <span v-else class="text-gray-400">—</span>
                                            <q-btn 
                                                v-if="props.value"
                                                flat dense round 
                                                icon="content_copy" 
                                                size="xs" 
                                                color="grey"
                                                @click.stop="navigator.clipboard.writeText(props.value); $q.notify({message: 'Número copiado!', color: 'positive', timeout: 1500})"
                                            />
                                        </div>
                                    </q-td>
                                ''')
                                
                                # Handler para clique no título (abre modal de edição - igual ao módulo de Processos)
                                def handle_title_click(e):
                                    """Handler para clique no título - abre modal de edição do processo"""
                                    clicked_row = e.args
                                    if clicked_row and '_id' in clicked_row:
                                        process_id = clicked_row['_id']
                                        async def _open():
                                            await open_edit_process_from_case(process_id)
                                        ui.run_coroutine(_open())
                                
                                processes_table.on('titleClick', handle_title_click)
                    
                    except Exception as e:
                        print(f"Erro ao carregar processos vinculados: {e}")
                        import traceback
                        traceback.print_exc()
                        with processes_container:
                            with ui.card().classes('w-full p-8 flex flex-col justify-center items-center bg-red-50 border border-red-200'):
                                ui.label('Erro ao carregar processos.').classes('text-red-600 font-semibold mb-2')
                                ui.label(f'Detalhes: {str(e)}').classes('text-red-500 text-sm')
                                ui.button('Tentar novamente', icon='refresh', on_click=render_linked_processes.refresh).props('color=red outline')
                
                # Diálogo para vincular processo existente (definido DEPOIS de render_linked_processes)
                with ui.dialog() as link_process_dialog, ui.card().classes('w-full max-w-2xl p-6'):
                    ui.label('Vincular Processo ao Caso').classes('text-lg font-bold mb-4')
                    
                    # Lista de processos disponíveis (todos os processos)
                    # Usa case_slug (fonte da verdade) em vez de título
                    all_processes = get_processes_list()  # Precisa dados frescos para vinculação
                    case_slug = case.get('slug')
                    linked_process_ids = {p.get('_id') for p in get_processes_by_case(case_slug=case_slug, case_title=case.get('title'))}
                    available_processes = [
                        {'label': f"{p.get('title', 'Sem título')} - {p.get('number', 'Sem número')}", 'value': p.get('_id')}
                        for p in all_processes if p.get('_id') not in linked_process_ids
                    ]
                    
                    if not available_processes:
                        ui.label('Todos os processos já estão vinculados a este caso.').classes('text-gray-500 italic')
                    else:
                        process_select = ui.select(
                            options=available_processes,
                            label='Selecione o processo',
                            with_input=True
                        ).classes('w-full mb-4').props('dense outlined')
                        
                        async def link_selected_process():
                            """Vincula um processo ao caso usando case_ids (fonte da verdade)"""
                            selected_id = process_select.value
                            if not selected_id:
                                ui.notify('Selecione um processo para vincular.', type='warning')
                                return
                            
                            try:
                                db = get_db()
                                case_slug = case.get('slug')
                                
                                if not case_slug:
                                    ui.notify('Caso não possui slug válido. Não é possível vincular.', type='negative')
                                    return
                                
                                doc_ref = db.collection('processes').document(selected_id)
                                doc = doc_ref.get()
                                
                                if not doc.exists:
                                    ui.notify('Processo não encontrado no Firestore. Pode ter sido excluído.', type='negative')
                                    link_process_dialog.close()
                                    render_linked_processes.refresh()
                                    return
                                
                                process_data = doc.to_dict()
                                case_ids = process_data.get('case_ids', [])
                                
                                # Usa case_ids (fonte da verdade) em vez de cases (títulos)
                                if case_slug not in case_ids:
                                    case_ids.append(case_slug)
                                    await run.io_bound(doc_ref.update, {'case_ids': case_ids})
                                    # save_process sincroniza automaticamente
                                    from ...core import save_process
                                    process_data['case_ids'] = case_ids
                                    save_process(process_data, doc_id=selected_id)
                                    ui.notify('Processo vinculado com sucesso!', type='positive')
                                    link_process_dialog.close()
                                    render_linked_processes.refresh()
                                else:
                                    ui.notify('Processo já está vinculado a este caso.', type='info')
                                    link_process_dialog.close()
                                    render_linked_processes.refresh()
                            except Exception as e:
                                print(f'Erro ao vincular processo {selected_id}: {e}')
                                import traceback
                                traceback.print_exc()
                                ui.notify(f'Erro ao vincular processo. Verifique sua conexão e tente novamente.', type='negative')
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Cancelar', on_click=link_process_dialog.close).props('flat')
                            ui.button('Vincular', icon='link', on_click=link_selected_process).props('color=primary')
                
                # ===== MODAL DE NOVO/EDITAR PROCESSO (DENTRO DA ABA PROCESSOS) =====
                process_form_state = {'is_editing': False, 'edit_id': None}
                process_modal_tab = {'current': 'dados_gerais'}  # Estado da aba atual
                
                # Variáveis globais para os campos do formulário (definidas ANTES de serem usadas)
                process_form_fields = {
                    'title_input': None,
                    'area_select': None,
                    'type_select': None,
                    'status_select': None,
                    'client_select': None,
                    'number_input': None,
                    'link_input': None,
                    'client_options': []
                }
                
                with ui.dialog() as edit_process_dialog, ui.card().classes('w-full max-w-6xl p-0 overflow-hidden').style('height: 85vh;'):
                    # Cabeçalho
                    with ui.row().classes('w-full items-center justify-between px-6 pt-6 pb-4'):
                        dialog_title = ui.label('Novo Processo').classes('text-xl font-bold text-gray-800')
                        error_message = ui.label('').classes('text-red-600 font-semibold text-sm')
                        error_message.visible = False
                    ui.separator()
                    
                    # Container principal: sidebar + conteúdo
                    with ui.row().classes('w-full m-0').style('height: calc(85vh - 120px); overflow: hidden;'):
                        # ===== SIDEBAR ESQUERDA COM ABAS =====
                        with ui.column().classes('w-56 bg-gray-50 border-r border-gray-200 p-0 flex-shrink-0').style('height: 100%; overflow-y: auto;'):
                            def set_process_tab(tab_name: str):
                                process_modal_tab['current'] = tab_name
                                refresh_process_tab_content()
                                render_sidebar_tabs.refresh()
                            
                            sidebar_tabs_container = ui.column().classes('w-full gap-1 p-3')
                            
                            @ui.refreshable
                            def render_sidebar_tabs():
                                sidebar_tabs_container.clear()
                                
                                with sidebar_tabs_container:
                                    # Aba: Dados gerais
                                    is_active = process_modal_tab['current'] == 'dados_gerais'
                                    btn_style = f'background-color: {PRIMARY_COLOR}; color: white;' if is_active else 'background-color: white; color: #374151; border: 1px solid #e5e7eb;'
                                    btn = ui.button('Dados gerais', icon='description', on_click=lambda: set_process_tab('dados_gerais'))
                                    btn.classes('w-full justify-start text-left').style(btn_style)
                                    
                                    # Aba: Estratégia
                                    is_active = process_modal_tab['current'] == 'estrategia'
                                    btn_style = f'background-color: {PRIMARY_COLOR}; color: white;' if is_active else 'background-color: white; color: #374151; border: 1px solid #e5e7eb;'
                                    with ui.row().classes('w-full items-center gap-2'):
                                        btn = ui.button('Estratégia', icon='lightbulb', on_click=lambda: set_process_tab('estrategia'))
                                        btn.classes('flex-1 justify-start text-left').style(btn_style)
                                    
                                    # Aba: Chave/acesso
                                    is_active = process_modal_tab['current'] == 'chave_acesso'
                                    btn_style = f'background-color: {PRIMARY_COLOR}; color: white;' if is_active else 'background-color: white; color: #374151; border: 1px solid #e5e7eb;'
                                    with ui.row().classes('w-full items-center gap-2'):
                                        btn = ui.button('Chave/acesso', icon='key', on_click=lambda: set_process_tab('chave_acesso'))
                                        btn.classes('flex-1 justify-start text-left').style(btn_style)
                            
                            render_sidebar_tabs()
                        
                        # ===== CONTEÚDO PRINCIPAL (ÁREA DIREITA) =====
                        content_container = ui.column().classes('flex-1 p-6').style('height: 100%; overflow-y: auto; background-color: #f8fafc;')
                        
                        @ui.refreshable
                        def refresh_process_tab_content():
                            content_container.clear()
                            
                            with content_container:
                                if process_modal_tab['current'] == 'dados_gerais':
                                    # ===== ABA: DADOS GERAIS =====
                                    with ui.column().classes('w-full gap-4'):
                                        ui.label('Dados Gerais do Processo').classes('text-lg font-semibold text-gray-700 mb-2')
                                        
                                        with ui.row().classes('w-full gap-3'):
                                            process_form_fields['title_input'] = ui.input('Título do processo *', placeholder='Ex: ACP - Município de ...').props('dense outlined clearable').classes('w-full')
                                        
                                        with ui.row().classes('w-full gap-3'):
                                            # Área do Direito: apenas as 5 opções padronizadas
                                            process_form_fields['area_select'] = ui.select(
                                                PROCESS_AREA_OPTIONS, 
                                                label='Área do direito *', 
                                                clearable=False,
                                                value='Administrativo'
                                            ).props('dense outlined').classes('flex-1')
                                            
                                            process_form_fields['type_select'] = ui.select(
                                                ['Existente', 'Futuro'], 
                                                label='Tipo *', 
                                                value='Existente'
                                            ).props('dense outlined').classes('w-56')
                                        
                                        with ui.row().classes('w-full gap-3'):
                                            status_options = ['Em andamento', 'Concluído', 'Concluído com pendências', 'Em monitoramento']
                                            process_form_fields['status_select'] = ui.select(
                                                status_options, 
                                                label='Status *', 
                                                value='Em andamento'
                                            ).props('dense outlined').classes('flex-1')
                                            
                                            # Cliente - usa a mesma lógica do New Case modal
                                            process_form_fields['client_options'] = get_client_options_for_select()
                                            
                                            process_form_fields['client_select'] = ui.select(
                                                options=process_form_fields['client_options'], 
                                                label='Cliente *', 
                                                with_input=True, 
                                                clearable=False
                                            ).props('dense outlined use-input fill-input').classes('flex-1')
                                        
                                        with ui.row().classes('w-full gap-3'):
                                            process_form_fields['number_input'] = ui.input('Número do processo *', placeholder='0000000-00.0000.0.00.0000').props('dense outlined clearable').classes('flex-1')
                                            process_form_fields['link_input'] = ui.input('Link do processo', placeholder='URL do processo no tribunal').props('dense outlined clearable').classes('flex-1')
                                        
                                        # Campo de Estado (herdado do caso - somente leitura)
                                        with ui.row().classes('w-full gap-2 items-center'):
                                            process_form_fields['state_input'] = ui.input(
                                                'Estado (UF)', 
                                                placeholder='Herdado do caso vinculado'
                                            ).props('dense outlined readonly').classes('flex-1').style('background-color: #f3f4f6;')
                                            
                                            ui.icon('info').classes('text-gray-400').tooltip('O estado é automaticamente herdado do caso vinculado')
                                
                                elif process_modal_tab['current'] == 'estrategia':
                                    # ===== ABA: ESTRATÉGIA (EM DESENVOLVIMENTO) =====
                                    with ui.column().classes('w-full items-center justify-center').style('height: 100%; min-height: 400px;'):
                                        ui.icon('construction', size='64px').classes('text-gray-400 mb-4')
                                        ui.label('Estratégia').classes('text-2xl font-bold text-gray-500 mb-2')
                                        ui.label('Esta funcionalidade está em desenvolvimento.').classes('text-gray-400')
                                
                                elif process_modal_tab['current'] == 'chave_acesso':
                                    # ===== ABA: CHAVE/ACESSO (EM DESENVOLVIMENTO) =====
                                    with ui.column().classes('w-full items-center justify-center').style('height: 100%; min-height: 400px;'):
                                        ui.icon('construction', size='64px').classes('text-gray-400 mb-4')
                                        ui.label('Chave/Acesso').classes('text-2xl font-bold text-gray-500 mb-2')
                                        ui.label('Esta funcionalidade está em desenvolvimento.').classes('text-gray-400')
                        
                        # Renderiza conteúdo inicial
                        refresh_process_tab_content()
                    
                    def set_process_error(message: str = ''):
                        error_message.text = message or ''
                        error_message.visible = bool(message)
                        error_message.update()
                    
                    def reset_process_form():
                        dialog_title.text = 'Novo Processo'
                        set_process_error('')
                        process_modal_tab['current'] = 'dados_gerais'
                        refresh_process_tab_content()
                        render_sidebar_tabs.refresh()
                        
                        # Aguarda um pouco para os campos serem criados
                        def _reset_fields():
                            if process_form_fields['title_input']:
                                process_form_fields['title_input'].value = ''
                            if process_form_fields['type_select']:
                                process_form_fields['type_select'].value = 'Existente'
                            if process_form_fields['status_select']:
                                process_form_fields['status_select'].value = 'Em andamento'
                            if process_form_fields['area_select']:
                                process_form_fields['area_select'].value = 'Administrativo'
                            if process_form_fields['client_select']:
                                process_form_fields['client_select'].value = None
                            if process_form_fields['number_input']:
                                process_form_fields['number_input'].value = ''
                            if process_form_fields['link_input']:
                                process_form_fields['link_input'].value = ''
                            # Estado herdado do caso (exibe estado do caso atual automaticamente)
                            if process_form_fields.get('state_input'):
                                case_state = case.get('state', '')
                                process_form_fields['state_input'].value = case_state or ''
                        
                        ui.timer(0.1, _reset_fields, once=True)
                    
                    def fill_process_form(process: dict):
                        dialog_title.text = 'Editar Processo'
                        set_process_error('')
                        process_modal_tab['current'] = 'dados_gerais'
                        refresh_process_tab_content()
                        render_sidebar_tabs.refresh()
                        
                        # Aguarda um pouco para os campos serem criados
                        def _fill_fields():
                            if process_form_fields['title_input']:
                                process_form_fields['title_input'].value = process.get('title', '')
                            if process_form_fields['type_select']:
                                process_form_fields['type_select'].value = process.get('tipo') or process.get('process_type') or 'Existente'
                            if process_form_fields['status_select']:
                                process_form_fields['status_select'].value = process.get('status') or 'Em andamento'
                            
                            # Normalizar área para valor canônico
                            if process_form_fields['area_select']:
                                area_value = process.get('area_direito') or process.get('area') or 'Administrativo'
                                normalized_area = normalize_process_area(area_value)
                                process_form_fields['area_select'].value = normalized_area
                            
                            # Cliente - converte ID para nome formatado para exibição
                            if process_form_fields['client_select']:
                                client_id = process.get('cliente_id') or process.get('client_id')
                                if not client_id:
                                    # Fallback: tenta obter do campo 'client' ou 'clients'
                                    clients_field = process.get('clients') or []
                                    client_name = clients_field[0] if clients_field else process.get('client')
                                    if client_name:
                                        # Se já é um nome, busca o formato formatado
                                        all_clients = _clients + _opposing
                                        for c in all_clients:
                                            if c.get('name', '') == client_name:
                                                formatted = format_client_option_for_select(c)
                                                process_form_fields['client_select'].value = formatted
                                                break
                                        else:
                                            process_form_fields['client_select'].value = client_name
                                    else:
                                        process_form_fields['client_select'].value = None
                                else:
                                    # Converte ID para nome formatado
                                    client_name = get_client_name_by_id(client_id)
                                    if client_name:
                                        all_clients = _clients + _opposing
                                        for c in all_clients:
                                            if c.get('name', '') == client_name:
                                                formatted = format_client_option_for_select(c)
                                                process_form_fields['client_select'].value = formatted
                                                break
                                        else:
                                            process_form_fields['client_select'].value = client_name
                                    else:
                                        process_form_fields['client_select'].value = None
                            
                            if process_form_fields['number_input']:
                                process_form_fields['number_input'].value = process.get('numero_processo') or process.get('number') or ''
                            if process_form_fields['link_input']:
                                process_form_fields['link_input'].value = process.get('link_processo') or process.get('link') or ''
                            # Estado herdado do caso
                            if process_form_fields.get('state_input'):
                                process_state = process.get('state', '')
                                # Se processo não tem estado, usa o do caso atual
                                if not process_state:
                                    process_state = case.get('state', '')
                                process_form_fields['state_input'].value = process_state or ''
                        
                        ui.timer(0.1, _fill_fields, once=True)
                    
                    def collect_process_form_data() -> dict:
                        # Garante que estamos na aba dados_gerais
                        if process_modal_tab['current'] != 'dados_gerais':
                            return None
                        
                        # O valor selecionado é uma string formatada (ex: "Nome (Apelido)")
                        # Precisamos extrair o nome e converter para ID
                        selected_option = process_form_fields['client_select'].value if process_form_fields['client_select'] else None
                        client_id = None
                        client_name = ''
                        
                        if selected_option:
                            # Extrai o nome completo da opção formatada
                            client_name = extract_client_name_from_formatted_option(selected_option)
                            # Converte nome para ID
                            client_id = get_client_id_by_name(client_name) or client_name
                        
                        # Garantir que área está normalizada
                        area_value = process_form_fields['area_select'].value if process_form_fields['area_select'] else 'Administrativo'
                        normalized_area = normalize_process_area(area_value)
                        
                        return {
                            'title': (process_form_fields['title_input'].value or '').strip() if process_form_fields['title_input'] else '',
                            'titulo': (process_form_fields['title_input'].value or '').strip() if process_form_fields['title_input'] else '',
                            'area_direito': normalized_area,
                            'area': normalized_area,
                            'tipo': process_form_fields['type_select'].value or 'Existente' if process_form_fields['type_select'] else 'Existente',
                            'process_type': process_form_fields['type_select'].value or 'Existente' if process_form_fields['type_select'] else 'Existente',
                            'status': process_form_fields['status_select'].value or '' if process_form_fields['status_select'] else '',
                            'cliente_id': client_id,
                            'client_id': client_id,
                            'client': client_name or client_id,
                            'clients': [client_name or client_id] if client_id else [],
                            'numero_processo': (process_form_fields['number_input'].value or '').strip() if process_form_fields['number_input'] else '',
                            'number': (process_form_fields['number_input'].value or '').strip() if process_form_fields['number_input'] else '',
                            'link_processo': (process_form_fields['link_input'].value or '').strip() if process_form_fields['link_input'] else '',
                            'link': (process_form_fields['link_input'].value or '').strip() if process_form_fields['link_input'] else '',
                        }
                    
                    async def save_process_from_case():
                        set_process_error('')
                        
                        # Garante que estamos na aba dados_gerais
                        if process_modal_tab['current'] != 'dados_gerais':
                            set_process_error('Por favor, preencha os dados gerais antes de salvar.')
                            process_modal_tab['current'] = 'dados_gerais'
                            refresh_process_tab_content()
                            render_sidebar_tabs.refresh()
                            return
                        
                        process_data = collect_process_form_data()
                        
                        if not process_data or not process_data.get('title'):
                            set_process_error('Título é obrigatório.')
                            return
                        if not process_data['number']:
                            set_process_error('Número do processo é obrigatório.')
                            return
                        if not process_data['area']:
                            set_process_error('Área do direito é obrigatória.')
                            return
                        if not process_data['tipo']:
                            set_process_error('Tipo é obrigatório.')
                            return
                        if not process_data['status']:
                            set_process_error('Status é obrigatório.')
                            return
                        if not process_data['cliente_id']:
                            set_process_error('Selecione um cliente.')
                            return
                        if process_data['link'] and not (process_data['link'].startswith('http://') or process_data['link'].startswith('https://')):
                            set_process_error('Informe um link válido (http ou https).')
                            return
                        
                        try:
                            is_editing = process_form_state['is_editing']
                            edit_id = process_form_state['edit_id']
                            
                            # Se está editando, preserva case_ids
                            if is_editing and edit_id:
                                def _merge_update():
                                    db = get_db()
                                    doc_ref = db.collection('processes').document(edit_id)
                                    snap = doc_ref.get()
                                    current = snap.to_dict() if snap.exists else {}
                                    # Preserva case_ids
                                    case_ids = current.get('case_ids', [])
                                    process_data['case_ids'] = case_ids
                                    current.update(process_data)
                                    save_process_core(current, doc_id=edit_id)
                                await run.io_bound(_merge_update)
                                ui.notify('Processo atualizado!', type='positive')
                            else:
                                # Novo processo: vincula automaticamente ao caso atual
                                case_slug = case.get('slug')
                                if case_slug:
                                    process_data['case_ids'] = [case_slug]
                                await run.io_bound(save_process_core, process_data)
                                ui.notify('Processo cadastrado e vinculado!', type='positive')
                            
                            await run.io_bound(sync_processes_cases)
                            edit_process_dialog.close()
                            render_linked_processes.refresh()
                        except Exception as e:
                            print(f'Erro ao salvar processo: {e}')
                            import traceback
                            traceback.print_exc()
                            set_process_error(f'Erro ao salvar: {e}')
                            ui.notify('Erro ao salvar o processo. Confira os dados e tente novamente.', type='negative')
                    
                    async def delete_process_from_modal():
                        if not process_form_state['is_editing'] or not process_form_state['edit_id']:
                            set_process_error('Apenas processos existentes podem ser excluídos.')
                            return
                        
                        try:
                            await run.io_bound(delete_process_core, process_form_state['edit_id'])
                            await run.io_bound(sync_processes_cases)
                            ui.notify('Processo excluído!', type='positive')
                            edit_process_dialog.close()
                            render_linked_processes.refresh()
                        except Exception as e:
                            print(f'Erro ao excluir processo: {e}')
                            import traceback
                            traceback.print_exc()
                            set_process_error(f'Erro ao excluir: {e}')
                            ui.notify('Erro ao excluir o processo.', type='negative')
                    
                    with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10'):
                        delete_process_button = ui.button('EXCLUIR', icon='delete', on_click=delete_process_from_modal).props('color=red').classes('font-bold')
                        ui.button('SALVAR', icon='save', on_click=save_process_from_case).props('color=primary').classes('font-bold')
                    delete_process_button.visible = False
                
                # Cabeçalho com botões (definido DEPOIS de render_linked_processes e do diálogo)
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Processos vinculados').classes('text-lg font-bold')
                    with ui.row().classes('gap-2'):
                        ui.button('Atualizar', icon='refresh', on_click=render_linked_processes.refresh).props('flat size=sm').tooltip('Recarregar processos do Firestore')
                        def open_new_process():
                            reset_process_form()
                            process_form_state['is_editing'] = False
                            process_form_state['edit_id'] = None
                            delete_process_button.visible = False
                            edit_process_dialog.open()
                        
                        ui.button('Novo Processo', icon='add', on_click=open_new_process).props('color=primary size=sm')
                        ui.button('Vincular Processo', icon='link', on_click=lambda: link_process_dialog.open()).props('color=primary size=sm outline')
                
                # Funções para manipular processos
                async def open_edit_process_from_case(process_id: str):
                    """Abre edição de processo usando o modal do módulo de processos"""
                    try:
                        # Busca todos os processos para encontrar o índice
                        all_processes = get_processes_list()
                        
                        # Encontra o índice do processo pelo ID
                        process_idx = None
                        for idx, proc in enumerate(all_processes):
                            if proc.get('_id') == process_id:
                                process_idx = idx
                                break
                        
                        if process_idx is None:
                            ui.notify('Processo não encontrado na lista.', type='negative')
                            return
                        
                        # Abre o modal de edição usando o índice
                        open_process_modal(process_idx=process_idx)
                    except Exception as e:
                        print(f'Erro ao abrir edição de processo: {e}')
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao abrir processo: {e}', type='negative')
                
                async def unlink_process(process_id: str):
                    """Desvincula um processo do caso atual usando case_ids (fonte da verdade)"""
                    if not process_id:
                        ui.notify('ID do processo não fornecido.', type='warning')
                        return
                    
                    try:
                        db = get_db()
                        case_slug = case.get('slug')
                        
                        if not case_slug:
                            ui.notify('Caso não possui slug válido.', type='warning')
                            return
                        
                        doc_ref = db.collection('processes').document(process_id)
                        doc = doc_ref.get()
                        
                        if not doc.exists:
                            ui.notify('Processo não encontrado no Firestore. Pode ter sido excluído.', type='negative')
                            render_linked_processes.refresh()
                            return
                        
                        process_data = doc.to_dict()
                        case_ids = process_data.get('case_ids', [])
                        
                        # Usa case_ids (fonte da verdade) em vez de cases (títulos)
                        if case_slug in case_ids:
                            case_ids.remove(case_slug)
                            # Atualiza usando save_process para garantir sincronização
                            from ...core import save_process
                            process_data['case_ids'] = case_ids
                            await run.io_bound(save_process, process_data, process_id)
                            ui.notify('Processo desvinculado com sucesso!', type='positive')
                            render_linked_processes.refresh()
                        else:
                            ui.notify('Processo já não está vinculado a este caso.', type='info')
                            render_linked_processes.refresh()
                    except Exception as e:
                        print(f'Erro ao desvincular processo {process_id}: {e}')
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao desvincular processo. Tente novamente ou atualize a página.', type='negative')
                
                async def delete_process_from_case(process_id: str):
                    """Exclui um processo (mesma lógica do módulo principal)"""
                    if not process_id:
                        ui.notify('ID do processo não fornecido.', type='warning')
                        return
                    
                    # Confirmação antes de excluir
                    try:
                        db = get_db()
                        doc = db.collection('processes').document(process_id).get()
                        if not doc.exists:
                            ui.notify('Processo não encontrado. Pode ter sido excluído.', type='warning')
                            render_linked_processes.refresh()
                            return
                        
                        process_title = doc.to_dict().get('title', 'processo')
                    except Exception as e:
                        process_title = 'processo'
                    
                    # Diálogo de confirmação
                    with ui.dialog() as confirm_dialog, ui.card().classes('p-6'):
                        ui.label(f'Confirma a exclusão do processo "{process_title}"?').classes('text-lg font-semibold mb-4')
                        ui.label('Esta ação não pode ser desfeita.').classes('text-red-600 mb-4')
                        
                        async def confirm_delete():
                            try:
                                await run.io_bound(delete_process_core, process_id)
                                # sync removido para performance - delete_process já limpa referências
                                ui.notify('Processo excluído com sucesso!', type='positive')
                                confirm_dialog.close()
                                render_linked_processes.refresh()
                            except Exception as e:
                                print(f'Erro ao excluir processo {process_id}: {e}')
                                import traceback
                                traceback.print_exc()
                                ui.notify(f'Erro ao excluir processo. Tente novamente ou atualize a página.', type='negative')
                                confirm_dialog.close()
                        
                        with ui.row().classes('w-full justify-end gap-2'):
                            ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                            ui.button('Excluir', icon='delete', on_click=confirm_delete).props('color=red')
                        
                        confirm_dialog.open()
                
                # Renderiza a tabela inicial
                render_linked_processes()

            # Tab 3: Cálculos
            with ui.tab_panel(calc_tab).classes('w-full'):
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.label('Cálculos').classes('text-lg font-bold')
                    ui.label('💾 Salvamento automático ativado').classes('text-xs text-green-600 italic')
                
                # Inicializar lista de cálculos se não existir
                if 'calculations' not in case:
                    case['calculations'] = []
                
                # Dialog para editar/preencher cálculo com planilha
                with ui.dialog() as edit_calc_dialog, ui.card().classes('w-full max-w-7xl p-6').style('max-height: 95vh; overflow-y: auto;'):
                    edit_state = {'is_editing': False, 'edit_index': None, 'calc_type': None}
                    
                    # Container para planilha
                    spreadsheet_table_container = ui.column().classes('w-full')
                    
                    def render_spreadsheet():
                        """Renderiza a planilha baseada no tipo de cálculo"""
                        if edit_state['edit_index'] is None:
                            return
                        
                        spreadsheet_table_container.clear()
                        calc = case['calculations'][edit_state['edit_index']]
                        calc_type = edit_state['calc_type']
                        
                        with spreadsheet_table_container:
                            if calc_type == 'Área Total':
                                # Áreas Afetadas
                                rows = calc.get('area_rows', [])
                                
                                ui.label('Áreas Afetadas').classes('text-lg font-semibold mb-4')
                                
                                # Lista de áreas afetadas
                                areas_list_container = ui.column().classes('w-full gap-3 mb-4')
                                
                                def render_areas_list():
                                    areas_list_container.clear()
                                    calc = case['calculations'][edit_state['edit_index']]
                                    rows = calc.get('area_rows', [])
                                    
                                    with areas_list_container:
                                        if not rows:
                                            ui.label('Nenhuma área afetada cadastrada. Clique em "Adicionar Área Afetada" para começar.').classes('text-gray-400 italic text-center py-4')
                                        
                                        for row_idx, row in enumerate(rows):
                                            with ui.card().classes('w-full p-4 border shadow-sm'):
                                                with ui.row().classes('w-full items-start gap-3'):
                                                    # Descrição
                                                    with ui.column().classes('flex-1'):
                                                        desc_input = ui.input(
                                                            'Descrição da área afetada',
                                                            value=row.get('description', ''),
                                                            placeholder='Ex: Área de preservação permanente'
                                                        ).classes('w-full').props('outlined')
                                                        
                                                        def update_desc(idx=row_idx):
                                                            calc = case['calculations'][edit_state['edit_index']]
                                                            if 'area_rows' not in calc:
                                                                calc['area_rows'] = []
                                                            if idx < len(calc['area_rows']):
                                                                calc['area_rows'][idx]['description'] = desc_input.value or ''
                                                                trigger_autosave()
                                                        
                                                        desc_input.on('update:model-value', lambda: update_desc())
                                                    
                                                    # Hectares
                                                    with ui.column().classes('w-40'):
                                                        hectares_input = ui.number(
                                                            'Hectares',
                                                            value=row.get('hectares', 0.0),
                                                            format='%.2f'
                                                        ).classes('w-full').props('outlined')
                                                        
                                                        def update_hectares(idx=row_idx):
                                                            calc = case['calculations'][edit_state['edit_index']]
                                                            if 'area_rows' not in calc:
                                                                calc['area_rows'] = []
                                                            if idx < len(calc['area_rows']):
                                                                calc['area_rows'][idx]['hectares'] = hectares_input.value or 0.0
                                                                trigger_autosave()
                                                                render_areas_list()
                                                        
                                                        hectares_input.on('update:model-value', lambda: update_hectares())
                                                    
                                                    # Status
                                                    with ui.column().classes('w-48'):
                                                        status_options = ['Perdido', 'Em discussão', 'Pendente', 'Recuperado']
                                                        status_select = ui.select(
                                                            options=status_options,
                                                            label='Status',
                                                            value=row.get('status', 'Pendente')
                                                        ).classes('w-full').props('outlined')
                                                        
                                                        def update_status(idx=row_idx):
                                                            calc = case['calculations'][edit_state['edit_index']]
                                                            if 'area_rows' not in calc:
                                                                calc['area_rows'] = []
                                                            if idx < len(calc['area_rows']):
                                                                calc['area_rows'][idx]['status'] = status_select.value or 'Pendente'
                                                                trigger_autosave()
                                                        
                                                        status_select.on('update:model-value', lambda: update_status())
                                                    
                                                    # Botão remover
                                                    def remove_area(idx=row_idx):
                                                        calc = case['calculations'][edit_state['edit_index']]
                                                        if 'area_rows' in calc and idx < len(calc['area_rows']):
                                                            calc['area_rows'].pop(idx)
                                                            trigger_autosave()
                                                            render_areas_list()
                                                    
                                                    ui.button(
                                                        icon='delete',
                                                        on_click=remove_area
                                                    ).props('flat round dense color=red').tooltip('Remover área')
                                
                                render_areas_list()
                                
                                # Botão para adicionar área
                                def add_area_row():
                                    calc = case['calculations'][edit_state['edit_index']]
                                    if 'area_rows' not in calc:
                                        calc['area_rows'] = []
                                    calc['area_rows'].append({
                                        'description': '',
                                        'hectares': 0.0,
                                        'status': 'Pendente'
                                    })
                                    trigger_autosave()
                                    render_areas_list()
                                
                                with ui.row().classes('w-full justify-center mb-4'):
                                    ui.button(
                                        '+ Adicionar Área Afetada',
                                        icon='add',
                                        on_click=add_area_row
                                    ).classes('bg-green-600 text-white px-6 py-2')
                                
                                # Total
                                if rows:
                                    total_hectares = sum(r.get('hectares', 0.0) for r in rows)
                                    with ui.card().classes('w-full p-4 mt-4 bg-green-50 border-2 border-green-300'):
                                        with ui.row().classes('w-full items-center justify-between'):
                                            ui.label('Total de Áreas Afetadas:').classes('font-semibold text-gray-700 text-lg')
                                            ui.label(f'{total_hectares:,.2f} hectares').classes('font-bold text-green-700 text-xl')
                                
                            else:  # Financeiro
                                # Planilha Financeira
                                rows = calc.get('finance_rows', [])
                                
                                # Cabeçalho
                                with ui.row().classes('w-full bg-gray-100 p-2 font-semibold text-sm border-b'):
                                    ui.label('Descrição do Prejuízo').classes('flex-1')
                                    ui.label('Valor (R$)').classes('w-40 text-center')
                                    ui.label('Status').classes('w-40 text-center')
                                    ui.label('Ações').classes('w-20 text-center')
                                
                                # Linhas
                                for row_idx, row in enumerate(rows):
                                    with ui.row().classes('w-full p-1 border-b items-center hover:bg-gray-50'):
                                        desc_input = ui.input('', value=row.get('description', '')).classes('flex-1').props('dense outlined')
                                        value_input = ui.number('', value=row.get('value', 0.0), format='%.2f').classes('w-40').props('dense outlined')
                                        
                                        status_options = ['Confirmado', 'Estimado', 'Em análise', 'Recuperado']
                                        status_select = ui.select(
                                            options=status_options,
                                            value=row.get('status', 'Em análise')
                                        ).classes('w-40').props('dense outlined')
                                        
                                        def update_row(idx=row_idx, desc=desc_input, value=value_input, status=status_select):
                                            calc = case['calculations'][edit_state['edit_index']]
                                            if 'finance_rows' not in calc:
                                                calc['finance_rows'] = []
                                            if idx < len(calc['finance_rows']):
                                                calc['finance_rows'][idx] = {
                                                    'description': desc.value or '',
                                                    'value': value.value or 0.0,
                                                    'status': status.value or 'Em análise'
                                                }
                                                trigger_autosave()
                                        
                                        desc_input.on('update:model-value', lambda: update_row())
                                        value_input.on('update:model-value', lambda: update_row())
                                        status_select.on('update:model-value', lambda: update_row())
                                        
                                        def remove_row(idx=row_idx):
                                            calc = case['calculations'][edit_state['edit_index']]
                                            if 'finance_rows' in calc and idx < len(calc['finance_rows']):
                                                calc['finance_rows'].pop(idx)
                                                trigger_autosave()
                                                render_spreadsheet()
                                        
                                        ui.button(icon='delete', on_click=remove_row).props('flat round dense color=red size=sm').classes('w-20').tooltip('Remover')
                                
                                # Total
                                total_value = sum(r.get('value', 0.0) for r in rows)
                                with ui.row().classes('w-full p-2 bg-gray-50 font-semibold border-t-2'):
                                    ui.label('Total:').classes('flex-1')
                                    ui.label(f'R$ {total_value:,.2f}').classes('w-40 text-center text-blue-700')
                                    ui.space().classes('w-40')
                                    ui.space().classes('w-20')
                                
                                def add_finance_row():
                                    calc = case['calculations'][edit_state['edit_index']]
                                    if 'finance_rows' not in calc:
                                        calc['finance_rows'] = []
                                    calc['finance_rows'].append({
                                        'description': '',
                                        'value': 0.0,
                                        'status': 'Em análise'
                                    })
                                    trigger_autosave()
                                    render_spreadsheet()
                                
                                ui.button('+ Adicionar Linha', icon='add', on_click=add_finance_row).classes('bg-blue-600 text-white mt-2').props('flat')
                    
                    # Renderizar planilha
                    render_spreadsheet()
                    
                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                        ui.button('Fechar', on_click=edit_calc_dialog.close).props('flat color=grey')
                
                # Dialog minimalista para escolher tipo
                with ui.dialog() as choose_type_dialog, ui.card().classes('w-full max-w-xs p-4'):
                    with ui.column().classes('w-full gap-2'):
                        ui.button(
                            'Área',
                            icon='square_foot',
                            on_click=lambda: (add_calculation('Área Total'), choose_type_dialog.close())
                        ).classes('w-full bg-green-600 text-white py-2')
                        
                        ui.button(
                            'Financeiro',
                            icon='attach_money',
                            on_click=lambda: (add_calculation('Financeiro'), choose_type_dialog.close())
                        ).classes('w-full bg-blue-600 text-white py-2')
                
                def add_calculation(calc_type):
                    """Adiciona um novo cálculo"""
                    calc_data = {
                        'type': calc_type,
                        'title': f'Cálculo {calc_type}',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    if calc_type == 'Área Total':
                        calc_data['area_rows'] = []
                    else:  # Financeiro
                        calc_data['finance_rows'] = []
                    
                    case['calculations'].append(calc_data)
                    trigger_autosave()
                    render_calculations_list.refresh()
                    # Abre automaticamente o dialog de edição
                    open_edit_dialog(len(case['calculations']) - 1)
                
                def open_edit_dialog(index):
                    calc = case['calculations'][index]
                    edit_state['calc_type'] = calc.get('type', 'Área Total')
                    edit_state['is_editing'] = True
                    edit_state['edit_index'] = index
                    
                    # Garantir que as estruturas existem
                    if calc.get('type') == 'Área Total':
                        if 'area_rows' not in calc:
                            calc['area_rows'] = []
                    else:
                        if 'finance_rows' not in calc:
                            calc['finance_rows'] = []
                    
                    render_spreadsheet()
                    edit_calc_dialog.open()
                
                def delete_calculation(index):
                    case['calculations'].pop(index)
                    trigger_autosave()
                    render_calculations_list.refresh()
                    ui.notify('Cálculo excluído!')
                
                @ui.refreshable
                def render_calculations_list():
                    # Botão de adicionar cálculo
                    with ui.row().classes('w-full justify-end mb-4'):
                        ui.button('Adicionar Cálculo', icon='add', on_click=choose_type_dialog.open).classes('bg-primary text-white')
                    
                    if not case.get('calculations'):
                        with ui.card().classes('w-full p-8 text-center'):
                            ui.label('Nenhum cálculo cadastrado ainda.').classes('text-gray-500')
                    else:
                        for idx, calc in enumerate(case.get('calculations', [])):
                            with ui.card().classes('w-full p-3 mb-2 hover:shadow-md transition-shadow'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.row().classes('items-center gap-3 flex-grow'):
                                        # Ícone
                                        if calc.get('type') == 'Área Total':
                                            ui.icon('square_foot', size='md').classes('text-green-600')
                                        else:
                                            ui.icon('attach_money', size='md').classes('text-blue-600')
                                        
                                        # Título e tipo
                                        with ui.column().classes('flex-grow'):
                                            ui.label(calc.get('title', 'Sem título')).classes('text-base font-semibold')
                                            
                                            # Resumo minimalista
                                            if calc.get('type') == 'Área Total':
                                                rows = calc.get('area_rows', [])
                                                if rows:
                                                    total = sum(r.get('hectares', 0.0) for r in rows)
                                                    ui.label(f'{len(rows)} área(s) • {total:,.2f} ha').classes('text-xs text-gray-500')
                                                else:
                                                    ui.label('Planilha vazia').classes('text-xs text-gray-400 italic')
                                            else:
                                                rows = calc.get('finance_rows', [])
                                                if rows:
                                                    total = sum(r.get('value', 0.0) for r in rows)
                                                    ui.label(f'{len(rows)} item(ns) • R$ {total:,.2f}').classes('text-xs text-gray-500')
                                                else:
                                                    ui.label('Planilha vazia').classes('text-xs text-gray-400 italic')
                                    
                                    # Botões de ação
                                    with ui.row().classes('gap-1'):
                                        ui.button(
                                            icon='edit',
                                            on_click=lambda i=idx: open_edit_dialog(i)
                                        ).props('flat round dense color=primary').tooltip('Editar')
                                        ui.button(
                                            icon='delete',
                                            on_click=lambda i=idx: delete_calculation(i)
                                        ).props('flat round dense color=red').tooltip('Excluir')
                
                render_calculations_list()

            # Tab 4: Relatório geral do caso
            with ui.tab_panel(report_tab).classes('w-full gap-4'):
                # Variável reativa para o conteúdo do relatório (permite edição)
                report_value = {'content': case.get('general_report', '')}
                
                # Indicador de salvamento automático (definido antes para ser usado no callback)
                @ui.refreshable
                def report_save_indicator():
                    if autosave_state.get('is_saving', False):
                        with ui.row().classes('items-center gap-2'):
                            ui.spinner('dots', size='xs').classes('text-yellow-600')
                            ui.label('Salvando...').classes('text-xs text-yellow-600 italic')
                    else:
                        ui.label('💾 Salvamento automático ativado').classes('text-xs text-green-600 italic')
                
                # Cabeçalho com título e controles
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    with ui.column().classes('flex-grow'):
                        ui.label('Relatório geral do caso').classes('text-lg font-bold')
                    with ui.row().classes('items-center gap-3'):
                        report_save_indicator()
                        # Registra o indicador para atualização automática
                        register_autosave_refresh(report_save_indicator)
                        
                        # Botão de salvamento manual
                        async def manual_save_report():
                            """Salva manualmente o relatório no Firestore"""
                            try:
                                autosave_state['is_saving'] = True
                                report_save_indicator.refresh()
                                
                                from ...core import save_case
                                # Lê o valor atual (a variável reativa é atualizada pelos callbacks)
                                current_value = report_value['content']
                                
                                # Atualiza tanto o caso quanto a variável reativa
                                case['general_report'] = current_value
                                report_value['content'] = current_value
                                
                                # Salva no Firestore
                                save_case(case)
                                
                                await asyncio.sleep(0.3)  # Pequeno delay para mostrar o indicador
                                
                                autosave_state['is_saving'] = False
                                report_save_indicator.refresh()
                                
                                ui.notify('Relatório salvo com sucesso!', type='positive', timeout=2000)
                            except Exception as e:
                                print(f'Erro ao salvar relatório: {e}')
                                import traceback
                                traceback.print_exc()
                                autosave_state['is_saving'] = False
                                report_save_indicator.refresh()
                                ui.notify(f'Erro ao salvar: {str(e)}', type='negative', timeout=3000)
                        
                        ui.button(
                            'Salvar',
                            icon='save',
                            on_click=manual_save_report
                        ).classes('bg-primary text-white px-4 py-2').props('dense')
                
                # Textarea simples e direto - pronto para uso imediato
                def on_textarea_change(e):
                    """Callback para textarea"""
                    try:
                        new_value = e.value if hasattr(e, 'value') else str(e)
                        report_value['content'] = new_value
                        case['general_report'] = new_value
                        trigger_autosave()
                        report_save_indicator.refresh()
                    except Exception as err:
                        print(f'Erro no callback do editor: {err}')
                
                # Editor de texto rico para relatório
                report_textarea = ui.editor(
                    value=report_value['content'],
                    placeholder='Digite o relatório geral do caso aqui...',
                    on_change=on_textarea_change
                ).classes('w-full').style('min-height: 300px')
                    

            # Tab 5: Vistorias
            with ui.tab_panel(vistorias_tab).classes('w-full gap-4'):
                # Variável reativa para o conteúdo das vistorias (permite edição)
                vistorias_value = {'content': case.get('vistorias', '')}
                
                # Indicador de salvamento automático
                @ui.refreshable
                def vistorias_save_indicator():
                    if autosave_state.get('is_saving', False):
                        with ui.row().classes('items-center gap-2'):
                            ui.spinner('dots', size='xs').classes('text-yellow-600')
                            ui.label('Salvando...').classes('text-xs text-yellow-600 italic')
                    else:
                        ui.label('💾 Salvamento automático ativado').classes('text-xs text-green-600 italic')
                
                # Cabeçalho com título e controles
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    with ui.column().classes('flex-grow'):
                        ui.label('Vistorias').classes('text-lg font-bold')
                    with ui.row().classes('items-center gap-3'):
                        vistorias_save_indicator()
                        # Registra o indicador para atualização automática
                        register_autosave_refresh(vistorias_save_indicator)
                        
                        # Botão de salvamento manual
                        async def manual_save_vistorias():
                            """Salva manualmente as vistorias no Firestore"""
                            try:
                                autosave_state['is_saving'] = True
                                vistorias_save_indicator.refresh()
                                
                                from ...core import save_case
                                # Lê o valor atual (a variável reativa é atualizada pelos callbacks)
                                current_value = vistorias_value['content']
                                
                                # Atualiza tanto o caso quanto a variável reativa
                                case['vistorias'] = current_value
                                vistorias_value['content'] = current_value
                                
                                # Salva no Firestore
                                save_case(case)
                                
                                await asyncio.sleep(0.3)  # Pequeno delay para mostrar o indicador
                                
                                autosave_state['is_saving'] = False
                                vistorias_save_indicator.refresh()
                                
                                ui.notify('Vistorias salvas com sucesso!', type='positive', timeout=2000)
                            except Exception as e:
                                print(f'Erro ao salvar vistorias: {e}')
                                import traceback
                                traceback.print_exc()
                                autosave_state['is_saving'] = False
                                vistorias_save_indicator.refresh()
                                ui.notify(f'Erro ao salvar: {str(e)}', type='negative', timeout=3000)
                        
                        ui.button(
                            'Salvar',
                            icon='save',
                            on_click=manual_save_vistorias
                        ).classes('bg-primary text-white px-4 py-2').props('dense')
                
                # Textarea simples e direto - pronto para uso imediato
                def on_vistorias_change(e):
                    """Callback para editor de texto rico"""
                    try:
                        new_value = e.value if hasattr(e, 'value') else str(e)
                        vistorias_value['content'] = new_value
                        case['vistorias'] = new_value
                        trigger_autosave()
                        vistorias_save_indicator.refresh()
                    except Exception as err:
                        print(f'Erro no callback do editor: {err}')
                
                # Editor de texto rico para vistorias
                vistorias_editor = ui.editor(
                    value=vistorias_value['content'],
                    placeholder='Digite as informações das vistorias aqui...',
                    on_change=on_vistorias_change
                ).classes('w-full').style('min-height: 300px')

            # Tab 6: Estratégia geral
            with ui.tab_panel(strategy_tab).classes('w-full gap-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Estratégia geral').classes('text-lg font-bold')
                    ui.label('💾 Salvamento automático ativado').classes('text-xs text-green-600 italic')
                
                with ui.expansion('Objetivos do caso', icon='flag').classes('w-full border rounded bg-gray-50'):
                    def on_objectives_change(e):
                        new_value = e.value if hasattr(e, 'value') else str(e)
                        case['objectives'] = new_value
                        trigger_autosave()
                    
                    ui.editor(
                        value=case.get('objectives', ''),
                        placeholder='Descreva os objetivos do caso...',
                        on_change=on_objectives_change
                    ).classes('w-full').style('min-height: 150px')

                with ui.expansion('Considerações Jurídicas', icon='gavel').classes('w-full border rounded bg-gray-50'):
                    def on_legal_considerations_change(e):
                        new_value = e.value if hasattr(e, 'value') else str(e)
                        case['legal_considerations'] = new_value
                        trigger_autosave()
                    
                    ui.editor(
                        value=case.get('legal_considerations', ''),
                        placeholder='Descreva as considerações jurídicas do caso...',
                        on_change=on_legal_considerations_change
                    ).classes('w-full').style('min-height: 150px')

                with ui.expansion('Considerações Técnicas', icon='science').classes('w-full border rounded bg-gray-50'):
                    def on_technical_considerations_change(e):
                        new_value = e.value if hasattr(e, 'value') else str(e)
                        case['technical_considerations'] = new_value
                        trigger_autosave()
                    
                    ui.editor(
                        value=case.get('technical_considerations', ''),
                        placeholder='Descreva as considerações técnicas do caso...',
                        on_change=on_technical_considerations_change
                    ).classes('w-full').style('min-height: 150px')

                with ui.expansion('Teses a serem utilizadas', icon='gavel').classes('w-full border rounded bg-gray-50'):
                    # Inicializar lista de teses se não existir
                    if 'theses' not in case or not isinstance(case.get('theses'), list):
                        case['theses'] = []
                    
                    # Dialog para adicionar/editar tese
                    with ui.dialog() as thesis_dialog, ui.card().classes('w-full max-w-4xl p-6').style('max-height: 90vh; overflow-y: auto;'):
                        dialog_title = ui.label('Adicionar Tese').classes('text-xl font-bold mb-4 text-primary')
                        
                        edit_state = {'is_editing': False, 'edit_index': None}
                        
                        thesis_name = ui.input('Qual é a tese?').classes('w-full mb-4').props('outlined')
                        thesis_description = ui.textarea('Breve descrição da tese').classes('w-full mb-4').props('outlined rows=3')
                        
                        # Probabilidade (muito alta/alta/média/baixa/muito baixa)
                        probability_options = ['Muito alta', 'Alta', 'Média', 'Baixa', 'Muito baixa']
                        thesis_probability = ui.select(
                            options=probability_options,
                            label='Probabilidade de chance da tese dar certo',
                            value='Média'
                        ).classes('w-full mb-4').props('outlined')
                        
                        thesis_observations = ui.textarea('Observações').classes('w-full mb-4').props('outlined rows=3')
                        
                        status_options = [
                            'Apresentada e em discussão perante os órgãos',
                            'Rejeitada',
                            'Aguardando o momento certo para apresentar a tese'
                        ]
                        thesis_status = ui.select(
                            options=status_options,
                            label='Status da tese',
                            value='Aguardando o momento certo para apresentar a tese'
                        ).classes('w-full mb-4').props('outlined')
                        
                        def save_thesis():
                            if not thesis_name.value:
                                ui.notify('O nome da tese é obrigatório!', type='warning')
                                return
                            
                            thesis_data = {
                                'name': thesis_name.value,
                                'description': thesis_description.value or '',
                                'probability': thesis_probability.value or 'Média',
                                'observations': thesis_observations.value or '',
                                'status': thesis_status.value or 'Aguardando o momento certo para apresentar a tese'
                            }
                            
                            if edit_state['is_editing']:
                                case['theses'][edit_state['edit_index']] = thesis_data
                                ui.notify('Tese atualizada!')
                            else:
                                case['theses'].append(thesis_data)
                                ui.notify('Tese adicionada!')
                            
                            trigger_autosave()
                            render_theses_list.refresh()
                            thesis_dialog.close()
                        
                        def reset_form():
                            thesis_name.value = ''
                            thesis_description.value = ''
                            thesis_probability.value = 'Média'
                            thesis_observations.value = ''
                            thesis_status.value = 'Aguardando o momento certo para apresentar a tese'
                            edit_state['is_editing'] = False
                            edit_state['edit_index'] = None
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Cancelar', on_click=thesis_dialog.close).props('flat color=grey')
                            ui.button('Salvar', on_click=save_thesis).classes('bg-primary text-white')
                    
                    def open_add_dialog():
                        dialog_title.text = 'Adicionar Tese'
                        reset_form()
                        thesis_dialog.open()
                    
                    def open_edit_dialog(index):
                        thesis = case['theses'][index]
                        dialog_title.text = 'Editar Tese'
                        thesis_name.value = thesis.get('name', '')
                        thesis_description.value = thesis.get('description', '')
                        # Compatibilidade: se probability for número, converter para texto
                        prob_value = thesis.get('probability', 'Média')
                        if isinstance(prob_value, (int, float)):
                            # Converter número antigo para texto (mapeamento aproximado)
                            if prob_value >= 80:
                                prob_value = 'Muito alta'
                            elif prob_value >= 60:
                                prob_value = 'Alta'
                            elif prob_value >= 40:
                                prob_value = 'Média'
                            elif prob_value >= 20:
                                prob_value = 'Baixa'
                            else:
                                prob_value = 'Muito baixa'
                        thesis_probability.value = prob_value if prob_value in probability_options else 'Média'
                        thesis_observations.value = thesis.get('observations', '')
                        thesis_status.value = thesis.get('status', 'Aguardando o momento certo para apresentar a tese')
                        edit_state['is_editing'] = True
                        edit_state['edit_index'] = index
                        thesis_dialog.open()
                    
                    def delete_thesis(index):
                        case['theses'].pop(index)
                        trigger_autosave()
                        render_theses_list.refresh()
                        ui.notify('Tese excluída!')
                    
                    @ui.refreshable
                    def render_theses_list():
                        with ui.column().classes('w-full gap-3'):
                            with ui.row().classes('w-full justify-end mb-2'):
                                ui.button('Adicionar Tese', icon='add', on_click=open_add_dialog).classes('bg-primary text-white')
                            
                            if not case.get('theses'):
                                with ui.card().classes('w-full p-8 text-center bg-gray-50'):
                                    ui.label('Nenhuma tese cadastrada ainda.').classes('text-gray-500')
                            else:
                                for idx, thesis in enumerate(case.get('theses', [])):
                                    with ui.card().classes('w-full p-4 border-l-4').style(f'border-left-color: {PRIMARY_COLOR}'):
                                        with ui.row().classes('w-full items-start justify-between mb-2'):
                                            with ui.column().classes('flex-grow gap-2'):
                                                ui.label(thesis.get('name', 'Sem nome')).classes('text-lg font-bold text-gray-800')
                                                
                                                if thesis.get('description'):
                                                    ui.label(thesis.get('description')).classes('text-sm text-gray-600')
                                                
                                                # Probabilidade
                                                probability = thesis.get('probability', 'Média')
                                                # Compatibilidade: se probability for número, converter para texto
                                                if isinstance(probability, (int, float)):
                                                    if probability >= 80:
                                                        probability = 'Muito alta'
                                                    elif probability >= 60:
                                                        probability = 'Alta'
                                                    elif probability >= 40:
                                                        probability = 'Média'
                                                    elif probability >= 20:
                                                        probability = 'Baixa'
                                                    else:
                                                        probability = 'Muito baixa'
                                                
                                                probability_colors = {
                                                    'Muito alta': 'bg-green-100 text-green-800 border-green-300',
                                                    'Alta': 'bg-green-50 text-green-700 border-green-200',
                                                    'Média': 'bg-yellow-100 text-yellow-800 border-yellow-300',
                                                    'Baixa': 'bg-orange-100 text-orange-800 border-orange-300',
                                                    'Muito baixa': 'bg-red-100 text-red-800 border-red-300'
                                                }
                                                prob_color = probability_colors.get(probability, 'bg-gray-100 text-gray-800 border-gray-300')
                                                
                                                with ui.row().classes('w-full items-center gap-2 mt-2'):
                                                    ui.label('Probabilidade:').classes('text-xs text-gray-500')
                                                    ui.label(probability).classes(f'text-xs px-2 py-1 rounded-full border font-semibold {prob_color}')
                                                    
                                                if thesis.get('observations'):
                                                    with ui.card().classes('w-full p-2 mt-2 bg-gray-50'):
                                                        ui.label('Observações:').classes('text-xs font-semibold text-gray-600 mb-1')
                                                        ui.label(thesis.get('observations')).classes('text-sm text-gray-700')
                                                
                                                # Status
                                                status = thesis.get('status', 'Aguardando o momento certo para apresentar a tese')
                                                status_colors = {
                                                    'Apresentada e em discussão perante os órgãos': 'bg-blue-100 text-blue-800 border-blue-300',
                                                    'Rejeitada': 'bg-red-100 text-red-800 border-red-300',
                                                    'Aguardando o momento certo para apresentar a tese': 'bg-yellow-100 text-yellow-800 border-yellow-300'
                                                }
                                                status_color = status_colors.get(status, 'bg-gray-100 text-gray-800 border-gray-300')
                                                ui.label(status).classes(f'text-xs px-2 py-1 rounded-full border w-fit mt-2 {status_color}')
                                            
                                            with ui.row().classes('gap-2'):
                                                ui.button(
                                                    icon='edit',
                                                    on_click=lambda i=idx: open_edit_dialog(i)
                                                ).props('flat round dense color=primary').tooltip('Editar')
                                                ui.button(
                                                    icon='delete',
                                                    on_click=lambda i=idx: delete_thesis(i)
                                                ).props('flat round dense color=red').tooltip('Excluir')
                                    
                                    if idx < len(case.get('theses', [])) - 1:
                                        ui.separator().classes('my-2')
                    
                    render_theses_list()

                with ui.expansion('Matriz SWOT do caso', icon='grid_view').classes('w-full border rounded bg-gray-50'):
                    with ui.column().classes('w-full p-4 items-center'):
                        ui.label('Clique abaixo para abrir a Matriz SWOT detalhada').classes('text-gray-500 mb-2')
                        ui.button('Abrir Matriz SWOT', icon='open_in_new', on_click=lambda: ui.navigate.to(f'/casos/{case_slug}/matriz-swot')).classes('bg-primary text-white w-full')

                with ui.expansion('Observações', icon='note').classes('w-full border rounded bg-gray-50'):
                    def on_strategy_observations_change(e):
                        new_value = e.value if hasattr(e, 'value') else str(e)
                        case['strategy_observations'] = new_value
                        trigger_autosave()
                    
                    ui.editor(
                        value=case.get('strategy_observations', ''),
                        placeholder='Adicione observações gerais sobre a estratégia do caso...',
                        on_change=on_strategy_observations_change
                    ).classes('w-full').style('min-height: 150px')

            # Tab 7: Próximas ações
            with ui.tab_panel(next_actions_tab).classes('w-full'):
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.label('Próximas ações').classes('text-lg font-bold')
                    ui.label('💾 Salvamento automático ativado').classes('text-xs text-green-600 italic')
                
                def on_next_actions_change(e):
                    new_value = e.value if hasattr(e, 'value') else str(e)
                    case['next_actions'] = new_value
                    trigger_autosave()
                
                ui.editor(
                    value=case.get('next_actions', ''),
                    placeholder='Liste as próximas ações do caso...',
                    on_change=on_next_actions_change
                ).classes('w-full').style('min-height: 300px')

            # Tab 8: Slack
            with ui.tab_panel(slack_tab).classes('w-full'):
                ui.label('Slack').classes('text-lg font-bold mb-4')
                with ui.card().classes('w-full p-8 flex flex-col items-center justify-center bg-gray-50'):
                    ui.label('No futuro, o Slack do escritório será adicionado neste local.').classes('text-gray-500 italic text-center')

            # Tab 9: Links úteis
            with ui.tab_panel(links_tab).classes('w-full'):
                ui.label('Links úteis').classes('text-lg font-bold mb-4')
                
                if not isinstance(case.get('links'), list):
                    case['links'] = []
                
                edit_state = {'is_editing': False, 'edit_index': None}
                
                with ui.dialog() as add_link_dialog, ui.card().classes('w-full max-w-md p-6'):
                    dialog_title = ui.label('Adicionar Link').classes('text-xl font-bold mb-4 text-primary')
                    
                    link_title = ui.input('Título do Link').classes('w-full mb-2').props('outlined')
                    link_url = ui.input('URL do Link').classes('w-full mb-2').props('outlined')
                    
                    link_type_options = [
                        'Google Drive',
                        'NotebookLM',
                        'Ayoa',
                        'Slack',
                        'Outros'
                    ]
                    link_type = ui.select(options=link_type_options, label='Tipo do Link', value='Outros').classes('w-full mb-4')
                    
                    def save_link():
                        if not link_title.value or not link_url.value:
                            ui.notify('Título e URL são obrigatórios!', type='warning')
                            return
                        
                        link_data = {
                            'title': link_title.value,
                            'url': link_url.value,
                            'type': link_type.value
                        }
                        
                        if edit_state['is_editing']:
                            case['links'][edit_state['edit_index']] = link_data
                            ui.notify('Link atualizado!')
                        else:
                            case['links'].append(link_data)
                            ui.notify('Link adicionado!')
                        
                        # CRÍTICO: Salvar no Firebase
                        from ...core import save_case
                        save_case(case)
                        
                        save_data()
                        render_links_list.refresh()
                        add_link_dialog.close()
                        link_title.value = ''
                        link_url.value = ''
                        link_type.value = 'Outros'
                        edit_state['is_editing'] = False
                        edit_state['edit_index'] = None
                    
                    with ui.row().classes('w-full justify-end gap-2'):
                        ui.button('Cancelar', on_click=add_link_dialog.close).props('flat color=grey')
                        ui.button('Salvar', on_click=save_link).classes('bg-primary text-white')
                
                def open_add_dialog():
                    dialog_title.text = 'Adicionar Link'
                    link_title.value = ''
                    link_url.value = ''
                    link_type.value = 'Outros'
                    edit_state['is_editing'] = False
                    edit_state['edit_index'] = None
                    add_link_dialog.open()
                
                def open_edit_dialog(idx, link):
                    dialog_title.text = 'Editar Link'
                    link_title.value = link['title']
                    link_url.value = link['url']
                    link_type.value = link.get('type', 'Outros')
                    edit_state['is_editing'] = True
                    edit_state['edit_index'] = idx
                    add_link_dialog.open()
                
                with ui.row().classes('w-full justify-end mb-4'):
                    ui.button('Adicionar Link', icon='add_link', on_click=open_add_dialog).classes('bg-primary text-white')
                
                @ui.refreshable
                def render_links_list():
                    if not case.get('links'):
                        with ui.card().classes('w-full p-8 flex justify-center items-center bg-gray-50'):
                            ui.label('Nenhum link cadastrado.').classes('text-gray-400 italic')
                        return
                    
                    def render_logo(link_type):
                        if link_type == 'Google Drive':
                            ui.html('''
                                <svg width="24" height="24" viewBox="0 0 87.3 78" xmlns="http://www.w3.org/2000/svg">
                                    <path d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z" fill="#0066da"/>
                                    <path d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44a9.06 9.06 0 0 0 -1.2 4.5h27.5z" fill="#00ac47"/>
                                    <path d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z" fill="#ea4335"/>
                                    <path d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z" fill="#00832d"/>
                                    <path d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684fc"/>
                                    <path d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#ffba00"/>
                                </svg>
                            ''', sanitize=False).classes('flex-shrink-0')
                        elif link_type == 'NotebookLM':
                            ui.html('''
                                <svg width="24" height="24" viewBox="0 0 106 80" xmlns="http://www.w3.org/2000/svg">
                                  <g fill="#4285F4">
                                    <path d="M52.96.1C23.71.1,0,23.61,0,52.62v25.15h9.76v-2.51c0-11.77,9.61-21.31,21.48-21.31s21.48,9.54,21.48,21.31v2.51h9.76v-2.51c0-17.11-13.99-30.98-31.24-30.98-6.72,0-12.94,2.1-18.03,5.69,5.33-10.51,16.31-17.73,28.99-17.73,17.91,0,32.43,14.41,32.43,32.16v13.36h9.76v-13.36c0-23.11-18.89-41.85-42.19-41.85-10.48,0-20.06,3.79-27.44,10.06,7.25-13.59,21.63-22.84,38.21-22.84,23.86,0,43.2,19.18,43.2,42.84v25.15h9.76v-25.15C105.92,23.61,82.21.1,52.96.1Z"/>
                                  </g>
                                </svg>
                            ''', sanitize=False).classes('flex-shrink-0')
                        elif link_type == 'Ayoa':
                            ui.html('''
                                <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="12" r="11" fill="#FD4556"/>
                                    <text x="12" y="16" font-family="Arial, sans-serif" font-size="12" fill="white" text-anchor="middle" font-weight="bold">A</text>
                                </svg>
                            ''', sanitize=False).classes('flex-shrink-0')
                        elif link_type == 'Slack':
                            ui.html('''
                                <svg width="24" height="24" viewBox="0 0 54 54" xmlns="http://www.w3.org/2000/svg">
                                    <g fill="none">
                                        <path d="M19.712.133a5.381 5.381 0 0 0-5.376 5.387 5.381 5.381 0 0 0 5.376 5.386h5.376V5.52A5.381 5.381 0 0 0 19.712.133m0 14.365H5.376A5.381 5.381 0 0 0 0 19.884a5.381 5.381 0 0 0 5.376 5.387h14.336a5.381 5.381 0 0 0 5.376-5.387 5.381 5.381 0 0 0-5.376-5.386" fill="#36c5f0"/>
                                        <path d="M53.76 19.884a5.381 5.381 0 0 0-5.376-5.386 5.381 5.381 0 0 0-5.376 5.386v5.387h5.376a5.381 5.381 0 0 0 5.376-5.387m-14.336 0V5.52A5.381 5.381 0 0 0 34.048.133a5.381 5.381 0 0 0-5.376 5.387v14.364a5.381 5.381 0 0 0 5.376 5.387 5.381 5.381 0 0 0 5.376-5.387" fill="#2eb67d"/>
                                        <path d="M34.048 54a5.381 5.381 0 0 0 5.376-5.387 5.381 5.381 0 0 0-5.376-5.386h-5.376v5.386A5.381 5.381 0 0 0 34.048 54m0-14.365h14.336a5.381 5.381 0 0 0 5.376-5.386 5.381 5.381 0 0 0-5.376-5.387H34.048a5.381 5.381 0 0 0-5.376 5.387 5.381 5.381 0 0 0 5.376 5.386" fill="#ecb22e"/>
                                        <path d="M0 34.249a5.381 5.381 0 0 0 5.376 5.386 5.381 5.381 0 0 0 5.376-5.386v-5.387H5.376A5.381 5.381 0 0 0 0 34.25m14.336 0v14.364a5.381 5.381 0 0 0 5.376 5.387 5.381 5.381 0 0 0 5.376-5.387V34.25a5.381 5.381 0 0 0-5.376-5.387 5.381 5.381 0 0 0-5.376 5.387" fill="#e01e5a"/>
                                    </g>
                                </svg>
                            ''', sanitize=False).classes('flex-shrink-0')
                        else:
                            ui.html(f'''
                                <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path fill="{PRIMARY_COLOR}" d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
                                </svg>
                            ''', sanitize=False).classes('flex-shrink-0')
                    
                    with ui.column().classes('w-full gap-2'):
                        for idx, link in enumerate(case.get('links', [])):
                            link_type = link.get('type', 'Outros')
                            
                            with ui.card().classes('w-full p-3 hover:shadow-md transition-shadow duration-200 border-l-4').style(f'border-left-color: {PRIMARY_COLOR}'):
                                with ui.row().classes('w-full items-center gap-3 justify-between'):
                                    with ui.row().classes('items-center gap-3 flex-grow'):
                                        render_logo(link_type)
                                        ui.link(link['title'], link['url'], new_tab=True).classes('text-base font-medium text-gray-800 hover:text-primary hover:underline no-underline')
                                    
                                    with ui.row().classes('gap-1'):
                                        ui.button(icon='edit', on_click=lambda i=idx, l=link: open_edit_dialog(i, l)).props('flat round dense').classes('text-gray-600').tooltip('Editar link')
                                        
                                        def delete_link(index=idx):
                                            case['links'].pop(index)
                                            
                                            # CRÍTICO: Salvar no Firebase
                                            from ...core import save_case
                                            save_case(case)
                                            
                                            save_data()
                                            ui.notify('Link removido!')
                                            render_links_list.refresh()
                                        
                                        ui.button(icon='delete', on_click=delete_link).props('flat round dense').classes('text-red-500').tooltip('Remover link')
                
                render_links_list()


@ui.page('/casos/{case_slug}/matriz-swot')
def case_swot(case_slug: str):
    case = next((c for c in get_cases_list() if c.get('slug') == case_slug), None)
    if not case:
        ui.label('Caso não encontrado.').classes('text-xl text-red-500 p-8')
        return

    # Inicializar listas se não existirem (migração de string para lista)
    for key in ['swot_s', 'swot_w', 'swot_o', 'swot_t']:
        if key not in case:
            case[key] = [''] * 10
        elif isinstance(case[key], str):
            # Migrar string antiga para lista com 10 linhas
            old_value = case[key].strip()
            if old_value:
                case[key] = [old_value] + [''] * 9
            else:
                case[key] = [''] * 10
        elif isinstance(case[key], list):
            # Garantir que sempre há 10 linhas
            while len(case[key]) < 10:
                case[key].append('')
            case[key] = case[key][:10]  # Limitar a 10 linhas

    # Sistema de salvamento automático com debounce
    import asyncio
    swot_autosave_state = {'timer': None, 'is_saving': False}
    
    async def swot_autosave_with_debounce(delay: float = 2.0):
        """Salva após um delay, cancelando salvamentos anteriores pendentes."""
        if swot_autosave_state['timer']:
            swot_autosave_state['timer'].cancel()
        
        async def delayed_save():
            await asyncio.sleep(delay)
            swot_autosave_state['is_saving'] = True
            swot_save_indicator.refresh()
            
            await asyncio.sleep(0.3)
            save_data()
            
            swot_autosave_state['is_saving'] = False
            swot_save_indicator.refresh()
        
        swot_autosave_state['timer'] = asyncio.create_task(delayed_save())
    
    def swot_trigger_autosave():
        asyncio.create_task(swot_autosave_with_debounce())

    def create_swot_section(title: str, icon: str, color: str, bg_color: str, border_color: str, field_key: str):
        """Cria uma seção SWOT com campos expansíveis e contador"""
        with ui.card().classes(f'w-full h-full p-4 {bg_color} flex flex-col border-l-4 {border_color} overflow-auto'):
            # Cabeçalho com título e contador
            with ui.row().classes('items-center justify-between w-full mb-3 flex-shrink-0'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon(icon, size='md').classes(f'text-{color}-600')
                    ui.label(title).classes(f'text-xl font-bold text-{color}-800')
                
                # Contador de itens preenchidos
                @ui.refreshable
                def item_counter():
                    lines = case.get(field_key, [])
                    filled_count = sum(1 for line in lines if line.strip())
                    total_count = len([line for line in lines if line is not None])
                    ui.label(f'{filled_count}/{total_count}').classes(f'text-sm font-medium text-{color}-600 bg-white px-2 py-1 rounded')
                
                item_counter()
            
            # Inicializar com pelo menos 2 campos
            lines = case.get(field_key, [])
            if len(lines) < 2:
                lines.extend([''] * (2 - len(lines)))
            case[field_key] = lines[:10]  # Máximo 10 campos
            
            # Estado para controlar campos visíveis
            visible_fields = {'count': max(2, len([line for line in lines if line.strip()]))}
            if visible_fields['count'] < len(lines) and any(lines[visible_fields['count']:]):
                visible_fields['count'] = len(lines)
            
            def update_line(idx: int, value: str):
                """Atualiza uma linha específica e gerencia expansão automática"""
                lines = case.get(field_key, [])
                while len(lines) <= idx:
                    lines.append('')
                
                lines[idx] = value
                case[field_key] = lines[:10]  # Limitar a 10 linhas
                swot_trigger_autosave()
                
                # Expandir automaticamente se necessário
                filled_count = sum(1 for line in lines if line.strip())
                if value.strip() and idx == visible_fields['count'] - 1 and visible_fields['count'] < 10:
                    visible_fields['count'] = min(visible_fields['count'] + 1, 10)
                    fields_container.refresh()
                
                item_counter.refresh()
            
            def make_on_change(idx: int):
                """Factory function para criar callback com índice correto"""
                return lambda val: update_line(idx, val)
            
            @ui.refreshable
            def fields_container():
                with ui.column().classes('w-full gap-2 flex-grow'):
                    for idx in range(visible_fields['count']):
                        line_value = lines[idx] if idx < len(lines) else ''
                        with ui.row().classes('w-full gap-2 items-start'):
                            # Textarea com suporte a atalhos de teclado
                            textarea = ui.textarea(
                                value=line_value,
                                placeholder='Digite aqui...',
                                on_change=make_on_change(idx)
                            ).classes('flex-grow bg-white rounded border border-gray-300 swot-textarea').props('rows=1 outlined')
                    
                    # Botão para adicionar campo manualmente (se ainda não chegou no máximo)
                    if visible_fields['count'] < 10:
                        def add_field():
                            visible_fields['count'] = min(visible_fields['count'] + 1, 10)
                            fields_container.refresh()
                        
                        ui.button(
                            '+ Adicionar item',
                            on_click=add_field,
                            icon='add'
                        ).classes(f'mt-2 text-{color}-600 border-{color}-300 hover:bg-{color}-50').props('flat outlined size=sm')
            
            fields_container()
    
    # Adicionar CSS e JavaScript para suporte a atalhos de teclado
    ui.add_head_html('''
    <style>
    .swot-textarea {
        font-family: inherit;
    }
    </style>
    <script>
    (function() {
        let observer = null;
        let isInitialized = false;
        
        function setupKeyboardShortcuts(textareaElement) {
            try {
                if (!textareaElement || textareaElement.dataset.shortcutsSetup === 'true') {
                    return;
                }
                
                textareaElement.addEventListener('keydown', function(e) {
                    try {
                        // Ctrl+B ou Cmd+B para negrito
                        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                            e.preventDefault();
                            const start = this.selectionStart || 0;
                            const end = this.selectionEnd || 0;
                            const selected = this.value.substring(start, end);
                            if (selected) {
                                this.value = this.value.substring(0, start) + 
                                            '**' + selected + '**' + 
                                            this.value.substring(end);
                                this.selectionStart = start + 2;
                                this.selectionEnd = end + 2;
                            } else {
                                this.value = this.value.substring(0, start) + '****' + this.value.substring(end);
                                this.selectionStart = start + 2;
                                this.selectionEnd = start + 2;
                            }
                            const inputEvent = new Event('input', { bubbles: true });
                            this.dispatchEvent(inputEvent);
                        }
                        // Ctrl+I ou Cmd+I para itálico
                        if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                            e.preventDefault();
                            const start = this.selectionStart || 0;
                            const end = this.selectionEnd || 0;
                            const selected = this.value.substring(start, end);
                            if (selected) {
                                this.value = this.value.substring(0, start) + 
                                            '*' + selected + '*' + 
                                            this.value.substring(end);
                                this.selectionStart = start + 1;
                                this.selectionEnd = end + 1;
                            } else {
                                this.value = this.value.substring(0, start) + '**' + this.value.substring(end);
                                this.selectionStart = start + 1;
                                this.selectionEnd = start + 1;
                            }
                            const inputEvent = new Event('input', { bubbles: true });
                            this.dispatchEvent(inputEvent);
                        }
                    } catch (err) {
                        console.error('Erro ao processar atalho:', err);
                    }
                });
                
                textareaElement.dataset.shortcutsSetup = 'true';
            } catch (err) {
                console.error('Erro ao configurar atalhos:', err);
            }
        }
        
        function initSwotShortcuts() {
            try {
                const textareas = document.querySelectorAll('.swot-textarea');
                textareas.forEach(function(ta) {
                    setupKeyboardShortcuts(ta);
                });
            } catch (err) {
                console.error('Erro ao inicializar atalhos:', err);
            }
        }
        
        function startObserver() {
            if (observer) {
                return;
            }
            try {
                observer = new MutationObserver(function() {
                    initSwotShortcuts();
                });
                observer.observe(document.body, { 
                    childList: true, 
                    subtree: true 
                });
            } catch (err) {
                console.error('Erro ao iniciar observer:', err);
            }
        }
        
        if (!isInitialized) {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    initSwotShortcuts();
                    startObserver();
                    isInitialized = true;
                });
            } else {
                initSwotShortcuts();
                startObserver();
                isInitialized = true;
            }
        }
    })();
    </script>
    ''')

    with layout(f'Matriz SWOT: {case["title"]}', breadcrumbs=[('Casos', '/casos'), (case['title'], f'/casos/{case_slug}'), ('Matriz SWOT', None)]):
        # Indicador de salvamento automático
        @ui.refreshable
        def swot_save_indicator():
            with ui.row().classes('fixed top-4 right-4 z-50'):
                if swot_autosave_state['is_saving']:
                    with ui.card().classes('px-4 py-2 bg-yellow-100 border border-yellow-400 rounded-lg shadow-lg flex items-center gap-2'):
                        ui.spinner('dots', size='sm').classes('text-yellow-600')
                        ui.label('Salvando...').classes('text-yellow-700 text-sm font-medium')
        
        swot_save_indicator()
        
        # Indicadores removidos para interface mais limpa
        
        with ui.grid(columns=2).classes('w-full h-[60vh] gap-4'):
            create_swot_section(
                '✅ Forças (Strengths)',
                'check_circle',
                'green',
                'bg-green-50',
                'border-green-500',
                'swot_s'
            )
            
            create_swot_section(
                '⚠️ Fraquezas (Weaknesses)',
                'warning',
                'red',
                'bg-red-50',
                'border-red-500',
                'swot_w'
            )
            
            create_swot_section(
                '📈 Oportunidades (Opportunities)',
                'trending_up',
                'blue',
                'bg-blue-50',
                'border-blue-500',
                'swot_o'
            )
            
            create_swot_section(
                '⚠️ Ameaças (Threats)',
                'report_problem',
                'orange',
                'bg-orange-50',
                'border-orange-500',
                'swot_t'
            )
