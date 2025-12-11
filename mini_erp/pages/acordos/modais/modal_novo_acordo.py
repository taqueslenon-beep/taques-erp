"""
modal_novo_acordo.py - Modal para criar novo acordo.
"""

from nicegui import ui
from typing import Optional, Callable, Dict
from mini_erp.core import (
    PRIMARY_COLOR,
    get_cases_list, 
    get_processes_list,
    get_clients_list,
    get_opposing_parties_list,
    get_display_name
)
from mini_erp.constants import AREA_COLORS_BACKGROUND, AREA_COLORS_TEXT, AREA_COLORS_BORDER
from .modal_nova_clausula import render_clausula_dialog


def make_required_label(text: str) -> str:
    """Adiciona asterisco ao final do label para campos obrigatórios."""
    return f'{text} *'


# Tipos de acordo criminal (em ordem específica)
TIPOS_ACORDO_CRIMINAL = [
    'Transação Penal',
    'Acordo de Não Persecução Penal (ANPP)',
    'Suspensão Condicional do Processo (Sursis Processual)',
    'Suspensão Condicional da Pena (Sursis Penal)',
]


def format_caso(caso: dict) -> str:
    """Formata caso para exibição."""
    title = caso.get('title', 'Sem título')
    number = caso.get('number', '')
    if number:
        return f"{title} ({number})"
    return title


def format_processo(processo: dict) -> str:
    """Formata processo para exibição."""
    title = processo.get('title', 'Sem título')
    number = processo.get('number', '')
    if number:
        return f"{title} ({number})"
    return title


def format_pessoa(pessoa: dict, tipo: str = '') -> str:
    """Formata pessoa para exibição com prefixo de tipo."""
    display = get_display_name(pessoa)
    
    if tipo == 'cliente':
        return f"[C] {display}"
    elif tipo == 'parte_contraria':
        return f"[PC] {display}"
    
    return display


def format_pessoa_simples(pessoa: dict) -> str:
    """Formata pessoa (sem prefixo de tipo)."""
    return get_display_name(pessoa)


def render_acordo_dialog(on_success: Optional[Callable] = None, acordo_inicial: Optional[Dict] = None):
    """
    Renderiza dialog para criar ou editar acordo.
    
    Args:
        on_success: Callback executado após salvar
        acordo_inicial: Dicionário com dados do acordo para edição (None para novo)
    
    Returns:
        tuple: (dialog, open_function)
    """
    
    # Determinar se é edição ou criação
    is_edicao = acordo_inicial is not None
    acordo_id = acordo_inicial.get('_id') if is_edicao else None
    
    # Estado do formulário - preencher com dados iniciais se for edição
    state = {
        'titulo': acordo_inicial.get('titulo', '') if is_edicao else '',
        'esfera': acordo_inicial.get('esfera', '') if is_edicao else '',
        'tipo_acordo_criminal': acordo_inicial.get('tipo_acordo_criminal', '') if is_edicao else '',
        'data_celebracao': acordo_inicial.get('data_celebracao', '') or acordo_inicial.get('data_assinatura', '') if is_edicao else '',
        'status': acordo_inicial.get('status', 'Em andamento') if is_edicao else 'Em andamento',
        'casos': acordo_inicial.get('casos', []) if is_edicao else [],
        'processos': acordo_inicial.get('processos', []) if is_edicao else [],
        'clientes': acordo_inicial.get('clientes', []) if is_edicao else [],
        'partes_contrarias': acordo_inicial.get('partes_contrarias', []) if is_edicao else [],
        'outros_envolvidos': acordo_inicial.get('outros_envolvidos', []) if is_edicao else [],
        'clausulas': acordo_inicial.get('clausulas', []) if is_edicao else [],
    }
    
    # Referência para função de renderização (será definida depois)
    render_clausulas_table_ref = {'func': None}
    
    # Função para salvar cláusula
    def on_save_clausula(clausula_data, edit_index=None):
        """Salva ou atualiza cláusula."""
        import uuid
        from datetime import datetime
        
        print(f"DEBUG: on_save_clausula chamado com dados: {clausula_data}")
        print(f"DEBUG: edit_index: {edit_index}")
        print(f"DEBUG: state['clausulas'] ANTES: {len(state['clausulas'])} itens")
        
        try:
            now = datetime.now().isoformat()
            
            if edit_index is not None and isinstance(edit_index, int):
                # UPDATE: Atualizar cláusula existente
                if 0 <= edit_index < len(state['clausulas']):
                    clausula_existente = state['clausulas'][edit_index]
                    clausula_data['_id'] = clausula_existente.get('_id') or str(uuid.uuid4())
                    clausula_data['data_criacao'] = clausula_existente.get('data_criacao', now)
                    clausula_data['data_atualizacao'] = now
                    clausula_data['ordem'] = clausula_existente.get('ordem', edit_index)
                    state['clausulas'][edit_index] = clausula_data
                    print(f"DEBUG: Cláusula editada no índice {edit_index}")
                    ui.notify('Cláusula atualizada com sucesso!', type='positive')
                else:
                    print(f"DEBUG: ERRO - Índice {edit_index} fora do range [0, {len(state['clausulas'])})")
                    ui.notify('Erro: cláusula não encontrada', type='negative')
                    return
            else:
                # CREATE: Adicionar nova cláusula
                if '_id' not in clausula_data or not clausula_data.get('_id'):
                    clausula_data['_id'] = str(uuid.uuid4())
                if 'data_criacao' not in clausula_data:
                    clausula_data['data_criacao'] = now
                clausula_data['data_atualizacao'] = now
                clausula_data['ordem'] = len(state['clausulas'])
                state['clausulas'].append(clausula_data)
                print(f"DEBUG: Nova cláusula adicionada. Total: {len(state['clausulas'])}")
                ui.notify('Cláusula adicionada com sucesso!', type='positive')
            
            print(f"DEBUG: state['clausulas'] DEPOIS: {state['clausulas']}")
            
            # Renderizar tabela atualizada
            if render_clausulas_table_ref['func']:
                print(f"DEBUG: Chamando render_clausulas_table_ref['func']()")
                render_clausulas_table_ref['func']()
                print("DEBUG: render_clausulas_table_ref['func']() executado")
            else:
                print("DEBUG: ERRO - render_clausulas_table_ref['func'] é None!")
            
        except Exception as e:
            import traceback
            print(f"ERRO em on_save_clausula: {traceback.format_exc()}")
            ui.notify(f'Erro ao salvar cláusula: {str(e)}', type='negative')
    
    # Função para abrir modal de nova cláusula
    def open_clausula_dialog():
        """Abre modal para nova cláusula."""
        dialog, open_dialog = render_clausula_dialog(
            on_save=on_save_clausula
        )
        open_dialog()
    
    # Função para abrir modal de edição de cláusula
    def open_clausula_dialog_edit(index):
        """Abre modal para editar cláusula existente."""
        if 0 <= index < len(state['clausulas']):
            clausula = state['clausulas'][index]
            
            # Criar dialog com dados preenchidos
            dialog_edit, open_edit = render_clausula_dialog(
                on_save=lambda data: on_save_clausula(data, edit_index=index),
                clausula_inicial=clausula
            )
            
            open_edit()
        else:
            ui.notify('Erro: cláusula não encontrada', type='negative')
    
    # Carregar dados de casos do Firestore
    casos_list = get_cases_list()  # Lista de todos os casos
    casos_options = [format_caso(c) for c in casos_list]
    
    # Carregar dados de processos do Firestore
    processos_list = get_processes_list()  # Lista de todos os processos
    processos_options = [format_processo(p) for p in processos_list]
    
    # CSS para sidebar (mesmo padrão do modal de processo)
    SIDEBAR_CSS = '''
        .acordo-sidebar-tabs .q-tab {
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
        .acordo-sidebar-tabs .q-tab:hover {
            background: rgba(255,255,255,0.08) !important;
            color: white !important;
        }
        .acordo-sidebar-tabs .q-tab--active {
            background: rgba(255,255,255,0.12) !important;
            color: white !important;
            border-left: 2px solid rgba(255,255,255,0.8) !important;
        }
        .acordo-sidebar-tabs .q-tab__content {
            flex-direction: row !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 8px !important;
            width: 100% !important;
        }
        .acordo-sidebar-tabs .q-tab__icon {
            font-size: 16px !important;
            margin: 0 !important;
            color: white !important;
            align-self: center !important;
            flex-shrink: 0 !important;
        }
        .acordo-sidebar-tabs .q-tab__label {
            font-weight: 400 !important;
            letter-spacing: 0.2px !important;
            color: white !important;
            text-align: left !important;
            align-self: center !important;
        }
        .acordo-sidebar-tabs .q-tabs__content {
            overflow: visible !important;
        }
        .acordo-sidebar-tabs .q-tab__indicator {
            display: none !important;
        }
    '''
    
    ui.add_head_html(f'<style>{SIDEBAR_CSS}</style>')
    
    # Dialog principal (mesmo padrão do modal de processo)
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden relative').style('height: 80vh; max-height: 80vh;'):
        with ui.row().classes('w-full h-full gap-0'):
            # Sidebar (mesmo padrão do modal de processo)
            with ui.column().classes('h-full shrink-0 justify-between').style(f'width: 170px; background: {PRIMARY_COLOR};'):
                with ui.column().classes('w-full gap-0'):
                    dialog_title = ui.label('EDITAR ACORDO' if is_edicao else 'NOVO ACORDO').classes('text-xs font-medium px-3 py-2 text-white/80 uppercase tracking-wide')
                    
                    with ui.tabs().props('vertical dense no-caps inline-label').classes('w-full acordo-sidebar-tabs') as tabs:
                        tab_dados = ui.tab('Dados básicos', icon='description')
                        tab_clausulas = ui.tab('Cláusulas', icon='article')
            
            # Content (mesmo padrão do modal de processo)
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_dados).classes('w-full h-full p-4 bg-transparent'):
                        
                        # ABA 1: DADOS BÁSICOS
                        with ui.tab_panel(tab_dados):
                            with ui.column().classes('w-full gap-4'):
                                
                                # Mapeamento de cores para tags (mesmo padrão do modal de processo)
                                TAG_COLORS = {
                                    'cases': '#9C27B0',      # Roxo para Casos
                                    'processes': '#FF9800',  # Laranja para Processos
                                }
                                
                                # Título do Acordo
                                with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                    ui.label('📋 Identificação').classes('text-lg font-bold mb-3')
                                    
                                    with ui.column().classes('w-full gap-2'):
                                        # Row 1: Título
                                        titulo_input = ui.input(
                                        label='Título do Acordo *',
                                        placeholder='Digite o título',
                                        value=state['titulo']
                                    ).classes('w-full').props('outlined dense')
                                    
                                        # Row 2: Esfera do Acordo
                                        esfera_options = ['Administrativo', 'Criminal', 'Cível', 'Tributário']
                                        esfera_input = ui.select(
                                            esfera_options,
                                            label=make_required_label('Esfera do Acordo'),
                                            value=state['esfera'] if state['esfera'] else None
                                        ).classes('w-full').props('outlined dense')
                                        esfera_input.tooltip('Área jurídica do acordo (Administrativa, Criminal, Cível ou Tributária)')
                                        
                                        # Row 2.5: Tipo de Acordo Criminal (campo condicional)
                                        # Verificar se deve mostrar inicialmente (se for edição e esfera for Criminal)
                                        esfera_inicial = state.get('esfera', '')
                                        mostrar_tipo_criminal = (esfera_inicial == 'Criminal')
                                        
                                        # Criar container vazio que será preenchido dinamicamente
                                        tipo_criminal_container = ui.column().classes('w-full')
                                        
                                        # Variável para armazenar o campo (será criado dinamicamente)
                                        tipo_acordo_criminal_input = None
                                        
                                        # Função para criar/atualizar o campo tipo criminal
                                        def render_tipo_criminal_field():
                                            """Cria ou atualiza o campo tipo de acordo criminal."""
                                            nonlocal tipo_acordo_criminal_input
                                            
                                            # Limpar container
                                            tipo_criminal_container.clear()
                                            
                                            # Verificar se deve mostrar
                                            current_esfera = esfera_input.value if esfera_input else esfera_inicial
                                            is_criminal = (current_esfera == 'Criminal')
                                            
                                            if is_criminal:
                                                # Criar o campo dentro do container
                                                with tipo_criminal_container:
                                                    tipo_acordo_criminal_input = ui.select(
                                                        TIPOS_ACORDO_CRIMINAL,
                                                        label=make_required_label('Tipo de Acordo Criminal'),
                                                        value=state['tipo_acordo_criminal'] if state['tipo_acordo_criminal'] else None
                                                    ).classes('w-full').props('outlined dense')
                                                    tipo_acordo_criminal_input.tooltip('Especifique o tipo de acordo na esfera criminal')
                                            else:
                                                # Limpar referência se não for criminal
                                                tipo_acordo_criminal_input = None
                                        
                                        # Renderizar campo inicialmente
                                        render_tipo_criminal_field()
                                        
                                        # Função para atualizar quando esfera mudar
                                        def on_esfera_change():
                                            """Atualiza campo tipo criminal quando esfera muda."""
                                            render_tipo_criminal_field()
                                        
                                        # Conectar evento de mudança da esfera
                                        esfera_input.on('update:model-value', lambda: on_esfera_change())
                                    
                                    # Row 3: Data e Status (lado a lado)
                                    with ui.row().classes('w-full gap-2'):
                                        # Formatar data para input type=date (YYYY-MM-DD)
                                        data_value = ''
                                        if state['data_celebracao']:
                                            try:
                                                # Tenta converter de DD/MM/YYYY ou timestamp
                                                if isinstance(state['data_celebracao'], str):
                                                    if '/' in state['data_celebracao']:
                                                        # DD/MM/YYYY -> YYYY-MM-DD
                                                        parts = state['data_celebracao'].split('/')
                                                        if len(parts) == 3:
                                                            data_value = f"{parts[2]}-{parts[1]}-{parts[0]}"
                                                    elif '-' in state['data_celebracao'] and len(state['data_celebracao']) >= 10:
                                                        # Já está em YYYY-MM-DD
                                                        data_value = state['data_celebracao'][:10]
                                                elif isinstance(state['data_celebracao'], (int, float)):
                                                    from datetime import datetime
                                                    dt = datetime.fromtimestamp(state['data_celebracao'])
                                                    data_value = dt.strftime('%Y-%m-%d')
                                            except:
                                                pass
                                        
                                        data_input = ui.input(
                                            label='Data de Celebração',
                                            placeholder='Selecione a data',
                                            value=data_value
                                        ).classes('flex-grow').props('outlined dense type=date')
                                        
                                        # Opções de status (apenas Em andamento e Concluído)
                                        status_options = ['Em andamento', 'Concluído']
                                        # Garantir que o status inicial seja válido
                                        status_inicial = state['status'] if state['status'] in status_options else 'Em andamento'
                                        status_input = ui.select(
                                            status_options,
                                            label='Status *',
                                            value=status_inicial
                                        ).classes('flex-grow').props('outlined dense')
                                
                                # SEÇÃO 2 - Vínculos (mesmo padrão do modal de processo)
                                with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                                    ui.label('🔗 Vínculos').classes('text-lg font-bold mb-3')
                                    
                                    with ui.column().classes('w-full gap-2'):
                                        # ===== CASOS RELACIONADOS =====
                                        # Container para chips de casos selecionados
                                        casos_chips_container = ui.column().classes('w-full')
                                        
                                        # Função para atualizar chips de casos (mesmo padrão do modal de processo)
                                        def refresh_casos_chips():
                                            """Atualiza exibição dos chips de casos."""
                                            casos_chips_container.clear()
                                            chip_color = TAG_COLORS.get('cases', '#9C27B0')
                                            
                                            with casos_chips_container:
                                                if state['casos']:
                                                    with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                                        for caso in state['casos']:
                                                            caso_id = caso.get('_id') or caso.get('id')
                                                            caso_title = format_caso(caso)
                                                            short_title = caso_title[:50] + '...' if len(caso_title) > 50 else caso_title
                                                            
                                                            with ui.badge(short_title).classes('pr-1').style(f'background-color: {chip_color}; color: white;'):
                                                                def remove_caso(cid=caso_id):
                                                                    """Remove caso da seleção."""
                                                                    state['casos'] = [
                                                                        c for c in state['casos']
                                                                        if (c.get('_id') or c.get('id')) != cid
                                                                    ]
                                                                    refresh_casos_chips()
                                                                
                                                                ui.button(icon='close', on_click=remove_caso).props('flat dense round size=xs color=white')
                                                else:
                                                    ui.label('Nenhum caso selecionado').classes('text-gray-400 italic text-sm')
                                
                                        # Row com select + botão (mesmo padrão do modal de processo)
                                        with ui.row().classes('w-full gap-2 items-center'):
                                            casos_select = ui.select(
                                                casos_options or [],
                                                label='Casos Vinculados',
                                                with_input=True
                                            ).classes('flex-grow').props('dense outlined')
                                            casos_select.tooltip('Casos do escritório relacionados a este acordo')
                                            
                                            # Função de filtro para casos
                                            def filter_casos(e):
                                                """Filtra opções de casos baseado no texto digitado."""
                                                search_text = (e.args or '').lower().strip()
                                                if not search_text:
                                                    casos_select.options = casos_options
                                                else:
                                                    filtered = [opt for opt in casos_options if search_text in opt.lower()]
                                                    casos_select.options = filtered if filtered else ['Nenhum caso encontrado']
                                                casos_select.update()
                                            
                                            casos_select.on('update:input-value', filter_casos)
                                            
                                            # Função para adicionar caso
                                            def add_caso():
                                                """Adiciona caso selecionado à lista."""
                                                if casos_select.value:
                                                    selected_title = casos_select.value
                                                    
                                                    # Verificar se já está na lista
                                                    caso_ids_selecionados = [
                                                        c.get('_id') or c.get('id') 
                                                        for c in state['casos']
                                                    ]
                                                    
                                                    # Encontrar o caso na lista original
                                                    selected_caso = None
                                                    for caso in casos_list:
                                                        if format_caso(caso) == selected_title:
                                                            selected_caso = caso
                                                            break
                                                    
                                                    if selected_caso:
                                                        caso_id = selected_caso.get('_id') or selected_caso.get('id')
                                                        
                                                        # Verificar se já está na lista
                                                        if caso_id not in caso_ids_selecionados:
                                                            state['casos'].append(selected_caso)
                                                            casos_select.value = None  # Limpar seleção
                                                            # Restaura opções completas
                                                            casos_select.options = casos_options
                                                            refresh_casos_chips()
                                                        else:
                                                            ui.notify('Este caso já está adicionado!', type='warning')
                                                    else:
                                                        ui.notify('Caso não encontrado!', type='warning')
                                            
                                            ui.button(icon='add', on_click=add_caso).props('flat dense').style('color: #9C27B0;')
                                        
                                        # Renderizar chips inicialmente (com dados se for edição)
                                        refresh_casos_chips()
                                    
                                    # ===== PROCESSOS RELACIONADOS =====
                                    # Container para chips de processos selecionados
                                    processos_chips_container = ui.column().classes('w-full')
                                    
                                    # Função para atualizar chips de processos (mesmo padrão do modal de processo)
                                    def refresh_processos_chips():
                                        """Atualiza exibição dos chips de processos."""
                                        processos_chips_container.clear()
                                        chip_color = TAG_COLORS.get('processes', '#FF9800')
                                        
                                        with processos_chips_container:
                                            if state['processos']:
                                                with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                                                    for processo in state['processos']:
                                                        processo_id = processo.get('_id') or processo.get('id')
                                                        processo_title = format_processo(processo)
                                                        short_title = processo_title[:50] + '...' if len(processo_title) > 50 else processo_title
                                                        
                                                        with ui.badge(short_title).classes('pr-1').style(f'background-color: {chip_color}; color: white;'):
                                                            def remove_processo(pid=processo_id):
                                                                """Remove processo da seleção."""
                                                                state['processos'] = [
                                                                    p for p in state['processos']
                                                                    if (p.get('_id') or p.get('id')) != pid
                                                                ]
                                                                refresh_processos_chips()
                                                            
                                                            ui.button(icon='close', on_click=remove_processo).props('flat dense round size=xs color=white')
                                            else:
                                                ui.label('Nenhum processo selecionado').classes('text-gray-400 italic text-sm')
                                
                                        # Row com select + botão (mesmo padrão do modal de processo)
                                        with ui.row().classes('w-full gap-2 items-center'):
                                            processos_select = ui.select(
                                                processos_options or [],
                                                label='Processos Relacionados',
                                                with_input=True
                                            ).classes('flex-grow').props('dense outlined')
                                            processos_select.tooltip('Processos relacionados a este acordo')
                                            
                                            # Função de filtro para processos
                                            def filter_processos(e):
                                                """Filtra opções de processos baseado no texto digitado."""
                                                search_text = (e.args or '').lower().strip()
                                                if not search_text:
                                                    processos_select.options = processos_options
                                                else:
                                                    filtered = [opt for opt in processos_options if search_text in opt.lower()]
                                                    processos_select.options = filtered if filtered else ['Nenhum processo encontrado']
                                                processos_select.update()
                                            
                                            processos_select.on('update:input-value', filter_processos)
                                            
                                            # Função para adicionar processo
                                            def add_processo():
                                                """Adiciona processo selecionado à lista."""
                                                if processos_select.value:
                                                    selected_title = processos_select.value
                                                    
                                                    # Verificar se já está na lista
                                                    processo_ids_selecionados = [
                                                        p.get('_id') or p.get('id') 
                                                        for p in state['processos']
                                                    ]
                                                    
                                                    # Encontrar o processo na lista original
                                                    selected_processo = None
                                                    for processo in processos_list:
                                                        if format_processo(processo) == selected_title:
                                                            selected_processo = processo
                                                            break
                                                    
                                                    if selected_processo:
                                                        processo_id = selected_processo.get('_id') or selected_processo.get('id')
                                                        
                                                        # Verificar se já está na lista
                                                        if processo_id not in processo_ids_selecionados:
                                                            state['processos'].append(selected_processo)
                                                            processos_select.value = None  # Limpar seleção
                                                            # Restaura opções completas
                                                            processos_select.options = processos_options
                                                            refresh_processos_chips()
                                                        else:
                                                            ui.notify('Este processo já está adicionado!', type='warning')
                                                    else:
                                                        ui.notify('Processo não encontrado!', type='warning')
                                            
                                            ui.button(icon='add', on_click=add_processo).props('flat dense').style('color: #FF9800;')
                                        
                                        # Renderizar chips inicialmente (com dados se for edição)
                                        refresh_processos_chips()
                    
                        # ABA 2: CLÁUSULAS
                        with ui.tab_panel(tab_clausulas):
                            with ui.column().classes('w-full gap-6'):
                                # Botão Nova Cláusula
                                with ui.row().classes('w-full justify-end mb-4'):
                                    ui.button(
                                        '+ NOVA CLÁUSULA',
                                        icon='add',
                                        on_click=open_clausula_dialog
                                    ).props('color=primary').classes('font-bold')
                                
                                # Container para tabela de cláusulas
                                clausulas_table_container = ui.column().classes('w-full')
                                
                                # Função de renderização de tabela
                                def render_clausulas_table():
                                    """Renderiza tabela de cláusulas com cards em grid."""
                                    print(f"DEBUG: render_clausulas_table chamado")
                                    print(f"DEBUG: clausulas_table_container existe: {clausulas_table_container is not None}")
                                    print(f"DEBUG: Total de cláusulas para renderizar: {len(state['clausulas'])}")
                                    
                                    try:
                                        if not clausulas_table_container:
                                            print("DEBUG: ERRO - clausulas_table_container é None!")
                                            return
                                        
                                        clausulas_table_container.clear()
                                        
                                        with clausulas_table_container:
                                            if state['clausulas']:
                                                print(f"DEBUG: Renderizando {len(state['clausulas'])} cláusulas")
                                                # Card com borda para tabela
                                                with ui.card().classes('w-full p-0').style('border: 1px solid #e5e7eb;'):
                                                    # Cabeçalho da tabela
                                                    with ui.row().classes('w-full bg-gray-100 p-3 font-bold text-sm items-center').style(
                                                        'border-bottom: 2px solid #e0e0e0;'
                                                    ):
                                                        ui.label('Título').classes('flex-grow')
                                                        ui.label('Número').classes('w-24 text-center')
                                                        ui.label('Tipo').classes('w-28 text-center')
                                                        ui.label('Prazo Seg.').classes('w-32 text-center')
                                                        ui.label('Prazo Fatal').classes('w-32 text-center')
                                                        ui.label('Status').classes('w-28 text-center')
                                                        ui.label('Ações').classes('w-32 text-center')
                                                
                                                    # Linhas da tabela
                                                    for idx, clausula in enumerate(state['clausulas']):
                                                        print(f"DEBUG: Renderizando cláusula {idx}: {clausula.get('titulo', 'sem título')}")
                                                        with ui.row().classes('w-full p-3 items-center').style(
                                                            'border-bottom: 1px solid #e0e0e0;'
                                                        ):
                                                            # Título
                                                            ui.label(clausula.get('titulo', '-')).classes('flex-grow text-sm')
                                                            
                                                            # Número
                                                            ui.label(clausula.get('numero', '-')).classes('w-24 text-center text-sm')
                                                            
                                                            # Tipo
                                                            ui.label(clausula.get('tipo', '-')).classes('w-28 text-center text-sm')
                                                            
                                                            # Prazos (Regular ou valores)
                                                            if clausula.get('regular'):
                                                                ui.label('Regular').classes('w-32 text-center text-sm font-semibold').style('color: #4CAF50;')
                                                                ui.label('-').classes('w-32 text-center text-sm')
                                                            else:
                                                                prazo_seg = clausula.get('prazo_seguranca', '-')
                                                                prazo_fat = clausula.get('prazo_fatal', '-')
                                                                ui.label(prazo_seg if prazo_seg else '-').classes('w-32 text-center text-sm')
                                                                ui.label(prazo_fat if prazo_fat else '-').classes('w-32 text-center text-sm')
                                                            
                                                            # Status com badge
                                                            status = clausula.get('status', '-')
                                                            status_color = {
                                                                'Cumprida': 'positive',
                                                                'Pendente': 'warning',
                                                                'Atrasada': 'negative'
                                                            }.get(status, 'primary')
                                                            
                                                            with ui.row().classes('w-28 justify-center'):
                                                                ui.badge(status).props(f'color={status_color}').classes('text-xs')
                                                            
                                                            # Botões de ação
                                                            with ui.row().classes('w-32 justify-center gap-1'):
                                                                def edit_wrapper(index=idx):
                                                                    """Abre modal para editar cláusula."""
                                                                    open_clausula_dialog_edit(index)
                                                                
                                                                def delete_wrapper(index=idx):
                                                                    """Remove cláusula."""
                                                                    state['clausulas'].pop(index)
                                                                    render_clausulas_table()
                                                                    ui.notify('Cláusula removida!', type='positive')
                                                                
                                                                ui.button(
                                                                    icon='edit',
                                                                    on_click=edit_wrapper
                                                                ).props('flat color=primary size=sm')
                                                                
                                                                ui.button(
                                                                    icon='delete',
                                                                    on_click=delete_wrapper
                                                                ).props('flat color=negative size=sm')
                                            else:
                                                print("DEBUG: Nenhuma cláusula para renderizar - exibindo mensagem vazia")
                                                # Mensagem quando vazio
                                                with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                                                    ui.icon('note_add', size='48px').classes('text-gray-300 mb-4')
                                                    ui.label('Nenhuma cláusula adicionada').classes(
                                                        'text-gray-400 text-center font-medium'
                                                    )
                                                    ui.label('Clique em "+ NOVA CLÁUSULA" para começar').classes(
                                                        'text-sm text-gray-400 text-center mt-2'
                                                    )
                                        
                                        print("DEBUG: render_clausulas_table concluído com sucesso")
                                        
                                    except Exception as e:
                                        import traceback
                                        print(f"ERRO em render_clausulas_table: {traceback.format_exc()}")
                                        ui.notify(f'Erro ao renderizar cláusulas: {str(e)}', type='negative')
                                
                                # Armazenar referência da função
                                render_clausulas_table_ref['func'] = render_clausulas_table
                                
                                # Renderizar tabela inicial (vazia)
                                render_clausulas_table()
        
        # ===== BOTÕES FIXOS NA BASE (mesmo padrão do modal de processo) =====
        with ui.row().classes('w-full gap-4 p-4 justify-between items-center').style(
            'border-top: 1px solid #e5e7eb; background-color: white; flex-shrink: 0;'
        ):
            # Botão EXCLUIR (à esquerda) - apenas em modo edição (mesmo padrão do modal de processo)
            if is_edicao:
                def on_delete():
                    """Deleta o acordo."""
                    ui.notify('Funcionalidade de exclusão será implementada', type='info')
                    # Será implementado quando for editar acordo existente
                
                delete_btn = ui.button('EXCLUIR', icon='delete', on_click=on_delete).props('color=red').classes('font-bold shadow-lg')
            
            # Botão SALVAR (mesmo padrão do modal de processo)
            def on_save():
                """Salva o acordo."""
                # Importar logger
                from ....utils.save_logger import SaveLogger
                
                # Validar título
                if not titulo_input.value:
                    ui.notify('Título do acordo é obrigatório!', type='warning')
                    return
                
                # Validar esfera
                if not esfera_input.value:
                    ui.notify('Selecione a esfera do acordo!', type='warning')
                    return
                
                # Validar tipo de acordo criminal (obrigatório se esfera for Criminal)
                if esfera_input.value == 'Criminal':
                    if not tipo_acordo_criminal_input or not tipo_acordo_criminal_input.value:
                        ui.notify('Para acordos criminais, selecione o tipo de acordo!', type='warning')
                        return
                
                # Validar status
                if not status_input.value:
                    ui.notify('Status do acordo é obrigatório!', type='warning')
                    return
                
                # Preparar dados - GARANTIR que TODOS os campos estão incluídos
                tipo_criminal_value = None
                if esfera_input.value == 'Criminal' and tipo_acordo_criminal_input and tipo_acordo_criminal_input.value:
                    tipo_criminal_value = tipo_acordo_criminal_input.value
                
                acordo_data = {
                    'titulo': titulo_input.value or '',
                    'esfera': esfera_input.value if esfera_input.value else None,
                    'tipo_acordo_criminal': tipo_criminal_value,
                    'data_celebracao': data_input.value or '',
                    'status': status_input.value or 'Em andamento',
                    'casos': state.get('casos', []) or [],
                    'processos': state.get('processos', []) or [],
                    'clientes': state.get('clientes', []) or [],
                    'partes_contrarias': state.get('partes_contrarias', []) or [],
                    'outros_envolvidos': state.get('outros_envolvidos', []) or [],
                    'clausulas': state.get('clausulas', []) or [],
                }
                
                # Adicionar ID se for edição
                if is_edicao and acordo_id:
                    acordo_data['_id'] = acordo_id
                
                # Validar se há cláusulas (opcional)
                if not state['clausulas']:
                    ui.notify('Adicione pelo menos uma cláusula ao acordo', type='warning')
                    return
                
                # Log antes de salvar
                SaveLogger.log_save_attempt('acordos', acordo_id or 'novo', acordo_data)
                
                try:
                    # Chamar callback se fornecido
                    if on_success:
                        on_success(acordo_data)
                    
                    # Log de sucesso
                    SaveLogger.log_save_success('acordos', acordo_id or 'novo')
                    
                    # Notificar sucesso
                    ui.notify('Acordo salvo com sucesso!', type='positive')
                    
                    # Fechar dialog
                    dialog.close()
                except Exception as e:
                    # Log de erro
                    SaveLogger.log_save_error('acordos', acordo_id or 'novo', e)
                    ui.notify(f'Erro ao salvar acordo: {str(e)}', type='negative')
            
            ui.button('SALVAR', icon='save', on_click=on_save).props('color=primary').classes('font-bold shadow-lg')
    
    def open_dialog():
        """Abre o dialog."""
        dialog.open()
    
    return dialog, open_dialog

