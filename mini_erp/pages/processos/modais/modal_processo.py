from nicegui import ui
from datetime import datetime
from ....core import (
    PRIMARY_COLOR, get_cases_list, get_clients_list, get_opposing_parties_list, 
    get_processes_list, format_date_br, get_display_name, get_protocols_by_process
)
from ..models import (
    PROCESS_TYPE_OPTIONS, SYSTEM_OPTIONS, NUCLEO_OPTIONS, AREA_OPTIONS,
    STATUS_OPTIONS, RESULT_OPTIONS, SCENARIO_TYPE_OPTIONS,
    SCENARIO_STATUS_OPTIONS, SCENARIO_IMPACT_OPTIONS, SCENARIO_CHANCE_OPTIONS,
    PROCESSES_TABLE_CSS
)
from ..utils import (
    get_short_name, format_option_for_search, get_option_value,
    get_scenario_type_style, get_scenario_status_icon,
    get_scenario_impact_icon, get_scenario_chance_icon
)
from ..business_logic import (
    validate_process, should_show_result_field, build_process_data
)
from ..database import save_process, delete_process, get_process_passwords, save_process_password, delete_process_password

def make_required_label(text: str) -> str:
    """
    Adiciona asterisco ao final do label para campos obrigatórios.
    
    Args:
        text: Texto do label (pode incluir ícones)
    
    Returns:
        Label com asterisco simples (sem HTML)
    """
    return f'{text} *'

class DummyField:
    """Helper class para campos dummy que mantém compatibilidade com código existente."""
    def __init__(self, default_value):
        self._value = default_value
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val

def render_process_dialog(on_success=None):
    """
    Factory function to create the Process Modal (Dialog).
    Handles both 'NOVO PROCESSO' and 'EDITAR PROCESSO' modes.
    
    Args:
        on_success: Callback function to run after successful save/delete (e.g., refresh list).
    
    Returns:
        tuple: (dialog_component, open_function)
        - dialog_component: The ui.dialog instance.
        - open_function: Function to open the dialog, accepts optional process_idx for editing.
    """
    
    # Inject CSS styles for sidebar menu
    ui.add_head_html(f'<style>{PROCESSES_TABLE_CSS}</style>')
    
    # State
    state = {
        'is_editing': False,
        'edit_index': None,
        'process_id': None,  # _id do processo no Firestore
        'parent_ids': [],  # Lista de IDs dos processos pais (vínculos)
        'scenarios': [],
        'protocols': [],
        'selected_clients': [],
        'selected_opposing': [],
        'selected_others': [],
        'selected_cases': []
    }
    
    # Referência para opções de casos (atualizada quando o modal abre)
    case_options_ref = {'val': [c['title'] for c in get_cases_list()]}

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden relative').style('height: 80vh; max-height: 80vh;'):
        with ui.row().classes('w-full h-full gap-0'):
            # Sidebar
            with ui.column().classes('h-full shrink-0 justify-between').style(f'width: 170px; background: {PRIMARY_COLOR};'):
                with ui.column().classes('w-full gap-0'):
                    dialog_title = ui.label('NOVO PROCESSO').classes('text-xs font-medium px-3 py-2 text-white/80 uppercase tracking-wide')
                    
                    with ui.tabs().props('vertical dense no-caps inline-label').classes('w-full process-sidebar-tabs') as tabs:
                        tab_basic = ui.tab('Dados básicos', icon='description')
                        tab_legal = ui.tab('Dados jurídicos', icon='gavel')
                        tab_relatory = ui.tab('Relatório', icon='article')
                        tab_strategy = ui.tab('Estratégia', icon='lightbulb')
                        tab_scenarios = ui.tab('Cenários', icon='analytics')
                        tab_protocols = ui.tab('Protocolos', icon='history')
                        tab_access = ui.tab('Senhas de acesso', icon='key')
                        tab_slack = ui.tab('Slack', icon='tag')
            
            # Variáveis dummy para campos de acesso (mantidas para compatibilidade com código de salvamento)
            access_lawyer_requested = DummyField(False)
            access_lawyer_granted = DummyField(False)
            access_technicians_requested = DummyField(False)
            access_technicians_granted = DummyField(False)
            access_client_requested = DummyField(False)
            access_client_granted = DummyField(False)
            access_lawyer_comment = DummyField('')
            access_technicians_comment = DummyField('')
            access_client_comment = DummyField('')
            
            # Content
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_basic).classes('w-full h-full p-4 bg-transparent'):
                    
                    # --- TAB 1: DADOS BÁSICOS ---
                    with ui.tab_panel(tab_basic):
                        with ui.column().classes('w-full gap-4'):
                            
                            # Mapeamento de cores para tags
                            TAG_COLORS = {
                                'clients': '#4CAF50',      # Verde para Clientes
                                'opposing': '#F44336',     # Vermelho para Parte Contrária
                                'others': '#2196F3',       # Azul para Outros Envolvidos
                                'cases': '#9C27B0'         # Roxo para Casos Vinculados
                            }

                            # Lists Helpers
                            def refresh_chips(container, items, tag_type, source_list):
                                container.clear()
                                safe_source = source_list or []
                                chip_color = TAG_COLORS.get(tag_type, '#6B7280')  # Cor padrão cinza se não encontrado
                                with container:
                                    with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                        for item in items:
                                            short = get_short_name(item, safe_source) if safe_source else item
                                            with ui.badge(short).classes('pr-1').style(f'background-color: {chip_color}; color: white;'):
                                                ui.button(icon='close', on_click=lambda i=item: remove_item(items, i, container, tag_type, source_list)).props('flat dense round size=xs color=white')

                            def remove_item(list_ref, item, container, tag_type, source_list):
                                if item in list_ref:
                                    list_ref.remove(item)
                                    refresh_chips(container, list_ref, tag_type, source_list)

                            def add_item(select, list_ref, container, tag_type, source_list):
                                val = select.value
                                if val and val != '-' and val not in list_ref:
                                    full_name = get_option_value(val, source_list) if source_list else val
                                    
                                    # CORREÇÃO: Busca o nome de exibição ao invés de salvar nome completo
                                    display_name = full_name  # fallback
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
                                    else:
                                        ui.notify('Este item já está adicionado!', type='warning')
                                elif val and val in list_ref:
                                    ui.notify('Este item já está adicionado!', type='warning')
                            
                            # Função para atualizar chips de processos pais (definida antes do uso)
                            def refresh_parent_chips(container, parent_ids):
                                container.clear()
                                all_procs = get_processes_list()
                                proc_map = {p.get('_id'): p for p in all_procs if p.get('_id')}
                                
                                with container:
                                    with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                        for pid in parent_ids:
                                            proc = proc_map.get(pid)
                                            if proc:
                                                title = proc.get('title') or proc.get('number') or 'Sem título'
                                                number = proc.get('number', '')
                                                display = f"{title}" + (f" ({number})" if number else "")
                                                with ui.badge(display).classes('pr-1').style('background-color: #FF9800; color: white;'):
                                                    ui.button(icon='close', on_click=lambda pid=pid: remove_parent_process(state['parent_ids'], pid, parent_process_chips)).props('flat dense round size=xs color=white')
                            
                            # Função para remover processo pai
                            def remove_parent_process(list_ref, process_id, container):
                                if process_id in list_ref:
                                    list_ref.remove(process_id)
                                    refresh_parent_chips(container, list_ref)
                            
                            # Função para adicionar processo pai
                            def add_parent_process(select, list_ref, container):
                                val = select.value
                                if val and val != '— Nenhum (processo raiz) —' and val != '-':
                                    # Extrair o ID do processo (formato: "Título | id")
                                    if ' | ' in val:
                                        process_id = val.split(' | ')[-1].strip()
                                        
                                        # Validação: não pode ser o próprio processo
                                        if process_id == state.get('process_id'):
                                            ui.notify('Um processo não pode ser vinculado a si mesmo!', type='warning')
                                            return
                                        
                                        # Validação: não pode já estar na lista
                                        if process_id in list_ref:
                                            ui.notify('Este processo pai já está adicionado!', type='warning')
                                            return
                                        
                                        # Validação: verifica ciclos (simplificada - validação completa no save)
                                        # Adiciona à lista
                                        list_ref.append(process_id)
                                        select.value = None
                                        refresh_parent_chips(container, list_ref)
                                    else:
                                        ui.notify('Formato inválido do processo selecionado', type='warning')
                                elif val and val in list_ref:
                                    ui.notify('Este processo pai já está adicionado!', type='warning')

                            # SEÇÃO 1 - Identificação do Processo
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('📋 Identificação do Processo').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-4'):
                                    with ui.row().classes('w-full gap-4 items-start'):
                                        title_input = ui.input(make_required_label('Título do Processo')).classes('flex-grow').props('outlined dense')
                                        title_input.tooltip('Nome descritivo do processo. Ex: AIA 450566 - DESMATAMENTO - IBAMA')
                                        number_input = ui.input(make_required_label('Número do Processo')).classes('w-48').props('outlined dense')
                                        number_input.tooltip('Número oficial do processo no tribunal ou órgão')
                                    
                                    with ui.row().classes('w-full gap-4 items-center'):
                                        link_input = ui.input('Link do Processo').classes('flex-grow').props('outlined dense')
                                        link_input.tooltip('URL para acessar o processo no sistema do tribunal (SEI, PJe, etc)')
                                        
                                        def open_link():
                                            link = link_input.value.strip()
                                            if link:
                                                # Garante que o link tenha protocolo
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
                                        update_button_state()  # Estado inicial
                                    
                                    type_select = ui.select(PROCESS_TYPE_OPTIONS, label=make_required_label('Tipo de processo'), value='Existente').classes('w-full').props('outlined dense')
                                    type_select.tooltip('Classificação: Novo (ainda não existe) ou Existente (já em andamento)')
                                    
                                    # =====================================================
                                    # CAMPO DATA DE ABERTURA (APROXIMADA)
                                    # =====================================================
                                    # Permite 3 formatos de precisão:
                                    # - Data completa: DD/MM/AAAA (ex: 05/09/2008)
                                    # - Mês e ano: MM/AAAA (ex: 09/2008)
                                    # - Apenas ano: AAAA (ex: 2008)
                                    # =====================================================
                                    
                                    def validate_approximate_date(value: str) -> bool:
                                        """
                                        Valida data aproximada em 3 formatos possíveis.
                                        """
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
                                    
                                    # Estado para o seletor de data
                                    date_selector_state = {
                                        'type': 'full',
                                        'day': '01',
                                        'month': '01',
                                        'year': str(datetime.now().year)
                                    }
                                    
                                    # Input de data
                                    with ui.row().classes('items-center gap-2'):
                                        data_abertura_input = ui.input(
                                            'Data de Abertura', 
                                            placeholder='Ex: 2008, 09/2008, 05/09/2008'
                                        ).classes('w-56').props('outlined dense')
                                        data_abertura_input.tooltip(
                                            'Formatos aceitos:\n'
                                            '• Ano: 2008\n'
                                            '• Mês/Ano: 09/2008\n'
                                            '• Completa: 05/09/2008'
                                        )
                                        data_abertura_input.validation = {'Formato inválido': validate_approximate_date}
                                        
                                        # Menu popup para seleção de data aproximada
                                        with ui.menu().props('anchor="bottom left" self="top left"') as date_menu:
                                            with ui.card().classes('p-4 w-72'):
                                                ui.label('📅 Data Aproximada').classes('text-base font-bold mb-2')
                                                
                                                # Seletor de tipo
                                                date_type_sel = ui.select(
                                                    options={
                                                        'full': '📆 Data completa',
                                                        'month_year': '📅 Mês e ano',
                                                        'year_only': '📋 Apenas ano'
                                                    },
                                                    value='full',
                                                    label='Precisão'
                                                ).classes('w-full mb-2').props('outlined dense')
                                                
                                                # Campos de seleção
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
                                        
                                        # Botão para abrir o menu
                                        def open_date_selector():
                                            # Pré-preenche com valor atual
                                            val = data_abertura_input.value or ''
                                            if val:
                                                if len(val) == 4:
                                                    date_type_sel.value = 'year_only'
                                                    year_sel.value = val
                                                elif len(val) == 7:
                                                    date_type_sel.value = 'month_year'
                                                    parts = val.split('/')
                                                    month_sel.value = parts[0]
                                                    year_sel.value = parts[1]
                                                elif len(val) == 10:
                                                    date_type_sel.value = 'full'
                                                    parts = val.split('/')
                                                    day_sel.value = parts[0]
                                                    month_sel.value = parts[1]
                                                    year_sel.value = parts[2]
                                            on_type_change()
                                            date_menu.open()
                                        
                                        ui.button(icon='edit_calendar', on_click=open_date_selector).props('flat dense round').tooltip('Selecionar data aproximada')

                            # SEÇÃO 2 - Partes Envolvidas
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('👥 Partes Envolvidas').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-4'):
                                    # Clients
                                    client_options = [format_option_for_search(c) for c in get_clients_list()]
                                    with ui.row().classes('w-full gap-4'):
                                        with ui.column().classes('flex-1 gap-2'):
                                            with ui.row().classes('w-full gap-2 items-center'):
                                                client_sel = ui.select(client_options or ['-'], label=make_required_label('Clientes'), with_input=True).classes('flex-grow').props('dense outlined')
                                                client_sel.tooltip('Pessoas ou empresas que você representa neste processo')
                                                ui.button(icon='add', on_click=lambda: add_item(client_sel, state['selected_clients'], client_chips, 'clients', get_clients_list())).props('flat dense').style('color: #4CAF50;')
                                            client_chips = ui.column().classes('w-full')

                                        # Opposing
                                        opposing_options = [format_option_for_search(op) for op in get_opposing_parties_list()]
                                        with ui.column().classes('flex-1 gap-2'):
                                            with ui.row().classes('w-full gap-2 items-center'):
                                                opposing_sel = ui.select(opposing_options or ['-'], label='Parte Contrária', with_input=True).classes('flex-grow').props('dense outlined')
                                                opposing_sel.tooltip('Pessoa, empresa ou órgão do lado oposto do processo')
                                                ui.button(icon='add', on_click=lambda: add_item(opposing_sel, state['selected_opposing'], opposing_chips, 'opposing', get_opposing_parties_list())).props('flat dense').style('color: #F44336;')
                                            opposing_chips = ui.column().classes('w-full')

                                    # Others
                                    with ui.column().classes('w-full gap-2'):
                                        with ui.row().classes('w-full gap-2 items-center'):
                                            others_sel = ui.select(opposing_options or ['-'], label='Outros Envolvidos', with_input=True).classes('flex-grow').props('dense outlined')
                                            others_sel.tooltip('Terceiros interessados, assistentes, litisconsortes, etc')
                                            ui.button(icon='add', on_click=lambda: add_item(others_sel, state['selected_others'], others_chips, 'others', get_opposing_parties_list())).props('flat dense').style('color: #2196F3;')
                                        others_chips = ui.column().classes('w-full')

                            # SEÇÃO 3 - Vínculos
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('🔗 Vínculos').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-2'):
                                    # Container para chips de processos pais
                                    parent_process_chips = ui.column().classes('w-full')
                                    
                                    # Processos Pais (múltiplos vínculos)
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        parent_process_sel = ui.select(
                                            options=['— Nenhum (processo raiz) —'],
                                            label='Processos Pais (opcional)',
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined use-input filter-input')
                                        parent_process_sel.tooltip(
                                            'Adicione processos pais para criar vínculos. Você pode adicionar múltiplos.\n'
                                            'Use a busca para encontrar processos rapidamente.'
                                        )
                                        ui.button(icon='add', on_click=lambda: add_parent_process(parent_process_sel, state['parent_ids'], parent_process_chips)).props('flat dense').style('color: #FF9800;')
                                    
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        cases_sel = ui.select(case_options_ref['val'] or ['-'], label='Casos Vinculados', with_input=True).classes('flex-grow').props('dense outlined')
                                        cases_sel.tooltip('Casos do escritório relacionados a este processo')
                                        ui.button(icon='add', on_click=lambda: add_item(cases_sel, state['selected_cases'], cases_chips, 'cases', None)).props('flat dense').style('color: #9C27B0;')
                                    cases_chips = ui.column().classes('w-full')

                    # --- TAB 2: DADOS JURÍDICOS ---
                    with ui.tab_panel(tab_legal):
                        with ui.column().classes('w-full gap-4'):
                            system_select = ui.select(SYSTEM_OPTIONS, label='Sistema Processual').classes('w-full')
                            nucleo_select = ui.select(NUCLEO_OPTIONS, label='Núcleo', value='Ambiental').classes('w-full')
                            area_select = ui.select(AREA_OPTIONS, label='Área').classes('w-full')
                            
                            status_select = ui.select(STATUS_OPTIONS, label='Status', value='Em andamento').classes('w-full')
                            
                            # Campo: Envolve Dano em APP?
                            envolve_dano_app_switch = ui.switch(
                                'Envolve Dano em Área de Preservação Permanente (APP)?',
                                value=False
                            ).classes('w-full')
                            envolve_dano_app_switch.tooltip('Marque se o processo envolve dano em APP conforme Código Florestal')
                            
                            # Campo: Área Total Discutida (ha)
                            area_total_discutida_input = ui.number(
                                label='Área Total Discutida (ha)',
                                placeholder='Ex: 150.5',
                                format='%.2f',
                                min=0,
                                step=0.01
                            ).classes('w-full').props('outlined dense')
                            area_total_discutida_input.tooltip('Área total discutida no processo em hectares. Ex: 150.5')
                            
                            result_container = ui.column().classes('w-full gap-2 hidden')
                            with result_container:
                                result_select = ui.select(RESULT_OPTIONS, label='Resultado do processo').classes('w-full').props('dense outlined')
                            
                            def toggle_result(e=None):
                                val = status_select.value
                                if should_show_result_field(val):
                                    result_container.classes(remove='hidden')
                                else:
                                    result_container.classes(add='hidden')
                                    result_select.value = None
                            status_select.on_value_change(toggle_result)

                    # --- TAB 3: RELATÓRIO DO PROCESSO ---
                    with ui.tab_panel(tab_relatory):
                        with ui.column().classes('w-full gap-5'):
                            ui.label('Resumo dos Fatos').classes('text-sm font-semibold text-gray-700')
                            relatory_facts_input = ui.editor(placeholder='Descreva os principais fatos do processo...').classes('w-full').style('height: 200px')
                            
                            ui.label('Histórico / Linha do Tempo').classes('text-sm font-semibold text-gray-700')
                            relatory_timeline_input = ui.editor(placeholder='Descreva a sequência cronológica dos eventos...').classes('w-full').style('height: 200px')
                            
                            ui.label('Documentos Relevantes').classes('text-sm font-semibold text-gray-700')
                            relatory_documents_input = ui.editor(placeholder='Liste os documentos importantes do processo...').classes('w-full').style('height: 200px')

                    # --- TAB 4: ESTRATÉGIA ---
                    with ui.tab_panel(tab_strategy):
                        with ui.column().classes('w-full gap-5'):
                            ui.label('Objetivos').classes('text-sm font-semibold text-gray-700')
                            objectives_input = ui.editor(placeholder='Descreva os objetivos...').classes('w-full').style('height: 200px')
                            
                            ui.label('Teses a serem trabalhadas').classes('text-sm font-semibold text-gray-700')
                            thesis_input = ui.editor(placeholder='Descreva as teses...').classes('w-full').style('height: 200px')
                            
                            ui.label('Observações').classes('text-sm font-semibold text-gray-700')
                            observations_input = ui.editor(placeholder='Observações...').classes('w-full').style('height: 200px')

                    # --- TAB 5: CENÁRIOS ---
                    with ui.tab_panel(tab_scenarios):
                        # Scenario Dialog
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
                                    data = {'title': s_title.value, 'type': s_type.value, 'status': s_status.value, 'impact': s_impact.value, 'chance': s_chance.value, 'obs': s_obs.value}
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
                                s_title.value = d.get('title'); s_type.value = d.get('type'); s_status.value = d.get('status')
                                s_impact.value = d.get('impact'); s_chance.value = d.get('chance'); s_obs.value = d.get('obs')
                            else:
                                s_title.value = ''; s_type.value = None; s_status.value = None; s_impact.value = None; s_chance.value = None; s_obs.value = ''
                            scen_dialog.open()

                        ui.button('+ Novo Cenário', on_click=lambda: open_scen_dialog(None)).props('flat dense color=primary')
                        
                        @ui.refreshable
                        def render_scenarios():
                            if not state['scenarios']:
                                ui.label('Nenhum cenário.').classes('text-gray-400 italic text-sm')
                                return
                            for i, s in enumerate(state['scenarios']):
                                tipo = s.get('type', '⚪ Neutro')
                                _, cor_hex = get_scenario_type_style(tipo)
                                with ui.card().classes('w-full p-3 mb-2').style(f'border-left: 3px solid {cor_hex};'):
                                    with ui.row().classes('w-full justify-between'):
                                        with ui.column():
                                            ui.label(s['title']).classes('font-medium')
                                            ui.label(tipo).style(f'color: {cor_hex}').classes('text-xs')
                                        with ui.row():
                                            ui.button(icon='edit', on_click=lambda idx=i: open_scen_dialog(idx)).props('flat dense size=sm color=primary')
                                            def rm_scen(idx=i): state['scenarios'].pop(idx); render_scenarios.refresh()
                                            ui.button(icon='delete', on_click=rm_scen).props('flat dense size=sm color=red')
                        render_scenarios()

                    # --- TAB 6: PROTOCOLOS ---
                    with ui.tab_panel(tab_protocols):
                        # Dialog para protocolo local (dentro do processo)
                        with ui.dialog() as prot_dialog, ui.card().classes('p-4 w-96'):
                            prot_title_label = ui.label('Novo Protocolo').classes('text-lg font-bold mb-2')
                            p_title = ui.input('Título').classes('w-full').props('dense outlined')
                            p_date = ui.input('Data').classes('w-full').props('dense outlined type=date')
                            p_number = ui.input('Número do protocolo').classes('w-full').props('dense outlined')
                            p_system = ui.select(SYSTEM_OPTIONS, label='Processo sistema', with_input=True).classes('w-full').props('dense outlined')
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
                            # Protocolos locais (salvos junto com o processo)
                            local_protocols = state['protocols'] or []
                            
                            # Protocolos vinculados (salvos separadamente, sincronização bidirecional)
                            linked_protocols = []
                            if state['is_editing'] and state['process_id']:
                                linked_protocols = get_protocols_by_process(state['process_id'])
                            
                            has_any = len(local_protocols) > 0 or len(linked_protocols) > 0
                            
                            if not has_any:
                                ui.label('Nenhum protocolo.').classes('text-gray-400 italic text-sm')
                                return
                            
                            # Exibe protocolos locais
                            for i, p in enumerate(local_protocols):
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
                                            ui.button(icon='edit', on_click=lambda idx=i: open_prot_dialog(idx)).props('flat dense size=sm color=primary')
                                            def rm_prot(idx=i): state['protocols'].pop(idx); render_protocols.refresh()
                                            ui.button(icon='delete', on_click=rm_prot).props('flat dense size=sm color=red')
                            
                            # Exibe protocolos vinculados externamente (somente leitura)
                            if linked_protocols:
                                if local_protocols:
                                    ui.separator().classes('my-3')
                                ui.label('📎 Protocolos Vinculados').classes('text-sm font-medium text-gray-600 mb-2')
                                
                                for lp in linked_protocols:
                                    with ui.card().classes('w-full p-2 mb-2').style('border-left: 3px solid #2196F3;'):
                                        with ui.row().classes('w-full justify-between items-start'):
                                            with ui.column().classes('gap-1 flex-grow'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label(lp.get('title', '-')).classes('font-medium text-sm')
                                                    ui.badge('vinculado').props('color=blue-4').classes('text-xs')
                                                date_str = format_date_br(lp.get('date')) if lp.get('date') else '-'
                                                number_str = f"Nº {lp.get('number')}" if lp.get('number') else ''
                                                system_str = lp.get('system', '') if lp.get('system') else ''
                                                info_parts = [part for part in [date_str, number_str, system_str] if part]
                                                ui.label(' • '.join(info_parts) if info_parts else '-').classes('text-xs text-gray-600')
                                                if lp.get('observations'):
                                                    ui.label(lp.get('observations')).classes('text-xs text-gray-500 mt-1')
                                                # Mostra outros vínculos
                                                other_cases = len(lp.get('case_ids', []))
                                                other_procs = len(lp.get('process_ids', [])) - 1  # -1 porque já está neste
                                                if other_cases > 0 or other_procs > 0:
                                                    links_info = []
                                                    if other_cases > 0:
                                                        links_info.append(f'{other_cases} caso(s)')
                                                    if other_procs > 0:
                                                        links_info.append(f'{other_procs} outro(s) processo(s)')
                                                    ui.label(f'Vinculado a: {", ".join(links_info)}').classes('text-xs text-blue-600 mt-1')
                                            ui.icon('link').classes('text-blue-400 text-lg')
                        render_protocols()

                    # --- TAB 7: SENHAS DE ACESSO ---
                    with ui.tab_panel(tab_access):
                        # Dialog de confirmação de exclusão
                        with ui.dialog() as delete_senha_dialog, ui.card().classes('p-4 w-96'):
                            ui.label('Confirmar exclusão').classes('text-lg font-bold mb-3')
                            ui.label('Deseja realmente excluir esta senha? Esta ação não pode ser desfeita.').classes('text-gray-700 mb-4')
                            delete_senha_id_ref = {'val': None}
                            
                            with ui.row().classes('w-full justify-end gap-2'):
                                ui.button('Cancelar', on_click=delete_senha_dialog.close).props('flat')
                                def confirm_delete_senha():
                                    pid = delete_senha_id_ref['val']
                                    if pid:
                                        success, message = delete_process_password(state['process_id'], pid)
                                        if success:
                                            ui.notify(message, type='positive')
                                            render_passwords.refresh()
                                        else:
                                            ui.notify(message, type='negative')
                                    delete_senha_dialog.close()
                                ui.button('Excluir', on_click=confirm_delete_senha).props('color=red')
                        
                        # Dialog para cadastrar/editar senha
                        with ui.dialog() as senha_dialog, ui.card().classes('p-4 w-[500px]'):
                            senha_title_label = ui.label('Nova senha').classes('text-lg font-bold mb-3')
                            
                            senha_titulo_input = ui.input('Título *', placeholder='Ex: Acesso ao sistema SEI').classes('w-full').props('dense outlined')
                            senha_usuario_input = ui.input('Usuário', placeholder='Nome de usuário para login').classes('w-full').props('dense outlined')
                            
                            # Campo de senha com toggle mostrar/ocultar
                            with ui.row().classes('w-full items-end gap-2'):
                                senha_password_input = ui.input('Senha *', placeholder='Senha para login', password=True).classes('flex-grow').props('dense outlined')
                                senha_toggle_btn = ui.button(icon='visibility_off', on_click=lambda: toggle_password_visibility()).props('flat dense').tooltip('Mostrar/ocultar senha')
                            
                            senha_link_input = ui.input('Link de acesso', placeholder='https://...').classes('w-full').props('dense outlined')
                            senha_obs_textarea = ui.textarea('Observações', placeholder='Notas adicionais...').classes('w-full').props('dense outlined rows=3')
                            
                            senha_id_ref = {'val': None}
                            senha_show_password = {'val': False}
                            
                            def toggle_password_visibility():
                                senha_show_password['val'] = not senha_show_password['val']
                                if senha_show_password['val']:
                                    senha_password_input.props(remove='password')
                                    senha_toggle_btn.props(remove='icon=visibility_off')
                                    senha_toggle_btn.props(add='icon=visibility')
                                    senha_toggle_btn.tooltip('Ocultar senha')
                                else:
                                    senha_password_input.props(add='password')
                                    senha_toggle_btn.props(remove='icon=visibility')
                                    senha_toggle_btn.props(add='icon=visibility_off')
                                    senha_toggle_btn.tooltip('Mostrar senha')
                            
                            def save_password():
                                if not senha_titulo_input.value or not senha_titulo_input.value.strip():
                                    ui.notify('Título é obrigatório!', type='warning')
                                    return
                                
                                if not senha_password_input.value or not senha_password_input.value.strip():
                                    ui.notify('Senha é obrigatória!', type='warning')
                                    return
                                
                                # Validar URL se fornecida
                                link = senha_link_input.value.strip()
                                if link and not (link.startswith('http://') or link.startswith('https://')):
                                    ui.notify('Link deve começar com http:// ou https://', type='warning')
                                    return
                                
                                if not state.get('process_id'):
                                    ui.notify('Processo não identificado. Salve o processo primeiro.', type='warning')
                                    return
                                
                                password_data = {
                                    'titulo': senha_titulo_input.value.strip(),
                                    'usuario': senha_usuario_input.value.strip() if senha_usuario_input.value else '',
                                    'senha': senha_password_input.value,
                                    'link_acesso': link if link else '',
                                    'observacoes': senha_obs_textarea.value.strip() if senha_obs_textarea.value else ''
                                }
                                
                                success, password_id, message = save_process_password(
                                    state['process_id'],
                                    password_data,
                                    senha_id_ref['val']
                                )
                                
                                if success:
                                    ui.notify(message, type='positive')
                                    senha_dialog.close()
                                    render_passwords.refresh()
                                else:
                                    ui.notify(message, type='negative')
                            
                            with ui.row().classes('w-full justify-end gap-2 mt-3'):
                                ui.button('Cancelar', on_click=senha_dialog.close).props('flat')
                                senha_save_btn = ui.button('Salvar', on_click=save_password).props('color=primary')
                            
                            def open_senha_dialog(password_id=None):
                                senha_id_ref['val'] = password_id
                                senha_show_password['val'] = False
                                senha_password_input.props(add='password')
                                senha_toggle_btn.props(remove='icon=visibility')
                                senha_toggle_btn.props(add='icon=visibility_off')
                                senha_toggle_btn.tooltip('Mostrar senha')
                                
                                if password_id:
                                    # Edição - carregar dados
                                    senhas = get_process_passwords(state.get('process_id', ''))
                                    senha_data = next((s for s in senhas if s.get('id') == password_id), None)
                                    if senha_data:
                                        senha_title_label.text = 'Editar senha'
                                        senha_save_btn.text = 'Salvar'
                                        senha_titulo_input.value = senha_data.get('titulo', '')
                                        senha_usuario_input.value = senha_data.get('usuario', '')
                                        senha_password_input.value = senha_data.get('senha', '')
                                        senha_link_input.value = senha_data.get('link_acesso', '')
                                        senha_obs_textarea.value = senha_data.get('observacoes', '')
                                    else:
                                        ui.notify('Senha não encontrada', type='warning')
                                        return
                                else:
                                    # Nova senha
                                    senha_title_label.text = 'Nova senha'
                                    senha_save_btn.text = 'Salvar'
                                    senha_titulo_input.value = ''
                                    senha_usuario_input.value = ''
                                    senha_password_input.value = ''
                                    senha_link_input.value = ''
                                    senha_obs_textarea.value = ''
                                
                                senha_dialog.open()
                        
                        # Header com botão de adicionar
                        with ui.row().classes('w-full justify-between items-center mb-4'):
                            ui.label('🔑 Senhas de acesso').classes('text-lg font-bold text-gray-800')
                            ui.button('+ Nova senha', icon='add', on_click=lambda: open_senha_dialog(None) if state.get('process_id') else ui.notify('Salve o processo primeiro para adicionar senhas', type='warning')).props('flat dense color=primary')
                        
                        @ui.refreshable
                        def render_passwords():
                            if not state.get('process_id'):
                                with ui.card().classes('w-full p-6 text-center'):
                                    ui.label('💡 Salve o processo primeiro para gerenciar senhas').classes('text-gray-500')
                                return
                            
                            senhas = get_process_passwords(state['process_id'])
                            
                            if not senhas:
                                with ui.card().classes('w-full p-6 text-center'):
                                    ui.label('Nenhuma senha cadastrada').classes('text-gray-400 italic')
                                return
                            
                            for senha in senhas:
                                senha_id = senha.get('id')
                                senha_show = {'val': False}
                                
                                with ui.card().classes('w-full p-4 mb-3').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                    # Título
                                    ui.label(senha.get('titulo', 'Sem título')).classes('text-base font-bold text-gray-800 mb-3')
                                    
                                    # Usuário
                                    if senha.get('usuario'):
                                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                                            ui.icon('person').classes('text-gray-500')
                                            ui.label(senha.get('usuario')).classes('text-sm text-gray-700 flex-grow')
                                            def copy_usuario(u=senha.get('usuario')):
                                                # Usar JSON.stringify para escapar corretamente
                                                import json
                                                u_json = json.dumps(u)
                                                ui.run_javascript(f'navigator.clipboard.writeText({u_json})')
                                                ui.notify('Usuário copiado!', type='positive')
                                            ui.button(icon='content_copy', on_click=copy_usuario).props('flat dense size=sm').tooltip('Copiar usuário')
                                    
                                    # Senha
                                    with ui.row().classes('w-full items-center gap-2 mb-2'):
                                        ui.icon('lock').classes('text-gray-500')
                                        senha_display_label = ui.label('••••••••').classes('text-sm text-gray-700 font-mono flex-grow')
                                        
                                        def toggle_senha_show():
                                            senha_show['val'] = not senha_show['val']
                                            if senha_show['val']:
                                                senha_display_label.text = senha.get('senha', '')
                                                toggle_senha_btn.props(remove='icon=visibility_off')
                                                toggle_senha_btn.props(add='icon=visibility')
                                                toggle_senha_btn.tooltip('Ocultar senha')
                                            else:
                                                senha_display_label.text = '••••••••'
                                                toggle_senha_btn.props(remove='icon=visibility')
                                                toggle_senha_btn.props(add='icon=visibility_off')
                                                toggle_senha_btn.tooltip('Mostrar senha')
                                        
                                        toggle_senha_btn = ui.button(icon='visibility_off', on_click=toggle_senha_show).props('flat dense size=sm').tooltip('Mostrar senha')
                                        
                                        def copy_senha(s=senha.get('senha')):
                                            # Usar JSON.stringify para escapar corretamente
                                            import json
                                            s_json = json.dumps(s)
                                            ui.run_javascript(f'navigator.clipboard.writeText({s_json})')
                                            ui.notify('Senha copiada!', type='positive')
                                        ui.button(icon='content_copy', on_click=copy_senha).props('flat dense size=sm').tooltip('Copiar senha')
                                    
                                    # Link de acesso
                                    if senha.get('link_acesso'):
                                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                                            ui.icon('link').classes('text-gray-500')
                                            link_url = senha.get('link_acesso')
                                            def open_link(l=link_url):
                                                ui.run_javascript(f'window.open("{l}", "_blank")')
                                            ui.link(link_url, target='_blank').classes('text-sm text-blue-600 hover:underline flex-grow')
                                            ui.button(icon='open_in_new', on_click=lambda l=link_url: open_link(l)).props('flat dense size=sm').tooltip('Abrir link')
                                    
                                    # Observações
                                    if senha.get('observacoes'):
                                        ui.label(senha.get('observacoes')).classes('text-xs text-gray-500 mt-2 italic')
                                    
                                    # Botões de ação
                                    with ui.row().classes('w-full justify-end gap-2 mt-3'):
                                        ui.button('Editar', icon='edit', on_click=lambda pid=senha_id: open_senha_dialog(pid)).props('flat dense size=sm color=primary')
                                        
                                        def delete_senha(pid=senha_id):
                                            delete_senha_id_ref['val'] = pid
                                            delete_senha_dialog.open()
                                        
                                        ui.button('Excluir', icon='delete', on_click=lambda pid=senha_id: delete_senha(pid)).props('flat dense size=sm color=red')
                        
                        render_passwords()

                    # --- TAB 8: SLACK ---
                    with ui.tab_panel(tab_slack):
                        ui.label('Integração com Slack em breve...').classes('text-gray-400 italic')

            # Footer Actions
            with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10').style('background: rgba(249, 250, 251, 0.95); border-radius: 8px 0 0 0;'):
                
                def do_delete():
                    if state['is_editing'] and state.get('process_id'):
                        process_title = delete_process(state['process_id'])
                        if process_title:
                            ui.notify(f'Processo "{process_title}" excluído!', type='positive')
                            dialog.close()
                            if on_success: 
                                from ...core import invalidate_cache
                                invalidate_cache('processes')
                                on_success()
                        else:
                            ui.notify('Erro ao excluir processo. Verifique se o processo existe.', type='negative')
                    else:
                        ui.notify('Não foi possível identificar o processo para exclusão.', type='warning')

                delete_btn = ui.button('EXCLUIR', icon='delete', on_click=do_delete).props('color=red').classes('hidden font-bold shadow-lg')

                def do_save():
                    # Importar logger
                    from ....utils.save_logger import SaveLogger
                    
                    # Validação antes de salvar
                    is_valid, msg = validate_process(
                        title_input.value, 
                        state['selected_cases'], 
                        state['selected_clients'],
                        parent_ids=state['parent_ids'],
                        current_process_id=state.get('process_id')
                    )
                    if not is_valid:
                        ui.notify(msg, type='warning')
                        return
                    
                    # Validação adicional: garante que clientes não seja None
                    selected_clients = state['selected_clients'] or []
                    if not isinstance(selected_clients, list):
                        selected_clients = []
                    
                    # Coletar TODOS os campos do formulário
                    p_data = build_process_data(
                        title=title_input.value, number=number_input.value, system=system_select.value,
                        link=link_input.value, nucleo=nucleo_select.value, area=area_select.value,
                        status=status_select.value, result=result_select.value, process_type=type_select.value,
                        data_abertura=data_abertura_input.value,
                        clients=selected_clients, opposing_parties=state['selected_opposing'],
                        other_parties=state['selected_others'], cases=state['selected_cases'],
                        relatory_facts=relatory_facts_input.value or '', relatory_timeline=relatory_timeline_input.value or '',
                        relatory_documents=relatory_documents_input.value or '',
                        strategy_objectives=objectives_input.value or '', legal_thesis=thesis_input.value or '',
                        strategy_observations=observations_input.value or '', scenarios=state['scenarios'],
                        protocols=state['protocols'],
                        access_lawyer=access_lawyer_granted.value, access_technicians=access_technicians_granted.value, 
                        access_client=access_client_granted.value,
                        access_lawyer_comment=access_lawyer_comment.value or '', 
                        access_technicians_comment=access_technicians_comment.value or '', 
                        access_client_comment=access_client_comment.value or '',
                        access_lawyer_requested=access_lawyer_requested.value,
                        access_technicians_requested=access_technicians_requested.value,
                        access_client_requested=access_client_requested.value,
                        parent_ids=state['parent_ids'],
                        area_total_discutida=area_total_discutida_input.value,
                        envolve_dano_app=envolve_dano_app_switch.value
                    )
                    
                    # Preserva o _id se estiver editando
                    documento_id = None
                    if state['is_editing'] and state['process_id']:
                        p_data['_id'] = state['process_id']
                        documento_id = state['process_id']
                    
                    # Compatibilidade: se houver apenas um parent_id, mantém também o campo antigo
                    if len(p_data.get('parent_ids', [])) == 1:
                        p_data['parent_id'] = p_data['parent_ids'][0]
                    else:
                        p_data['parent_id'] = None
                    
                    # Log antes de salvar
                    SaveLogger.log_save_attempt('processos', documento_id or 'novo', p_data)
                    
                    try:
                        idx = state['edit_index'] if state['is_editing'] else None
                        msg = save_process(p_data, idx)
                        
                        # Log de sucesso
                        SaveLogger.log_save_success('processos', documento_id or 'novo')
                        
                        ui.notify(msg, type='positive')
                        dialog.close()
                        if on_success: on_success()
                    except Exception as e:
                        # Log de erro
                        SaveLogger.log_save_error('processos', documento_id or 'novo', e)
                        ui.notify(f'Erro ao salvar processo: {str(e)}', type='negative')

                ui.button('SALVAR', icon='save', on_click=do_save).props('color=primary').classes('font-bold shadow-lg')

    def clear_form():
        title_input.value = ''; number_input.value = ''; link_input.value = ''
        type_select.value = 'Existente'; data_abertura_input.value = ''
        system_select.value = None; nucleo_select.value = 'Ambiental'
        area_select.value = None; status_select.value = 'Em andamento'; result_select.value = None
        envolve_dano_app_switch.value = False
        area_total_discutida_input.value = None
        # Relatório
        relatory_facts_input.value = ''; relatory_timeline_input.value = ''; relatory_documents_input.value = ''
        # Estratégia
        objectives_input.value = ''; thesis_input.value = ''; observations_input.value = ''
        
        # Acesso
        access_lawyer_requested.value = False; access_lawyer_granted.value = False
        access_technicians_requested.value = False; access_technicians_granted.value = False
        access_client_requested.value = False; access_client_granted.value = False
        access_lawyer_comment.value = ''; access_technicians_comment.value = ''; access_client_comment.value = ''
        
        parent_process_sel.value = None
        state['parent_ids'] = []
        refresh_parent_chips(parent_process_chips, state['parent_ids'])
        
        state['scenarios'] = []
        state['protocols'] = []
        state['selected_clients'] = []
        state['selected_opposing'] = []
        state['selected_others'] = []
        state['selected_cases'] = []
        
        refresh_chips(client_chips, state['selected_clients'], 'clients', get_clients_list())
        refresh_chips(opposing_chips, state['selected_opposing'], 'opposing', get_opposing_parties_list())
        refresh_chips(others_chips, state['selected_others'], 'others', get_opposing_parties_list())
        refresh_chips(cases_chips, state['selected_cases'], 'cases', None)
        render_scenarios.refresh()
        render_protocols.refresh()
        toggle_result()

    def open_modal(process_idx=None, parent_process_id=None):
        """
        Abre o modal de processo.
        
        Args:
            process_idx: Índice do processo para edição (None para novo processo)
            parent_process_id: ID do processo pai para criar desdobramento (None para processo independente)
        """
        clear_form()
        
        # Atualizar opções de casos sempre que o modal abre
        case_options_ref['val'] = [c['title'] for c in get_cases_list()]
        if case_options_ref['val']:
            cases_sel.options = case_options_ref['val']
        else:
            cases_sel.options = ['-']
        
        # PRIMEIRO: Carregar dados do processo se estiver editando
        if process_idx is not None:
            # EDIT MODE
            processes = get_processes_list()
            
            # Validação do índice
            if not isinstance(process_idx, int) or process_idx < 0 or process_idx >= len(processes):
                ui.notify(f'Erro: Processo não encontrado (índice {process_idx})', type='negative')
                return
            
            state['is_editing'] = True
            state['edit_index'] = process_idx
            dialog_title.text = 'EDITAR PROCESSO'
            delete_btn.classes(remove='hidden')
            
            # Load Data
            p = processes[process_idx]
            # Preserva o _id do processo para salvar corretamente no Firestore
            state['process_id'] = p.get('_id')
            
            # Log de carregamento
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            processo_id = state['process_id'] or 'SEM_ID'
            print(f"[{timestamp}] [PROCESSOS] [CARREGAR] ID: {processo_id}")
            print(f"[{timestamp}] [PROCESSOS] [CARREGAR] Título: {p.get('title', 'Sem título')}")
            print(f"[{timestamp}] [PROCESSOS] [CARREGAR] Campos disponíveis: {list(p.keys())}")
            print(f"[{timestamp}] [PROCESSOS] [CARREGAR] Total de campos: {len(p)}")
            
            # Carregar parent_ids (novo formato) ou migrar de parent_id (antigo)
            parent_ids = p.get('parent_ids', [])
            if not parent_ids and p.get('parent_id'):
                # Migração: se tem parent_id antigo mas não tem parent_ids, converte
                parent_ids = [p.get('parent_id')]
            state['parent_ids'] = list(parent_ids) if parent_ids else []
            
            # Campos básicos
            title_input.value = p.get('title', '') or ''
            number_input.value = p.get('number', '') or ''
            link_input.value = p.get('link', '') or ''
            type_select.value = p.get('process_type', 'Existente') or 'Existente'
            data_abertura_input.value = p.get('data_abertura', '') or ''
            system_select.value = p.get('system') or None
            nucleo_select.value = p.get('nucleo', 'Ambiental') or 'Ambiental'
            area_select.value = p.get('area') or None
            status_select.value = p.get('status', 'Em andamento') or 'Em andamento'
            envolve_dano_app_switch.value = p.get('envolve_dano_app', False) or False
            area_total_discutida_input.value = p.get('area_total_discutida') if p.get('area_total_discutida') is not None else None
            result_select.value = p.get('result') or None
            
            # Relatório
            relatory_facts_input.value = p.get('relatory_facts', '') or ''
            relatory_timeline_input.value = p.get('relatory_timeline', '') or ''
            relatory_documents_input.value = p.get('relatory_documents', '') or ''
            
            # Estratégia
            objectives_input.value = p.get('strategy_objectives', '') or ''
            thesis_input.value = p.get('legal_thesis', '') or ''
            observations_input.value = p.get('strategy_observations', '') or ''
            
            # Acesso
            access_lawyer_requested.value = p.get('access_lawyer_requested', False)
            access_lawyer_granted.value = p.get('access_lawyer_granted', False) or p.get('access_lawyer', False)
            access_technicians_requested.value = p.get('access_technicians_requested', False)
            access_technicians_granted.value = p.get('access_technicians_granted', False) or p.get('access_technicians', False)
            access_client_requested.value = p.get('access_client_requested', False)
            access_client_granted.value = p.get('access_client_granted', False) or p.get('access_client', False)
            access_lawyer_comment.value = p.get('access_lawyer_comment', '') or ''
            access_technicians_comment.value = p.get('access_technicians_comment', '') or ''
            access_client_comment.value = p.get('access_client_comment', '') or ''
            
            # Listas (garantir que são listas)
            state['scenarios'] = list(p.get('scenarios', [])) if p.get('scenarios') else []
            state['protocols'] = list(p.get('protocols', [])) if p.get('protocols') else []
            state['selected_clients'] = list(p.get('clients', [])) if p.get('clients') else []
            
            # CORREÇÃO: Normaliza opposing_parties para usar nome_exibicao em vez de nome_completo
            # Converte valores antigos (nome_completo) para nome_exibicao ao carregar
            opposing_raw = list(p.get('opposing_parties', [])) if p.get('opposing_parties') else []
            opposing_list = get_opposing_parties_list()
            state['selected_opposing'] = [
                get_short_name(opp, opposing_list) for opp in opposing_raw
            ] if opposing_raw else []
            
            # CORREÇÃO: Normaliza other_parties também
            others_raw = list(p.get('other_parties', [])) if p.get('other_parties') else []
            state['selected_others'] = [
                get_short_name(other, opposing_list) for other in others_raw
            ] if others_raw else []
            
            state['selected_cases'] = list(p.get('cases', [])) if p.get('cases') else []
            
            # Atualizar chips e renderizações
            refresh_chips(client_chips, state['selected_clients'], 'clients', get_clients_list())
            refresh_chips(opposing_chips, state['selected_opposing'], 'opposing', get_opposing_parties_list())
            refresh_chips(others_chips, state['selected_others'], 'others', get_opposing_parties_list())
            refresh_chips(cases_chips, state['selected_cases'], 'cases', None)
            refresh_parent_chips(parent_process_chips, state['parent_ids'])
            render_scenarios.refresh()
            render_protocols.refresh()
            toggle_result()
        else:
            # NEW MODE
            state['is_editing'] = False
            state['edit_index'] = None
            state['process_id'] = None
            
            # Verificar se é um desdobramento
            if parent_process_id:
                dialog_title.text = 'NOVO DESDOBRAMENTO DE PROCESSO'
                # Pré-configurar o processo pai
                state['parent_ids'] = [parent_process_id]
            else:
                dialog_title.text = 'NOVO PROCESSO'
                state['parent_ids'] = []
            
            delete_btn.classes(add='hidden')
        
        # DEPOIS: Carregar opções de processo pai (agora que temos os dados corretos)
        all_procs = get_processes_list()
        parent_options = []
        current_id = state.get('process_id')  # Agora tem o ID correto
        selected_parent_display = None
        
        for p in all_procs:
            proc_id = p.get('_id')
            if proc_id and proc_id != current_id:  # Não incluir o próprio processo
                title = p.get('title') or p.get('number') or 'Sem título'
                number = p.get('number', '')
                display = f"{title}" + (f" ({number})" if number else "") + f" | {proc_id}"
                parent_options.append(display)
                
                # Se este é o processo pai pré-selecionado, guardar o display
                if parent_process_id and proc_id == parent_process_id:
                    selected_parent_display = display
        
        parent_process_sel.options = parent_options if parent_options else ['— Nenhum (processo raiz) —']
        parent_process_sel.update()
        
        # Se há um processo pai pré-selecionado, atualizar chips (não precisa setar o seletor)
        if parent_process_id and state.get('parent_ids'):
            refresh_parent_chips(parent_process_chips, state['parent_ids'])
        
        dialog.open()

    return dialog, open_modal


def expand_to_technical_prompt(user_text: str) -> str:
    """
    Natural-language → Technical Prompt Generator
    
    Converte descrições em português em prompts técnicos completos e acionáveis para o Cursor.
    
    Args:
        user_text: Descrição do problema em linguagem natural (ex: "não estou conseguindo abrir o modal de editar processo")
    
    Returns:
        Prompt técnico completo com contexto e instruções detalhadas
    """
    return f"""

You must FIX the described issue inside the TAQUES ERP (NiceGUI + Firebase) codebase.



CONTEXT:

- The system uses NiceGUI for all UI components (dialogs, modals, selects, tables).

- Data operations use Firebase.

- Follow existing patterns: save_case(), get_cases_list(), deduplicate_cases_by_title().

- Maintain UI style: w-full, bg-primary, shadow-md.



TASK:

The user reports: "{user_text}"



You must:

1. Locate all code sections responsible for opening and handling the corresponding modal.

2. Identify why the modal does not open (event, missing reference, missing dialog instance, wrong callback, etc.).

3. Produce the necessary code changes (UI + backend if needed) to fix the problem completely.

4. Ensure the modal opens, loads data, shows correct fields, and saves updates.

5. Refactor anything that is breaking the flow.

6. After the fix, ensure no other page referencing this modal breaks.



DELIVERABLE:

Return ONLY the corrected code and file changes required to make the modal open and function perfectly, with no commentary.

""".strip()
