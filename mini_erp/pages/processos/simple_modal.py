"""
simple_modal.py - Modal simples e sincronizado para criar e editar processos.

Modal único usado tanto para criar quanto para editar processos,
com interface limpa e campos essenciais.
"""

from nicegui import ui
from typing import Callable, Optional, List, Dict, Any
from ...core import get_cases_list, get_clients_list, get_opposing_parties_list, get_processes_list
from .models import AREA_OPTIONS, SYSTEM_OPTIONS, STATUS_OPTIONS
from .database import save_process
from .business_logic import validate_process, build_process_data


def create_simple_process_modal(on_success: Optional[Callable] = None):
    """
    Cria modal simples para criar/editar processos.
    
    Args:
        on_success: Callback executado após salvar com sucesso
    
    Returns:
        Tupla (dialog, open_function) onde:
        - dialog: Instância do ui.dialog
        - open_function: Função para abrir o modal, aceita process_id opcional
    """
    
    # Estado do modal
    state = {
        'is_editing': False,
        'edit_index': None,
        'selected_clients': [],
        'selected_opposing': [],
        'selected_cases': []
    }
    
    # Criar dialog
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl p-6'):
        
        # Título do modal
        modal_title = ui.label('Novo Processo').classes('text-2xl font-bold text-gray-800 mb-6')
        
        # Campos do formulário
        with ui.column().classes('w-full gap-4'):
            
            # Título do processo
            title_input = ui.input('Título do Processo').classes('w-full').props('outlined dense')
            
            # Linha: Área e Sistema
            with ui.row().classes('w-full gap-4'):
                area_select = ui.select(
                    AREA_OPTIONS, 
                    label='Área',
                    value=None
                ).classes('flex-1').props('outlined dense')
                
                system_select = ui.select(
                    SYSTEM_OPTIONS, 
                    label='Sistema Processual',
                    value=None
                ).classes('flex-1').props('outlined dense')
            
            # Linha: Número e Status
            with ui.row().classes('w-full gap-4'):
                number_input = ui.input('Número do Processo').classes('flex-1').props('outlined dense')
                
                status_select = ui.select(
                    STATUS_OPTIONS,
                    label='Status',
                    value='Em andamento'
                ).classes('flex-1').props('outlined dense')
            
            # Link
            with ui.row().classes('w-full gap-2 items-end'):
                link_input = ui.input('Link do Processo').classes('flex-grow').props('outlined dense')
                
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
            
            # Divisor
            ui.separator().classes('my-2')
            
            # === CASOS VINCULADOS ===
            ui.label('Casos Vinculados').classes('text-sm font-semibold text-gray-700')
            
            with ui.row().classes('w-full gap-2 items-end'):
                case_select = ui.select(
                    [],
                    label='Selecione um caso',
                    with_input=True
                ).classes('flex-grow').props('outlined dense')
                
                def add_case():
                    val = case_select.value
                    if val and val not in state['selected_cases']:
                        state['selected_cases'].append(val)
                        refresh_case_chips()
                        case_select.value = None
                
                ui.button(icon='add', on_click=add_case).props('flat color=primary')
            
            # Container para chips de casos
            case_chips_container = ui.row().classes('w-full gap-1 flex-wrap min-h-8')
            
            def refresh_case_chips():
                case_chips_container.clear()
                with case_chips_container:
                    for case in state['selected_cases']:
                        with ui.badge(case, color='blue').classes('text-sm'):
                            def remove_case(c=case):
                                if c in state['selected_cases']:
                                    state['selected_cases'].remove(c)
                                    refresh_case_chips()
                            
                            ui.button(
                                icon='close',
                                on_click=remove_case
                            ).props('flat dense round size=xs color=white')
            
            # Divisor
            ui.separator().classes('my-2')
            
            # === CLIENTES ===
            ui.label('Clientes').classes('text-sm font-semibold text-gray-700')
            
            with ui.row().classes('w-full gap-2 items-end'):
                client_select = ui.select(
                    [],
                    label='Selecione um cliente',
                    with_input=True
                ).classes('flex-grow').props('outlined dense')
                
                def add_client():
                    val = client_select.value
                    if val and val not in state['selected_clients']:
                        # Extrai o nome completo (remove parte entre parênteses)
                        full_name = val.split(' (')[0] if '(' in val else val
                        
                        # CORREÇÃO: Busca o nome de exibição ao invés de salvar nome completo
                        clients = get_clients_list()
                        display_name = full_name  # fallback
                        
                        for client in clients:
                            client_full_name = client.get('full_name') or client.get('name', '')
                            if client_full_name == full_name:
                                display_name = get_display_name(client)
                                break
                        
                        state['selected_clients'].append(display_name)
                        refresh_client_chips()
                        client_select.value = None
                
                ui.button(icon='add', on_click=add_client).props('flat color=primary')
            
            # Container para chips de clientes
            client_chips_container = ui.row().classes('w-full gap-1 flex-wrap min-h-8')
            
            def refresh_client_chips():
                client_chips_container.clear()
                with client_chips_container:
                    for client in state['selected_clients']:
                        with ui.badge(client, color='green').classes('text-sm'):
                            def remove_client(c=client):
                                if c in state['selected_clients']:
                                    state['selected_clients'].remove(c)
                                    refresh_client_chips()
                            
                            ui.button(
                                icon='close',
                                on_click=remove_client
                            ).props('flat dense round size=xs color=white')
            
            # Divisor
            ui.separator().classes('my-2')
            
            # === PARTE CONTRÁRIA ===
            ui.label('Parte Contrária').classes('text-sm font-semibold text-gray-700')
            
            with ui.row().classes('w-full gap-2 items-end'):
                opposing_select = ui.select(
                    [],
                    label='Selecione parte contrária',
                    with_input=True
                ).classes('flex-grow').props('outlined dense')
                
                def add_opposing():
                    val = opposing_select.value
                    if val and val not in state['selected_opposing']:
                        # Extrai o nome completo (remove parte entre parênteses)
                        full_name = val.split(' (')[0] if '(' in val else val
                        
                        # CORREÇÃO: Busca o nome de exibição ao invés de salvar nome completo
                        opposing_parties = get_opposing_parties_list()
                        display_name = full_name  # fallback
                        
                        for op in opposing_parties:
                            op_full_name = op.get('full_name') or op.get('name', '')
                            if op_full_name == full_name:
                                display_name = get_display_name(op)
                                break
                        
                        state['selected_opposing'].append(display_name)
                        refresh_opposing_chips()
                        opposing_select.value = None
                
                ui.button(icon='add', on_click=add_opposing).props('flat color=red')
            
            # Container para chips de parte contrária
            opposing_chips_container = ui.row().classes('w-full gap-1 flex-wrap min-h-8')
            
            def refresh_opposing_chips():
                opposing_chips_container.clear()
                with opposing_chips_container:
                    for opposing in state['selected_opposing']:
                        with ui.badge(opposing, color='red').classes('text-sm'):
                            def remove_opposing(o=opposing):
                                if o in state['selected_opposing']:
                                    state['selected_opposing'].remove(o)
                                    refresh_opposing_chips()
                            
                            ui.button(
                                icon='close',
                                on_click=remove_opposing
                            ).props('flat dense round size=xs color=white')
        
        # Botões de ação
        with ui.row().classes('w-full justify-end gap-2 mt-6'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')
            
            def save_action():
                # Validação
                is_valid, msg = validate_process(
                    title_input.value,
                    state['selected_cases'],
                    state['selected_clients']
                )
                
                if not is_valid:
                    ui.notify(msg, type='warning')
                    return
                
                # Construir dados do processo
                process_data = build_process_data(
                    title=title_input.value or '',
                    number=number_input.value or '',
                    system=system_select.value,
                    link=link_input.value or '',
                    nucleo='Ambiental',  # Valor padrão
                    area=area_select.value,
                    status=status_select.value,
                    result=None,
                    process_type='Existente',  # Valor padrão
                    data_abertura=None,  # Campo não disponível no modal simples
                    clients=state['selected_clients'].copy(),
                    opposing_parties=state['selected_opposing'].copy(),
                    other_parties=[],
                    cases=state['selected_cases'].copy(),
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
                    access_client_comment=''
                )
                
                # Salvar
                idx = state['edit_index'] if state['is_editing'] else None
                msg = save_process(process_data, idx)
                ui.notify(msg, type='positive')
                
                dialog.close()
                
                # Callback de sucesso
                if on_success:
                    on_success()
            
            ui.button('Salvar', icon='save', on_click=save_action).props('color=primary')
    
    def clear_form():
        """Limpa todos os campos do formulário."""
        title_input.value = ''
        number_input.value = ''
        link_input.value = ''
        area_select.value = None
        system_select.value = None
        status_select.value = 'Em andamento'
        
        state['selected_clients'] = []
        state['selected_opposing'] = []
        state['selected_cases'] = []
        
        refresh_client_chips()
        refresh_opposing_chips()
        refresh_case_chips()
    
    def load_options():
        """Carrega opções dinâmicas do sistema."""
        # Casos
        cases = get_cases_list()
        case_options = [c['title'] for c in cases if c.get('title')]
        case_select.options = case_options
        
        # Clientes - usando regra centralizada de exibição
        from ...core import get_display_name
        
        clients = get_clients_list()
        client_options = []
        for c in clients:
            name = c.get('full_name') or c.get('name', '')
            display_name = get_display_name(c)
            if display_name and display_name != name:
                client_options.append(f"{name} ({display_name})")
            else:
                client_options.append(name)
        client_select.options = sorted(client_options)
        
        # Parte contrária - usando regra centralizada de exibição
        opposing = get_opposing_parties_list()
        opposing_options = []
        for o in opposing:
            name = o.get('full_name') or o.get('name', '')
            display_name = get_display_name(o)
            if display_name and display_name != name:
                opposing_options.append(f"{name} ({display_name})")
            else:
                opposing_options.append(name)
        opposing_select.options = sorted(opposing_options)
    
    def open_modal(process_idx: Optional[int] = None):
        """
        Abre o modal para criar ou editar processo.
        
        Args:
            process_idx: Se fornecido, abre em modo de edição para esse processo
        """
        clear_form()
        load_options()
        
        if process_idx is not None:
            # MODO EDIÇÃO
            processes = get_processes_list()
            
            # Validação do índice
            if not isinstance(process_idx, int) or process_idx < 0 or process_idx >= len(processes):
                ui.notify(f'Erro: Processo não encontrado (índice {process_idx})', type='negative')
                return
            
            state['is_editing'] = True
            state['edit_index'] = process_idx
            modal_title.text = 'Editar Processo'
            
            # Carregar dados do processo
            p = processes[process_idx]
            
            title_input.value = p.get('title', '') or ''
            number_input.value = p.get('number', '') or ''
            link_input.value = p.get('link', '') or ''
            area_select.value = p.get('area')
            system_select.value = p.get('system')
            status_select.value = p.get('status', 'Em andamento')
            
            # Listas
            state['selected_clients'] = list(p.get('clients', [])) if p.get('clients') else []
            state['selected_opposing'] = list(p.get('opposing_parties', [])) if p.get('opposing_parties') else []
            state['selected_cases'] = list(p.get('cases', [])) if p.get('cases') else []
            
            # Atualizar chips
            refresh_client_chips()
            refresh_opposing_chips()
            refresh_case_chips()
        else:
            # MODO NOVO
            state['is_editing'] = False
            state['edit_index'] = None
            modal_title.text = 'Novo Processo'
        
        dialog.open()
    
    return dialog, open_modal

