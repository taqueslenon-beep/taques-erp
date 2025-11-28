from nicegui import ui
from datetime import datetime
from ...core import PRIMARY_COLOR, get_cases_list, get_clients_list, get_opposing_parties_list, get_processes_list, format_date_br
from .models import (
    PROCESS_TYPE_OPTIONS, SYSTEM_OPTIONS, NUCLEO_OPTIONS, AREA_OPTIONS,
    STATUS_OPTIONS, RESULT_OPTIONS, SCENARIO_TYPE_OPTIONS,
    SCENARIO_STATUS_OPTIONS, SCENARIO_IMPACT_OPTIONS, SCENARIO_CHANCE_OPTIONS,
    PROCESSES_TABLE_CSS
)
from .utils import (
    get_short_name, format_option_for_search, get_option_value,
    get_scenario_type_style, get_scenario_status_icon,
    get_scenario_impact_icon, get_scenario_chance_icon
)
from .business_logic import (
    validate_process, should_show_result_field, build_process_data
)
from .database import save_process, delete_process

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
                        tab_strategy = ui.tab('Estratégia', icon='lightbulb')
                        tab_scenarios = ui.tab('Cenários', icon='analytics')
                        tab_protocols = ui.tab('Protocolos', icon='history')
                        tab_slack = ui.tab('Slack', icon='tag')
            
            # Content
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_basic).classes('w-full h-full p-4 bg-transparent'):
                    
                    # --- TAB 1: DADOS BÁSICOS ---
                    with ui.tab_panel(tab_basic):
                        with ui.column().classes('w-full gap-2'):
                            with ui.row().classes('w-full gap-2'):
                                title_input = ui.input('Título do Processo').classes('flex-grow').props('outlined dense')
                                number_input = ui.input('Número do Processo').classes('w-48').props('outlined dense')
                            
                            link_input = ui.input('Link do Processo').classes('w-full').props('outlined dense')
                            
                            type_select = ui.select(PROCESS_TYPE_OPTIONS, label='Tipo de processo', value='Existente').classes('w-full').props('outlined dense')

                            # Lists Helpers
                            def refresh_chips(container, items, color, source_list):
                                container.clear()
                                safe_source = source_list or []
                                with container:
                                    with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                        for item in items:
                                            short = get_short_name(item, safe_source) if safe_source else item
                                            with ui.badge(short, color=color).classes('pr-1'):
                                                ui.button(icon='close', on_click=lambda i=item: remove_item(items, i, container, color, source_list)).props('flat dense round size=xs color=white')

                            def remove_item(list_ref, item, container, color, source_list):
                                if item in list_ref:
                                    list_ref.remove(item)
                                    refresh_chips(container, list_ref, color, source_list)

                            def add_item(select, list_ref, container, color, source_list):
                                val = select.value
                                if val and val != '-' and val not in list_ref:
                                    full_name = get_option_value(val, source_list) if source_list else val
                                    if full_name not in list_ref:
                                        list_ref.append(full_name)
                                        select.value = None
                                        refresh_chips(container, list_ref, color, source_list)
                                    else:
                                        ui.notify('Este item já está adicionado!', type='warning')
                                elif val and val in list_ref:
                                    ui.notify('Este item já está adicionado!', type='warning')

                            # Clients
                            client_options = [format_option_for_search(c) for c in get_clients_list()]
                            with ui.row().classes('w-full gap-4'):
                                with ui.column().classes('flex-1 gap-1'):
                                    with ui.row().classes('w-full gap-1 items-end'):
                                        client_sel = ui.select(client_options or ['-'], label='Clientes', with_input=True).classes('flex-grow').props('dense outlined')
                                        ui.button(icon='add', on_click=lambda: add_item(client_sel, state['selected_clients'], client_chips, 'primary', get_clients_list())).props('flat dense color=primary')
                                    client_chips = ui.column().classes('w-full')

                                # Opposing
                                opposing_options = [format_option_for_search(op) for op in get_opposing_parties_list()]
                                with ui.column().classes('flex-1 gap-1'):
                                    with ui.row().classes('w-full gap-1 items-end'):
                                        opposing_sel = ui.select(opposing_options or ['-'], label='Parte Contrária', with_input=True).classes('flex-grow').props('dense outlined')
                                        ui.button(icon='add', on_click=lambda: add_item(opposing_sel, state['selected_opposing'], opposing_chips, 'red', get_opposing_parties_list())).props('flat dense color=red')
                                    opposing_chips = ui.column().classes('w-full')

                            # Others & Cases
                            with ui.row().classes('w-full gap-4'):
                                with ui.column().classes('flex-1 gap-1'):
                                    with ui.row().classes('w-full gap-1 items-end'):
                                        others_sel = ui.select(opposing_options or ['-'], label='Outros Envolvidos', with_input=True).classes('flex-grow').props('dense outlined')
                                        ui.button(icon='add', on_click=lambda: add_item(others_sel, state['selected_others'], others_chips, 'purple', get_opposing_parties_list())).props('flat dense color=purple')
                                    others_chips = ui.column().classes('w-full')
                                
                                with ui.column().classes('flex-1 gap-1'):
                                    with ui.row().classes('w-full gap-1 items-end'):
                                        cases_sel = ui.select(case_options_ref['val'] or ['-'], label='Casos Vinculados', with_input=True).classes('flex-grow').props('dense outlined')
                                        ui.button(icon='add', on_click=lambda: add_item(cases_sel, state['selected_cases'], cases_chips, 'primary', None)).props('flat dense color=primary')
                                    cases_chips = ui.column().classes('w-full')

                    # --- TAB 2: DADOS JURÍDICOS ---
                    with ui.tab_panel(tab_legal):
                        with ui.column().classes('w-full gap-4'):
                            system_select = ui.select(SYSTEM_OPTIONS, label='Sistema Processual').classes('w-full')
                            nucleo_select = ui.select(NUCLEO_OPTIONS, label='Núcleo', value='Ambiental').classes('w-full')
                            area_select = ui.select(AREA_OPTIONS, label='Área').classes('w-full')
                            
                            status_select = ui.select(STATUS_OPTIONS, label='Status', value='Em andamento').classes('w-full')
                            
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

                    # --- TAB 3: ESTRATÉGIA ---
                    with ui.tab_panel(tab_strategy):
                        with ui.column().classes('w-full gap-5'):
                            ui.label('Objetivos').classes('text-sm font-semibold text-gray-700')
                            objectives_input = ui.textarea(placeholder='Descreva os objetivos...').props('outlined autogrow rows=4').classes('w-full')
                            
                            ui.label('Teses a serem trabalhadas').classes('text-sm font-semibold text-gray-700')
                            thesis_input = ui.textarea(placeholder='Descreva as teses...').props('outlined autogrow rows=4').classes('w-full')
                            
                            ui.label('Observações').classes('text-sm font-semibold text-gray-700')
                            observations_input = ui.textarea(placeholder='Observações...').props('outlined autogrow rows=4').classes('w-full')

                    # --- TAB 4: CENÁRIOS ---
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

                    # --- TAB 5: PROTOCOLOS ---
                    with ui.tab_panel(tab_protocols):
                        with ui.dialog() as prot_dialog, ui.card().classes('p-4 w-96'):
                            ui.label('Novo Protocolo').classes('text-lg font-bold mb-2')
                            p_title = ui.input('Título').classes('w-full').props('dense outlined')
                            p_date = ui.input('Data').classes('w-full').props('dense outlined type=date')
                            p_link = ui.input('Link').classes('w-full').props('dense outlined')
                            p_by = ui.input('Feito por').classes('w-full').props('dense outlined')
                            
                            def add_protocol():
                                if p_title.value:
                                    state['protocols'].append({'title': p_title.value, 'date': p_date.value, 'link': p_link.value, 'by': p_by.value})
                                    prot_dialog.close()
                                    render_protocols.refresh()
                                    p_title.value = ''; p_date.value = ''; p_link.value = ''; p_by.value = ''

                            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                                ui.button('Cancelar', on_click=prot_dialog.close).props('flat')
                                ui.button('Adicionar', on_click=add_protocol).props('color=primary')

                        ui.button('+ Novo Protocolo', on_click=prot_dialog.open).props('flat dense color=primary')
                        
                        @ui.refreshable
                        def render_protocols():
                            if not state['protocols']:
                                ui.label('Nenhum protocolo.').classes('text-gray-400 italic text-sm')
                                return
                            for i, p in enumerate(state['protocols']):
                                with ui.card().classes('w-full p-2 mb-2'):
                                    with ui.row().classes('w-full justify-between'):
                                        with ui.column().classes('gap-0'):
                                            ui.label(p['title']).classes('font-medium text-sm')
                                            ui.label(f"{format_date_br(p.get('date'))} • {p.get('by', '-')}")
                                        with ui.row():
                                            if p.get('link'):
                                                ui.button(icon='open_in_new', on_click=lambda l=p['link']: ui.navigate.to(l, new_tab=True)).props('flat dense size=sm color=blue')
                                            def rm_prot(idx=i): state['protocols'].pop(idx); render_protocols.refresh()
                                            ui.button(icon='delete', on_click=rm_prot).props('flat dense size=sm color=red')
                        render_protocols()

                    # --- TAB 6: SLACK ---
                    with ui.tab_panel(tab_slack):
                        ui.label('Integração com Slack em breve...').classes('text-gray-400 italic')

            # Footer Actions
            with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10').style('background: rgba(249, 250, 251, 0.95); border-radius: 8px 0 0 0;'):
                
                def do_delete():
                    if state['is_editing'] and state['edit_index'] is not None:
                        delete_process(state['edit_index'])
                        ui.notify('Processo excluído!')
                        dialog.close()
                        if on_success: on_success()

                delete_btn = ui.button('EXCLUIR', icon='delete', on_click=do_delete).props('color=red').classes('hidden font-bold shadow-lg')

                def do_save():
                    is_valid, msg = validate_process(title_input.value, state['selected_cases'], state['selected_clients'])
                    if not is_valid:
                        ui.notify(msg, type='warning')
                        return
                    
                    p_data = build_process_data(
                        title=title_input.value, number=number_input.value, system=system_select.value,
                        link=link_input.value, nucleo=nucleo_select.value, area=area_select.value,
                        status=status_select.value, result=result_select.value, process_type=type_select.value,
                        clients=state['selected_clients'], opposing_parties=state['selected_opposing'],
                        other_parties=state['selected_others'], cases=state['selected_cases'],
                        strategy_objectives=objectives_input.value, legal_thesis=thesis_input.value,
                        strategy_observations=observations_input.value, scenarios=state['scenarios'],
                        protocols=state['protocols'],
                        access_lawyer=False, access_technicians=False, access_client=False,
                        access_lawyer_comment='', access_technicians_comment='', access_client_comment=''
                    )
                    
                    # Preserva o _id se estiver editando
                    if state['is_editing'] and state['process_id']:
                        p_data['_id'] = state['process_id']
                    
                    idx = state['edit_index'] if state['is_editing'] else None
                    msg = save_process(p_data, idx)
                    ui.notify(msg)
                    dialog.close()
                    if on_success: on_success()

                ui.button('SALVAR', icon='save', on_click=do_save).props('color=primary').classes('font-bold shadow-lg')

    def clear_form():
        title_input.value = ''; number_input.value = ''; link_input.value = ''
        type_select.value = 'Existente'; system_select.value = None; nucleo_select.value = 'Ambiental'
        area_select.value = None; status_select.value = 'Em andamento'; result_select.value = None
        objectives_input.value = ''; thesis_input.value = ''; observations_input.value = ''
        
        state['scenarios'] = []
        state['protocols'] = []
        state['selected_clients'] = []
        state['selected_opposing'] = []
        state['selected_others'] = []
        state['selected_cases'] = []
        
        refresh_chips(client_chips, state['selected_clients'], 'primary', get_clients_list())
        refresh_chips(opposing_chips, state['selected_opposing'], 'red', get_opposing_parties_list())
        refresh_chips(others_chips, state['selected_others'], 'purple', get_opposing_parties_list())
        refresh_chips(cases_chips, state['selected_cases'], 'primary', None)
        render_scenarios.refresh()
        render_protocols.refresh()
        toggle_result()

    def open_modal(process_idx=None):
        clear_form()
        
        # Atualizar opções de casos sempre que o modal abre
        case_options_ref['val'] = [c['title'] for c in get_cases_list()]
        if case_options_ref['val']:
            cases_sel.options = case_options_ref['val']
        else:
            cases_sel.options = ['-']
        
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
            
            # Campos básicos
            title_input.value = p.get('title', '') or ''
            number_input.value = p.get('number', '') or ''
            link_input.value = p.get('link', '') or ''
            type_select.value = p.get('process_type', 'Existente') or 'Existente'
            system_select.value = p.get('system') or None
            nucleo_select.value = p.get('nucleo', 'Ambiental') or 'Ambiental'
            area_select.value = p.get('area') or None
            status_select.value = p.get('status', 'Em andamento') or 'Em andamento'
            result_select.value = p.get('result') or None
            
            # Estratégia
            objectives_input.value = p.get('strategy_objectives', '') or ''
            thesis_input.value = p.get('legal_thesis', '') or ''
            observations_input.value = p.get('strategy_observations', '') or ''
            
            # Listas (garantir que são listas)
            state['scenarios'] = list(p.get('scenarios', [])) if p.get('scenarios') else []
            state['protocols'] = list(p.get('protocols', [])) if p.get('protocols') else []
            state['selected_clients'] = list(p.get('clients', [])) if p.get('clients') else []
            state['selected_opposing'] = list(p.get('opposing_parties', [])) if p.get('opposing_parties') else []
            state['selected_others'] = list(p.get('other_parties', [])) if p.get('other_parties') else []
            state['selected_cases'] = list(p.get('cases', [])) if p.get('cases') else []
            
            # Atualizar chips e renderizações
            refresh_chips(client_chips, state['selected_clients'], 'primary', get_clients_list())
            refresh_chips(opposing_chips, state['selected_opposing'], 'red', get_opposing_parties_list())
            refresh_chips(others_chips, state['selected_others'], 'purple', get_opposing_parties_list())
            refresh_chips(cases_chips, state['selected_cases'], 'primary', None)
            render_scenarios.refresh()
            render_protocols.refresh()
            toggle_result()
        else:
            # NEW MODE
            state['is_editing'] = False
            state['edit_index'] = None
            state['process_id'] = None
            dialog_title.text = 'NOVO PROCESSO'
            delete_btn.classes(add='hidden')
        
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
