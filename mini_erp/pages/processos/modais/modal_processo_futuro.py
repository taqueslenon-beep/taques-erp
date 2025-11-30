"""
future_process_dialog.py - Modal para criação de Processos Futuros.

Modal simplificado para criar processos futuros/previstos com campos específicos.
"""

from nicegui import ui
from datetime import datetime
from ....core import (
    PRIMARY_COLOR, get_cases_list, get_clients_list, get_opposing_parties_list, 
    get_processes_list, get_display_name
)
from ..models import (
    SYSTEM_OPTIONS, NUCLEO_OPTIONS, AREA_OPTIONS, PROCESSES_TABLE_CSS
)
from ..utils import get_short_name, format_option_for_search, get_option_value
from ..business_logic import validate_process, build_process_data
from ..database import save_process


def make_required_label(text: str) -> str:
    """Adiciona asterisco ao final do label para campos obrigatórios."""
    return f'{text} *'


def render_future_process_dialog(on_success=None):
    """
    Factory function para criar o Modal de Processo Futuro.
    
    Args:
        on_success: Callback function para executar após salvar com sucesso.
    
    Returns:
        tuple: (dialog_component, open_function)
    """
    
    # Inject CSS styles
    ui.add_head_html(f'<style>{PROCESSES_TABLE_CSS}</style>')
    
    # State
    state = {
        'parent_ids': [],  # Lista de IDs dos processos pais (vínculos)
        'selected_clients': [],
        'selected_opposing': [],
        'selected_others': [],
        'selected_cases': []
    }
    
    # Referência para opções de casos
    case_options_ref = {'val': [c['title'] for c in get_cases_list()]}
    
    # Referências para componentes do formulário (será preenchido dentro do dialog)
    refs = {}

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden relative').style('height: 80vh; max-height: 80vh;'):
        with ui.row().classes('w-full h-full gap-0'):
            # Sidebar
            with ui.column().classes('h-full shrink-0 justify-between').style(f'width: 170px; background: {PRIMARY_COLOR};'):
                with ui.column().classes('w-full gap-0'):
                    ui.label('NOVO PROCESSO FUTURO').classes('text-xs font-medium px-3 py-2 text-white/80 uppercase tracking-wide')
                    
                    with ui.tabs().props('vertical dense no-caps inline-label').classes('w-full process-sidebar-tabs') as tabs:
                        tab_basic = ui.tab('Dados básicos', icon='description')
                        tab_legal = ui.tab('Dados jurídicos', icon='gavel')
                        tab_description = ui.tab('Descrição', icon='article')
            
            # Content
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_basic).classes('w-full h-full p-4 bg-transparent'):
                    
                    # --- TAB 1: DADOS BÁSICOS ---
                    with ui.tab_panel(tab_basic):
                        with ui.column().classes('w-full gap-4'):
                            
                            # Mapeamento de cores para tags
                            TAG_COLORS = {
                                'clients': '#4CAF50',
                                'opposing': '#F44336',
                                'others': '#2196F3',
                                'cases': '#9C27B0'
                            }

                            # Helpers para chips
                            def refresh_chips(container, items, tag_type, source_list):
                                container.clear()
                                safe_source = source_list or []
                                chip_color = TAG_COLORS.get(tag_type, '#6B7280')
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
                                    else:
                                        ui.notify('Este item já está adicionado!', type='warning')
                                elif val and val in list_ref:
                                    ui.notify('Este item já está adicionado!', type='warning')
                            
                            # Função para atualizar chips de processos pais
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
                            
                            def remove_parent_process(list_ref, process_id, container):
                                if process_id in list_ref:
                                    list_ref.remove(process_id)
                                    refresh_parent_chips(container, list_ref)
                            
                            def add_parent_process(select, list_ref, container):
                                val = select.value
                                if val and val != '— Nenhum (processo raiz) —' and val != '-':
                                    if ' | ' in val:
                                        process_id = val.split(' | ')[-1].strip()
                                        if process_id in list_ref:
                                            ui.notify('Este processo pai já está adicionado!', type='warning')
                                            return
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
                                    title_input = ui.input(make_required_label('Título do Processo')).classes('w-full').props('outlined dense')
                                    title_input.tooltip('Nome descritivo do processo futuro. Ex: AIA 450566 - DESMATAMENTO - IBAMA')
                                    
                                    # Data Prevista (similar à data de abertura)
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
                                    
                                    date_selector_state = {
                                        'type': 'full',
                                        'day': '01',
                                        'month': '01',
                                        'year': str(datetime.now().year)
                                    }
                                    
                                    with ui.row().classes('items-center gap-2'):
                                        data_prevista_input = ui.input(
                                            'Data Prevista', 
                                            placeholder='Ex: 2025, 09/2025, 05/09/2025'
                                        ).classes('w-56').props('outlined dense')
                                        data_prevista_input.tooltip(
                                            'Formatos aceitos:\n'
                                            '• Ano: 2025\n'
                                            '• Mês/Ano: 09/2025\n'
                                            '• Completa: 05/09/2025'
                                        )
                                        data_prevista_input.validation = {'Formato inválido': validate_approximate_date}
                                        
                                        with ui.menu().props('anchor="bottom left" self="top left"') as date_menu:
                                            with ui.card().classes('p-4 w-72'):
                                                ui.label('📅 Data Prevista').classes('text-base font-bold mb-2')
                                                
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
                                                
                                                year_opts = sorted([str(y) for y in range(2024, 2051)], reverse=True)
                                                year_sel = ui.select(
                                                    options=year_opts,
                                                    label='Ano',
                                                    value=str(datetime.now().year + 1)
                                                ).classes('w-full mb-3').props('outlined dense')
                                                
                                                def on_type_change():
                                                    t = date_type_sel.value
                                                    day_sel.visible = (t == 'full')
                                                    month_sel.visible = (t in ['full', 'month_year'])
                                                
                                                date_type_sel.on_value_change(on_type_change)
                                                
                                                def apply_selected_date():
                                                    t = date_type_sel.value
                                                    if t == 'full':
                                                        data_prevista_input.value = f"{day_sel.value}/{month_sel.value}/{year_sel.value}"
                                                    elif t == 'month_year':
                                                        data_prevista_input.value = f"{month_sel.value}/{year_sel.value}"
                                                    else:
                                                        data_prevista_input.value = year_sel.value
                                                    date_menu.close()
                                                
                                                with ui.row().classes('w-full justify-end gap-2'):
                                                    ui.button('Cancelar', on_click=date_menu.close).props('flat dense')
                                                    ui.button('OK', on_click=apply_selected_date).props('color=primary dense')
                                        
                                        ui.button(icon='calendar_today', on_click=date_menu.open).props('flat dense').style('color: #1976D2;')

                            # SEÇÃO 2 - Partes Envolvidas
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('👥 Partes Envolvidas').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-2'):
                                    clients_list = get_clients_list()
                                    clients_options = [''] + [format_option_for_search(p) for p in clients_list]
                                    
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        clients_sel = ui.select(
                                            clients_options, 
                                            label='Clientes', 
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined use-input filter-input')
                                        ui.button(icon='add', on_click=lambda: add_item(clients_sel, state['selected_clients'], clients_chips, 'clients', clients_list)).props('flat dense').style('color: #4CAF50;')
                                    clients_chips = ui.column().classes('w-full')
                                    
                                    opposing_list = get_opposing_parties_list()
                                    opposing_options = [''] + [format_option_for_search(p) for p in opposing_list]
                                    
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        opposing_sel = ui.select(
                                            opposing_options, 
                                            label='Parte Contrária', 
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined use-input filter-input')
                                        ui.button(icon='add', on_click=lambda: add_item(opposing_sel, state['selected_opposing'], opposing_chips, 'opposing', opposing_list)).props('flat dense').style('color: #F44336;')
                                    opposing_chips = ui.column().classes('w-full')
                                    
                                    others_list = get_clients_list() + get_opposing_parties_list()
                                    others_options = [''] + [format_option_for_search(p) for p in others_list]
                                    
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        others_sel = ui.select(
                                            others_options, 
                                            label='Outros Envolvidos', 
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined use-input filter-input')
                                        ui.button(icon='add', on_click=lambda: add_item(others_sel, state['selected_others'], others_chips, 'others', others_list)).props('flat dense').style('color: #2196F3;')
                                    others_chips = ui.column().classes('w-full')

                            # SEÇÃO 3 - Vínculos
                            with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                ui.label('🔗 Vínculos').classes('text-lg font-bold mb-3')
                                with ui.column().classes('w-full gap-2'):
                                    parent_process_chips = ui.column().classes('w-full')
                                    
                                    all_procs = get_processes_list()
                                    process_options = ['— Nenhum (processo raiz) —'] + [
                                        f"{p.get('title', 'Sem título')} | {p.get('_id')}" 
                                        for p in all_procs if p.get('_id')
                                    ]
                                    
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        parent_process_sel = ui.select(
                                            options=process_options,
                                            label='Processos Pais (opcional)',
                                            with_input=True
                                        ).classes('flex-grow').props('dense outlined use-input filter-input')
                                        ui.button(icon='add', on_click=lambda: add_parent_process(parent_process_sel, state['parent_ids'], parent_process_chips)).props('flat dense').style('color: #FF9800;')
                                    
                                    with ui.row().classes('w-full gap-2 items-center'):
                                        cases_sel = ui.select(case_options_ref['val'] or ['-'], label='Casos Vinculados', with_input=True).classes('flex-grow').props('dense outlined')
                                        ui.button(icon='add', on_click=lambda: add_item(cases_sel, state['selected_cases'], cases_chips, 'cases', None)).props('flat dense').style('color: #9C27B0;')
                                    cases_chips = ui.column().classes('w-full')

                    # --- TAB 2: DADOS JURÍDICOS ---
                    with ui.tab_panel(tab_legal):
                        with ui.column().classes('w-full gap-4'):
                            system_select = ui.select(SYSTEM_OPTIONS, label='Sistema Processual').classes('w-full').props('outlined dense')
                            nucleo_select = ui.select(NUCLEO_OPTIONS, label='Núcleo', value='Ambiental').classes('w-full').props('outlined dense')
                            area_select = ui.select(AREA_OPTIONS, label='Área').classes('w-full').props('outlined dense')
                            
                            # Status fixo como "Futuro/Previsto"
                            ui.label('Status: Futuro/Previsto').classes('text-base font-semibold text-gray-700 p-3 bg-gray-100 rounded')

                    # --- TAB 3: DESCRIÇÃO ---
                    with ui.tab_panel(tab_description):
                        with ui.column().classes('w-full gap-4'):
                            ui.label('Descrição do Processo Futuro').classes('text-base font-semibold text-gray-700')
                            description_input = ui.editor(placeholder='Descreva o possível processo futuro...').classes('w-full').style('height: 300px')
                            
                            # Probabilidade
                            PROBABILITY_OPTIONS = ['Muito alta', 'Alta', 'Média', 'Baixa', 'Muito baixa']
                            probability_select = ui.select(
                                PROBABILITY_OPTIONS, 
                                label='Probabilidade de acontecer'
                            ).classes('w-full').props('outlined dense')
                            probability_select.tooltip('Probabilidade estimada de que este processo futuro venha a acontecer')

            # Footer Actions
            with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10').style('background: rgba(249, 250, 251, 0.95); border-radius: 8px 0 0 0;'):
                
                def do_save():
                    is_valid, msg = validate_process(
                        title_input.value, 
                        state['selected_cases'], 
                        state['selected_clients'],
                        parent_ids=state['parent_ids'],
                        current_process_id=None,
                        process_type='Futuro'
                    )
                    if not is_valid:
                        ui.notify(msg, type='warning')
                        return
                    
                    # Status fixo para processos futuros
                    status_futuro = 'Futuro/Previsto'
                    
                    p_data = build_process_data(
                        title=title_input.value, 
                        number='',  # Processos futuros não têm número ainda
                        system=system_select.value, 
                        link='',  # Processos futuros não têm link ainda
                        nucleo=nucleo_select.value, 
                        area=area_select.value,
                        status=status_futuro, 
                        result=None, 
                        process_type='Futuro',
                        data_abertura=data_prevista_input.value,  # Usa data prevista como data_abertura
                        clients=state['selected_clients'], 
                        opposing_parties=state['selected_opposing'],
                        other_parties=state['selected_others'], 
                        cases=state['selected_cases'],
                        relatory_facts='', 
                        relatory_timeline='', 
                        relatory_documents='',
                        strategy_objectives='', 
                        legal_thesis='', 
                        strategy_observations='',
                        scenarios=[], 
                        protocols=[],
                        access_lawyer=False, 
                        access_technicians=False, 
                        access_client=False,
                        access_lawyer_comment='', 
                        access_technicians_comment='', 
                        access_client_comment='',
                        access_lawyer_requested=False,
                        access_technicians_requested=False,
                        access_client_requested=False,
                        parent_ids=state['parent_ids']
                    )
                    
                    # Adiciona campos específicos de processo futuro
                    p_data['future_description'] = description_input.value
                    p_data['future_probability'] = probability_select.value
                    
                    msg = save_process(p_data, None)
                    ui.notify(msg)
                    dialog.close()
                    if on_success: 
                        from ...core import invalidate_cache
                        invalidate_cache('processes')
                        on_success()

                ui.button('SALVAR', icon='save', on_click=do_save).props('color=primary').classes('font-bold shadow-lg')
                
                # Armazenar referências para acesso na função open_modal
                refs['title_input'] = title_input
                refs['data_prevista_input'] = data_prevista_input
                refs['system_select'] = system_select
                refs['nucleo_select'] = nucleo_select
                refs['area_select'] = area_select
                refs['description_input'] = description_input
                refs['probability_select'] = probability_select
                refs['clients_chips'] = clients_chips
                refs['opposing_chips'] = opposing_chips
                refs['others_chips'] = others_chips
                refs['cases_chips'] = cases_chips
                refs['parent_process_chips'] = parent_process_chips
                refs['parent_process_sel'] = parent_process_sel

    def open_modal():
        """Abre o modal de processo futuro."""
        # Limpar formulário
        refs['title_input'].value = ''
        refs['data_prevista_input'].value = ''
        refs['system_select'].value = None
        refs['nucleo_select'].value = 'Ambiental'
        refs['area_select'].value = None
        refs['description_input'].value = ''
        refs['probability_select'].value = None
        
        state['parent_ids'] = []
        state['selected_clients'] = []
        state['selected_opposing'] = []
        state['selected_others'] = []
        state['selected_cases'] = []
        
        # Atualizar opções de casos
        case_options_ref['val'] = [c['title'] for c in get_cases_list()]
        
        # Atualizar opções de processos
        all_procs = get_processes_list()
        process_options = ['— Nenhum (processo raiz) —'] + [
            f"{p.get('title', 'Sem título')} | {p.get('_id')}" 
            for p in all_procs if p.get('_id')
        ]
        refs['parent_process_sel'].options = process_options
        
        # Limpar chips
        refs['clients_chips'].clear()
        refs['opposing_chips'].clear()
        refs['others_chips'].clear()
        refs['cases_chips'].clear()
        refs['parent_process_chips'].clear()
        
        dialog.open()

    return dialog, open_modal

