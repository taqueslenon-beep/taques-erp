"""
Aba de Dados Básicos do modal de processo (Visão Geral).
"""
from nicegui import ui
from datetime import datetime
from typing import Dict, Any, List, Callable
from mini_erp.core import get_display_name
from .helpers import (
    make_required_label, get_short_name, format_option_for_search,
    get_option_value
)
from ..constants import TIPOS_PROCESSO
from mini_erp.models.prioridade import PRIORIDADE_PADRAO, CODIGOS_PRIORIDADE


def render_aba_dados_basicos(
    state: Dict[str, Any],
    dados: Dict[str, Any],
    todas_pessoas: List[Dict[str, Any]],
    todos_casos: List[Dict[str, Any]],
    usuarios_internos: List[Dict[str, Any]],
    processos_pais: List[Dict[str, Any]],
    envolvidos_e_parceiros: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Renderiza a aba de Dados Básicos do modal.
    
    Args:
        state: Estado do modal
        dados: Dados do processo (se edição)
        todas_pessoas: Lista de todas as pessoas (clientes)
        todos_casos: Lista de todos os casos
        usuarios_internos: Lista de usuários internos já carregada
        processos_pais: Lista de processos pais já carregada
        envolvidos_e_parceiros: Lista de envolvidos e parceiros para Parte Contrária e Outros Envolvidos
        
    Returns:
        Dicionário com referências aos campos criados
    """
    # Fallback para compatibilidade
    if envolvidos_e_parceiros is None:
        envolvidos_e_parceiros = []
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
    
    # Helper para processos pais (usa lista já carregada)
    def refresh_parent_chips(container, processo_pai_id):
        container.clear()
        if not processo_pai_id:
            return
        
        proc = next((p for p in processos_pais if p.get('_id') == processo_pai_id), None)
        
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
    
    with ui.column().classes('w-full gap-4'):
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
                
                # Prioridade
                prioridade_select = ui.select(
                    CODIGOS_PRIORIDADE,
                    label='Prioridade',
                    value=dados.get('prioridade', PRIORIDADE_PADRAO)
                ).classes('w-full').props('outlined dense')
                
                # Responsável pelo Processo (usa lista já carregada)
                responsavel_options = [''] + [u.get('nome', u.get('email', '')) for u in usuarios_internos]
                
                # Determina valor inicial do responsável
                responsavel_val_inicial = dados.get('responsavel_nome', '') or dados.get('responsavel', '')
                # Se for UID, converte para nome
                if responsavel_val_inicial and responsavel_val_inicial not in [u.get('nome', '') for u in usuarios_internos]:
                    usuario_resp = next((u for u in usuarios_internos if u.get('uid') == responsavel_val_inicial), None)
                    if usuario_resp:
                        responsavel_val_inicial = usuario_resp.get('nome', '')
                
                responsavel_select = ui.select(
                    options=responsavel_options,
                    label='Responsável pelo Processo',
                    value=responsavel_val_inicial
                ).classes('w-full').props('outlined dense clearable')
        
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
                    
                    # Parte Contrária (usa envolvidos e parceiros, não clientes)
                    opposing_options = [format_option_for_search(p) for p in envolvidos_e_parceiros]
                    with ui.column().classes('flex-1 gap-2'):
                        with ui.row().classes('w-full gap-2 items-center'):
                            opposing_sel = ui.select(
                                opposing_options or ['— Nenhum envolvido/parceiro cadastrado —'],
                                label='Parte Contrária',
                                with_input=True
                            ).classes('flex-grow').props('dense outlined')
                            ui.button(
                                icon='add',
                                on_click=lambda: add_item(opposing_sel, state['selected_opposing'], opposing_chips, 'opposing', envolvidos_e_parceiros)
                            ).props('flat dense').style('color: #F44336;')
                        opposing_chips = ui.column().classes('w-full')
                
                # Outros Envolvidos (usa envolvidos e parceiros, não clientes)
                others_options = [format_option_for_search(p) for p in envolvidos_e_parceiros]
                with ui.column().classes('w-full gap-2'):
                    with ui.row().classes('w-full gap-2 items-center'):
                        others_sel = ui.select(
                            others_options or ['— Nenhum envolvido/parceiro cadastrado —'],
                            label='Outros Envolvidos',
                            with_input=True
                        ).classes('flex-grow').props('dense outlined')
                        ui.button(
                            icon='add',
                            on_click=lambda: add_item(others_sel, state['selected_others'], others_chips, 'others', envolvidos_e_parceiros)
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
    
    # Retorna referências aos campos
    return {
        'title_input': title_input,
        'number_input': number_input,
        'link_input': link_input,
        'type_select': type_select,
        'data_abertura_input': data_abertura_input,
        'prioridade_select': prioridade_select,
        'responsavel_select': responsavel_select,
        'client_sel': client_sel,
        'opposing_sel': opposing_sel,
        'others_sel': others_sel,
        'cases_sel': cases_sel,
        'parent_process_sel': parent_process_sel,
        'client_chips': client_chips,
        'opposing_chips': opposing_chips,
        'others_chips': others_chips,
        'cases_chips': cases_chips,
        'parent_process_chips': parent_process_chips,
        'refresh_chips': refresh_chips,
        'refresh_parent_chips': refresh_parent_chips,
    }

