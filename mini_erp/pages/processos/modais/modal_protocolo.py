"""
protocol_dialog.py - Modal para cadastro de Protocolos Independentes.

Protocolos podem ser vinculados a múltiplos casos e/ou processos.
Sincronização bidirecional com a aba de protocolos do processo.
"""

from nicegui import ui
from ....core import (
    PRIMARY_COLOR, get_cases_list, get_processes_list,
    save_protocol, delete_protocol, get_protocols_list
)
from ..models import SYSTEM_OPTIONS


def render_protocol_dialog(on_success=None):
    """
    Factory function para criar o modal de Protocolo Independente.
    
    Args:
        on_success: Callback após salvar/deletar (ex: refresh lista)
    
    Returns:
        tuple: (dialog_component, open_function)
    """
    
    # State
    state = {
        'is_editing': False,
        'protocol_id': None,
        'selected_cases': [],
        'selected_processes': [],
        'all_cases': [],
        'all_processes': [],
        'all_case_options': [],  # Cache de todas as opções de casos
        'all_process_options': []  # Cache de todas as opções de processos
    }
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl p-0').style('max-height: 90vh; overflow-y: auto;'):
        # Header fixo
        with ui.row().classes('w-full items-center justify-between px-4 py-3 sticky top-0 z-10').style(f'background: {PRIMARY_COLOR};'):
            dialog_title = ui.label('NOVO PROTOCOLO').classes('text-white font-bold text-lg')
            ui.button(icon='close', on_click=dialog.close).props('flat round color=white')
        
        # Content
        with ui.column().classes('w-full p-6 gap-4 bg-gray-50'):
            
            # Seção: Dados do Protocolo
            with ui.card().classes('w-full p-4').style('border: 1px solid #e5e7eb;'):
                ui.label('📋 Dados do Protocolo').classes('text-lg font-bold mb-3')
                
                with ui.column().classes('w-full gap-3'):
                    p_title = ui.input('Título/Descrição *').classes('w-full').props('outlined dense')
                    p_title.tooltip('Ex: Petição Inicial, Recurso, Defesa Administrativa')
                    
                    with ui.row().classes('w-full gap-4'):
                        with ui.input('Data', placeholder='DD/MM/AAAA').classes('flex-1').props('outlined dense mask="##/##/####"') as p_date:
                            with ui.menu().props('no-parent-event') as date_menu:
                                date_picker = ui.date(mask='DD/MM/YYYY')
                                date_picker.on('update:model-value', lambda e: (
                                    p_date.set_value(e.args if e.args else ''),
                                    date_menu.close()
                                ))
                                with ui.row().classes('justify-end'):
                                    ui.button('Fechar', on_click=date_menu.close).props('flat')
                            with p_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', date_menu.open).classes('cursor-pointer')
                        
                        p_number = ui.input('Número do Protocolo').classes('flex-1').props('outlined dense')
                    
                    p_system = ui.select(SYSTEM_OPTIONS, label='Sistema', with_input=True).classes('w-full').props('outlined dense')
                    
                    # Campo de Link
                    with ui.input('Link do Protocolo').classes('w-full').props('outlined dense') as p_link:
                        p_link.tooltip('URL do protocolo no sistema externo (ex: https://...)')
                        with p_link.add_slot('prepend'):
                            ui.icon('link').classes('text-gray-500')
                    
                    p_obs = ui.textarea('Observações').classes('w-full').props('outlined dense rows=2')
            
            # Seção: Vínculos
            with ui.card().classes('w-full p-4').style('border: 1px solid #e5e7eb;'):
                ui.label('🔗 Vínculos').classes('text-lg font-bold mb-3')
                ui.label('Vincule este protocolo a um ou mais casos e/ou processos:').classes('text-sm text-gray-600 mb-2')
                
                # Container para chips de casos selecionados
                cases_chips_container = ui.row().classes('w-full gap-1 flex-wrap min-h-8 mb-2')
                
                # Funções auxiliares para chips
                def refresh_case_chips():
                    cases_chips_container.clear()
                    with cases_chips_container:
                        for case_title in state['selected_cases']:
                            with ui.badge(case_title[:40] + '...' if len(case_title) > 40 else case_title).classes('pr-1').style('background-color: #9C27B0; color: white;'):
                                def remove_case(ct=case_title):
                                    if ct in state['selected_cases']:
                                        state['selected_cases'].remove(ct)
                                        refresh_case_chips()
                                ui.button(icon='close', on_click=remove_case).props('flat dense round size=xs color=white')
                
                def refresh_process_chips():
                    processes_chips_container.clear()
                    with processes_chips_container:
                        for proc_key in state['selected_processes']:
                            display = proc_key.split(' | ')[0] if ' | ' in proc_key else proc_key
                            display = display[:40] + '...' if len(display) > 40 else display
                            with ui.badge(display).classes('pr-1').style('background-color: #2196F3; color: white;'):
                                def remove_proc(pk=proc_key):
                                    if pk in state['selected_processes']:
                                        state['selected_processes'].remove(pk)
                                        refresh_process_chips()
                                ui.button(icon='close', on_click=remove_proc).props('flat dense round size=xs color=white')
                
                # Função de filtro para casos
                def filter_cases(e):
                    """Filtra opções de casos baseado no texto digitado."""
                    search_text = (e.args or '').lower().strip()
                    if not search_text:
                        # Mostra todas as opções
                        cases_search.options = state['all_case_options']
                    else:
                        # Filtra opções que contêm o texto
                        filtered = [opt for opt in state['all_case_options'] if search_text in opt.lower()]
                        cases_search.options = filtered if filtered else ['Nenhum caso encontrado']
                    cases_search.update()
                
                # Função de filtro para processos
                def filter_processes(e):
                    """Filtra opções de processos baseado no texto digitado."""
                    search_text = (e.args or '').lower().strip()
                    if not search_text:
                        # Mostra todas as opções
                        processes_search.options = state['all_process_options']
                    else:
                        # Filtra opções que contêm o texto (busca no título ou número)
                        filtered = [opt for opt in state['all_process_options'] if search_text in opt.lower()]
                        processes_search.options = filtered if filtered else ['Nenhum processo encontrado']
                    processes_search.update()
                
                # Campo de busca de casos
                with ui.column().classes('w-full gap-2'):
                    ui.label('Casos').classes('text-sm font-medium text-gray-700')
                    with ui.row().classes('w-full gap-2 items-center'):
                        cases_search = ui.select(
                            options=[],
                            label='Pesquisar casos...',
                            with_input=True,
                            on_change=lambda e: None  # Placeholder, será usado para seleção
                        ).classes('flex-grow').props('outlined dense use-input input-debounce="0"')
                        cases_search.on('update:input-value', filter_cases)
                        cases_search.tooltip('Digite para filtrar casos')
                        
                        def add_case():
                            val = cases_search.value
                            if val and val not in ['Nenhum caso encontrado', '-'] and val not in state['selected_cases']:
                                state['selected_cases'].append(val)
                                cases_search.value = None
                                # Restaura opções completas
                                cases_search.options = state['all_case_options']
                                refresh_case_chips()
                            elif val and val in state['selected_cases']:
                                ui.notify('Caso já adicionado!', type='warning')
                        
                        ui.button(icon='add', on_click=add_case).props('flat dense round').style('color: #9C27B0;')
                
                ui.separator().classes('my-2')
                
                # Container para chips de processos selecionados
                processes_chips_container = ui.row().classes('w-full gap-1 flex-wrap min-h-8 mb-2')
                
                # Campo de busca de processos
                with ui.column().classes('w-full gap-2'):
                    ui.label('Processos').classes('text-sm font-medium text-gray-700')
                    with ui.row().classes('w-full gap-2 items-center'):
                        processes_search = ui.select(
                            options=[],
                            label='Pesquisar processos...',
                            with_input=True,
                            on_change=lambda e: None  # Placeholder
                        ).classes('flex-grow').props('outlined dense use-input input-debounce="0"')
                        processes_search.on('update:input-value', filter_processes)
                        processes_search.tooltip('Digite para filtrar processos por título ou número')
                        
                        def add_process():
                            val = processes_search.value
                            if val and val not in ['Nenhum processo encontrado', '-'] and val not in state['selected_processes']:
                                state['selected_processes'].append(val)
                                processes_search.value = None
                                # Restaura opções completas
                                processes_search.options = state['all_process_options']
                                refresh_process_chips()
                            elif val and val in state['selected_processes']:
                                ui.notify('Processo já adicionado!', type='warning')
                        
                        ui.button(icon='add', on_click=add_process).props('flat dense round').style('color: #2196F3;')
        
        # Footer Actions - fixo na parte inferior
        with ui.row().classes('w-full justify-between gap-2 p-4 bg-white border-t sticky bottom-0'):
            delete_btn = ui.button('EXCLUIR', icon='delete', on_click=lambda: do_delete()).props('color=red').classes('hidden')
            
            with ui.row().classes('gap-2 ml-auto'):
                ui.button('CANCELAR', on_click=dialog.close).props('flat')
                ui.button('SALVAR', icon='save', on_click=lambda: do_save()).props('color=primary')
    
    def do_save():
        """Salva o protocolo no Firestore."""
        if not p_title.value or not p_title.value.strip():
            ui.notify('Título é obrigatório!', type='warning')
            return
        
        if not state['selected_cases'] and not state['selected_processes']:
            ui.notify('Vincule a pelo menos um caso ou processo!', type='warning')
            return
        
        try:
            # Extrai IDs dos processos selecionados (formato: "Título | _id")
            process_ids = []
            for p in state['selected_processes']:
                if ' | ' in p:
                    process_ids.append(p.split(' | ')[-1])  # Pega o último item após |
                else:
                    # Tenta encontrar pelo título
                    for proc in state['all_processes']:
                        if proc.get('title') == p:
                            process_ids.append(proc.get('_id'))
                            break
            
            # Extrai slugs dos casos selecionados
            case_ids = []
            for c in state['selected_cases']:
                for caso in state['all_cases']:
                    if caso.get('title') == c:
                        case_ids.append(caso.get('slug') or caso.get('_id'))
                        break
            
            protocol_data = {
                'title': p_title.value.strip(),
                'date': p_date.value or '',
                'number': p_number.value or '',
                'system': p_system.value or '',
                'link': p_link.value or '',
                'observations': p_obs.value or '',
                'case_ids': case_ids,
                'process_ids': process_ids
            }
            
            # Se editando, preserva _id
            doc_id = state['protocol_id'] if state['is_editing'] else None
            
            save_protocol(protocol_data, doc_id=doc_id)
            
            msg = 'Protocolo atualizado!' if state['is_editing'] else 'Protocolo cadastrado com sucesso!'
            ui.notify(msg, type='positive')
            dialog.close()
            
            if on_success:
                on_success()
                
        except Exception as e:
            ui.notify(f'Erro ao salvar: {str(e)}', type='negative')
            print(f'[PROTOCOL] Erro ao salvar: {e}')
    
    def do_delete():
        """Exclui o protocolo do Firestore."""
        if state['is_editing'] and state['protocol_id']:
            try:
                delete_protocol(state['protocol_id'])
                ui.notify('Protocolo excluído!', type='info')
                dialog.close()
                if on_success:
                    on_success()
            except Exception as e:
                ui.notify(f'Erro ao excluir: {str(e)}', type='negative')
    
    def clear_form():
        """Limpa todos os campos do formulário."""
        p_title.value = ''
        p_date.value = ''
        p_number.value = ''
        p_system.value = None
        p_link.value = ''
        p_obs.value = ''
        state['selected_cases'] = []
        state['selected_processes'] = []
        cases_chips_container.clear()
        processes_chips_container.clear()
    
    def open_modal(protocol_id=None):
        """Abre o modal para criar ou editar protocolo."""
        clear_form()
        
        # Carrega dados de casos (formato "Título | slug" para identificar)
        state['all_cases'] = get_cases_list()
        print(f"[DEBUG] get_cases_list retornou: {len(state['all_cases'])} casos")
        state['all_case_options'] = [
            f"{c['title']} | {c.get('slug') or c.get('_id')}"
            for c in state['all_cases']
            if c.get('title') and (c.get('slug') or c.get('_id'))
        ]
        print(f"[DEBUG] all_case_options: {state['all_case_options'][:3] if state['all_case_options'] else 'VAZIO'}")
        cases_search.options = state['all_case_options'] if state['all_case_options'] else ['-']
        cases_search.update()
        
        # Carrega dados de processos (formato: "Título | _id" para identificação única)
        state['all_processes'] = get_processes_list()
        print(f"[DEBUG] get_processes_list retornou: {len(state['all_processes'])} processos")
        state['all_process_options'] = []
        for p in state['all_processes']:
            if p.get('_id'):
                title = p.get('title') or p.get('number') or 'Sem título'
                number = p.get('number', '')
                # Formato: "Título (número) | _id" para exibição e identificação
                display = f"{title}" + (f" ({number})" if number else "") + f" | {p.get('_id')}"
                state['all_process_options'].append(display)
        print(f"[DEBUG] all_process_options: {state['all_process_options'][:3] if state['all_process_options'] else 'VAZIO'}")
        processes_search.options = state['all_process_options'] if state['all_process_options'] else ['-']
        processes_search.update()
        
        if protocol_id:
            # EDIT MODE
            state['is_editing'] = True
            state['protocol_id'] = protocol_id
            dialog_title.text = 'EDITAR PROTOCOLO'
            delete_btn.classes(remove='hidden')
            
            # Carrega dados do protocolo existente
            protocols = get_protocols_list()
            protocol = next((p for p in protocols if p.get('_id') == protocol_id), None)
            
            if protocol:
                p_title.value = protocol.get('title', '')
                p_date.value = protocol.get('date', '')
                p_number.value = protocol.get('number', '')
                p_system.value = protocol.get('system')
                p_link.value = protocol.get('link', '')
                p_obs.value = protocol.get('observations', '')
                
                # Carrega casos vinculados
                case_ids = protocol.get('case_ids', [])
                state['selected_cases'] = []
                for slug in case_ids:
                    for caso in state['all_cases']:
                        if caso.get('slug') == slug or caso.get('_id') == slug:
                            state['selected_cases'].append(caso.get('title'))
                            break
                
                # Carrega processos vinculados
                process_ids = protocol.get('process_ids', [])
                state['selected_processes'] = []
                for pid in process_ids:
                    for proc in state['all_processes']:
                        if proc.get('_id') == pid:
                            title = proc.get('title', 'Sem título')
                            number = proc.get('number', '')
                            display = f"{title}" + (f" ({number})" if number else "") + f" | {pid}"
                            state['selected_processes'].append(display)
                            break
                
                # Atualiza chips
                refresh_case_chips()
                refresh_process_chips()
        else:
            # NEW MODE
            state['is_editing'] = False
            state['protocol_id'] = None
            dialog_title.text = 'NOVO PROTOCOLO'
            delete_btn.classes(add='hidden')
        
        dialog.open()
    
    # Atualiza chips iniciais (vazios)
    refresh_case_chips()
    refresh_process_chips()
    
    return dialog, open_modal
