"""
ui_components.py - Componentes reutilizáveis da interface para o módulo de Acordos.

Este módulo contém:
- Componentes de tabela
- Formulários
- Cards de exibição
- Placeholders para funcionalidades em desenvolvimento
"""

from nicegui import ui
from typing import List, Dict, Any, Optional, Callable


# =============================================================================
# COMPONENTES DE TABELA
# =============================================================================

def render_acordos_table(
    acordos: List[Dict[str, Any]],
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None
) -> None:
    """
    Renderiza tabela com lista de acordos.
    
    Args:
        acordos: Lista de dicionários com dados dos acordos
        on_edit: Função callback para edição (recebe acordo_id)
        on_delete: Função callback para exclusão (recebe acordo_id)
    """
    if not acordos:
        ui.label('Nenhum acordo cadastrado.').classes('text-gray-500 mt-4')
        return
    
    # Cabeçalho da tabela
    with ui.table(
        columns=[
            {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'sortable': True},
            {'name': 'cliente', 'label': 'Cliente', 'field': 'cliente', 'align': 'left', 'sortable': True},
            {'name': 'valor', 'label': 'Valor', 'field': 'valor', 'align': 'right', 'sortable': True},
            {'name': 'data_assinatura', 'label': 'Data Assinatura', 'field': 'data_assinatura', 'align': 'center', 'sortable': True},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
            {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center'},
        ],
        rows=[],
        row_key='id'
    ).classes('w-full') as table:
        # Preenche dados
        rows = []
        for acordo in acordos:
            rows.append({
                'id': acordo.get('_id') or acordo.get('id', ''),
                'titulo': acordo.get('titulo', 'Sem título'),
                'cliente': acordo.get('cliente', '-'),
                'valor': acordo.get('valor', '-'),
                'data_assinatura': acordo.get('data_assinatura', '-'),
                'status': acordo.get('status', 'Rascunho'),
                'acoes': ''
            })
        
        table.rows = rows
        
        # Adiciona botões de ação (placeholder)
        def add_action_buttons(row):
            with table.add_slot('body-cell-acoes'):
                with ui.row().classes('gap-2'):
                    if on_edit:
                        ui.button('Editar', icon='edit', size='sm').props('flat dense').on('click', lambda e, id=row['id']: on_edit(id))
                    if on_delete:
                        ui.button('Deletar', icon='delete', size='sm').props('flat dense').on('click', lambda e, id=row['id']: on_delete(id))


def render_acordo_card(acordo: Dict[str, Any]) -> None:
    """
    Renderiza card com resumo de um acordo.
    
    Args:
        acordo: Dicionário com dados do acordo
    """
    with ui.card().classes('w-full p-4'):
        with ui.column().classes('gap-2'):
            ui.label(acordo.get('titulo', 'Sem título')).classes('text-lg font-semibold')
            
            if acordo.get('descricao'):
                ui.label(acordo['descricao']).classes('text-sm text-gray-600')
            
            with ui.row().classes('gap-4'):
                if acordo.get('cliente'):
                    with ui.column().classes('gap-1'):
                        ui.label('Cliente:').classes('text-xs text-gray-500')
                        ui.label(acordo['cliente']).classes('text-sm font-medium')
                
                if acordo.get('valor'):
                    with ui.column().classes('gap-1'):
                        ui.label('Valor:').classes('text-xs text-gray-500')
                        ui.label(f"R$ {acordo['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')).classes('text-sm font-medium')
                
                if acordo.get('status'):
                    with ui.column().classes('gap-1'):
                        ui.label('Status:').classes('text-xs text-gray-500')
                        ui.label(acordo['status']).classes('text-sm font-medium')


# =============================================================================
# FORMULÁRIOS (PLACEHOLDER)
# =============================================================================

def render_acordo_form(
    acordo_data: Optional[Dict[str, Any]] = None,
    on_save: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None
) -> None:
    """
    Renderiza formulário para criar/editar acordo.
    
    Args:
        acordo_data: Dados do acordo (None para novo acordo)
        on_save: Função callback ao salvar (recebe dados do acordo)
        on_cancel: Função callback ao cancelar
    """
    ui.label('Formulário de Acordo').classes('text-xl font-bold mb-4')
    ui.label('Esta funcionalidade está em desenvolvimento.').classes('text-gray-500')
    
    if acordo_data:
        ui.label(f'Editando acordo: {acordo_data.get("titulo", "Sem título")}').classes('text-sm text-gray-600 mt-2')
    
    # Placeholder para campos do formulário
    with ui.column().classes('gap-4 mt-4'):
        ui.input('Título', placeholder='Digite o título do acordo').classes('w-full')
        ui.textarea('Descrição', placeholder='Descrição do acordo').classes('w-full')
        ui.select(['Rascunho', 'Ativo', 'Arquivado', 'Cancelado'], label='Status').classes('w-full')
        
        with ui.row().classes('gap-4 w-full'):
            ui.input('Valor', placeholder='0.00').classes('flex-1')
            ui.input('Data de Assinatura', placeholder='DD/MM/AAAA').classes('flex-1')
        
        with ui.row().classes('gap-2 mt-4'):
            if on_save:
                ui.button('Salvar', icon='save').props('color=primary')
            if on_cancel:
                ui.button('Cancelar', icon='cancel').props('flat').on('click', on_cancel)


# =============================================================================
# MENSAGENS DE DESENVOLVIMENTO
# =============================================================================

def render_development_message() -> None:
    """Renderiza mensagem indicando que o módulo está em desenvolvimento."""
    with ui.column().classes('items-center justify-center gap-4 p-8'):
        ui.icon('construction', size='64px').classes('text-gray-400')
        ui.label('Módulo em Desenvolvimento').classes('text-2xl font-bold text-gray-600')
        ui.label('Este módulo está sendo desenvolvido e estará disponível em breve.').classes('text-gray-500 text-center max-w-md')


# =============================================================================
# FUNÇÕES AUXILIARES PARA FORMATAÇÃO
# =============================================================================

def formatar_partes_envolvidas(acordo: Dict[str, Any]) -> str:
    """
    Formata todas as partes envolvidas em uma string única.
    
    Args:
        acordo: Dicionário com dados do acordo (deve ter clientes_ids, parte_contraria, outros_envolvidos)
    
    Returns:
        String formatada: "Cliente 1, Cliente 2, Parte Contrária X, Envolvido 1"
    """
    from ...core import get_clients_list, get_opposing_parties_list, get_display_name
    
    partes = []
    
    # Busca clientes
    clientes_ids = acordo.get('clientes_ids', [])
    if clientes_ids:
        clients_list = get_clients_list()
        for cliente_id in clientes_ids:
            for cliente in clients_list:
                if cliente.get('_id') == cliente_id:
                    partes.append(get_display_name(cliente))
                    break
    
    # Busca parte contrária
    parte_contraria_id = acordo.get('parte_contraria')
    if parte_contraria_id:
        all_people = get_clients_list() + get_opposing_parties_list()
        for pessoa in all_people:
            if pessoa.get('_id') == parte_contraria_id:
                partes.append(get_display_name(pessoa))
                break
    
    # Busca outros envolvidos
    outros_envolvidos_ids = acordo.get('outros_envolvidos', [])
    if outros_envolvidos_ids:
        all_people = get_clients_list() + get_opposing_parties_list()
        for pessoa_id in outros_envolvidos_ids:
            for pessoa in all_people:
                if pessoa.get('_id') == pessoa_id:
                    partes.append(get_display_name(pessoa))
                    break
    
    if not partes:
        return '-'
    
    return ', '.join(partes)


# =============================================================================
# COMPONENTES DE TABELA - NOVA ESTRUTURA
# =============================================================================

def header_acordos(on_novo_acordo: Optional[Callable] = None) -> ui.input:
    """
    Renderiza barra superior com pesquisa e botão de novo acordo.
    
    Args:
        on_novo_acordo: Callback para criar novo acordo
    
    Returns:
        Campo de pesquisa (ui.input)
    """
    with ui.row().classes('w-full items-center gap-2 sm:gap-4 mb-4 flex-wrap'):
        # Campo de busca com ícone de lupa
        with ui.input(placeholder='Pesquisar acordos por título, número...').props('outlined dense clearable').classes('flex-grow w-full sm:w-auto sm:max-w-xl') as search_input:
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
        
        # Botão "+ NOVO ACORDO"
        if on_novo_acordo:
            ui.button('+ NOVO ACORDO', on_click=on_novo_acordo).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')
    
    return search_input


def filtros_acordos(
    filter_status: Dict[str, str],
    filter_options: Dict[str, List[str]],
    on_filter_change: Optional[Callable] = None,
    on_clear: Optional[Callable] = None
) -> Dict[str, ui.select]:
    """
    Renderiza seção de filtros.
    
    Args:
        filter_status: Dicionário com estado dos filtros
        filter_options: Opções disponíveis para cada filtro
        on_filter_change: Callback quando filtro muda
        on_clear: Callback para limpar filtros
    
    Returns:
        Dicionário com os selects de filtro
    """
    selects = {}
    
    with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
        ui.label('Filtros:').classes('text-gray-600 font-medium text-sm w-full sm:w-auto')
        
        # Filtro de Status
        def create_status_select():
            select = ui.select(
                filter_options.get('status', ['']),
                label='Status',
                value=filter_status.get('status', '')
            ).props('clearable dense outlined').classes('w-full sm:w-auto min-w-[100px] sm:min-w-[140px]')
            select.style('font-size: 12px; border-color: #d1d5db;')
            
            def on_change():
                filter_status['status'] = select.value if select.value else ''
                if on_filter_change:
                    on_filter_change()
            
            select.on('update:model-value', on_change)
            return select
        
        selects['status'] = create_status_select()
        
        # Botão Limpar
        if on_clear:
            ui.button('Limpar', icon='clear_all', on_click=on_clear).props('flat dense').classes('text-xs text-gray-600 w-full sm:w-auto')
    
    return selects


def tabela_acordos(
    acordos: List[Dict[str, Any]],
    on_edit: Optional[Callable] = None
) -> ui.table:
    """
    Renderiza tabela de acordos com novo layout.
    
    Colunas: Data de Celebração | Título (clicável) | Partes Envolvidas | Status
    
    Args:
        acordos: Lista de acordos para exibir (deve ter campos: data, titulo, partes_envolvidas, status, _id)
        on_edit: Callback para editar (recebe acordo_id) - chamado ao clicar no título
    
    Returns:
        Componente ui.table
    """
    # Define colunas (sem coluna de ações)
    columns = [
        {'name': 'data', 'label': 'Data de Celebração', 'field': 'data_sort', 'align': 'center', 'sortable': True, 'style': 'width: 120px; min-width: 120px;'},
        {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'sortable': True},
        {'name': 'partes_envolvidas', 'label': 'Partes Envolvidas', 'field': 'partes_envolvidas', 'align': 'left', 'sortable': False, 'style': 'width: 300px; max-width: 300px;'},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 120px; min-width: 120px;'},
    ]
    
    # Estado vazio
    if not acordos:
        with ui.card().classes('w-full p-8 flex justify-center items-center'):
            ui.label('Nenhum acordo cadastrado.').classes('text-gray-400 italic')
        return None
    
    # Cria tabela
    table = ui.table(
        columns=columns,
        rows=acordos,
        row_key='_id',
        pagination={'rowsPerPage': 20}
    ).classes('w-full')
    
    # Slot para data de celebração
    table.add_slot('body-cell-data', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <span v-if="props.row.data" class="text-xs text-gray-700 font-medium">{{ props.row.data }}</span>
            <span v-else class="text-gray-400">—</span>
        </q-td>
    ''')
    
    # Slot para título (clicável) - CSS puro para hover
    table.add_slot('body-cell-titulo', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <a 
                href="#" 
                @click.prevent="$parent.$emit('editAcordo', props.row._id)"
                class="acordo-titulo-link"
                style="color: #1976d2; text-decoration: none; cursor: pointer; font-weight: 500;"
            >
                {{ props.value || 'Sem título' }}
            </a>
        </q-td>
    ''')
    
    # CSS para hover do título (adiciona ao head)
    titulo_link_css = '''
        .acordo-titulo-link:hover {
            text-decoration: underline !important;
        }
    '''
    ui.add_head_html(f'<style>{titulo_link_css}</style>')
    
    # Slot para partes envolvidas (com tooltip se truncado)
    table.add_slot('body-cell-partes_envolvidas', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <span 
                v-if="props.value && props.value !== '-'" 
                :title="props.value"
                class="text-xs text-gray-700"
                style="display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 300px;"
            >
                {{ props.value }}
            </span>
            <span v-else class="text-gray-400">—</span>
        </q-td>
    ''')
    
    # Slot para status com badge colorido
    table.add_slot('body-cell-status', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <q-badge 
                :color="!props.value || props.value.toLowerCase().includes('rascunho') ? 'grey' : 
                        props.value.toLowerCase().includes('ativo') ? 'green' : 
                        props.value.toLowerCase().includes('arquivado') ? 'blue' : 
                        props.value.toLowerCase().includes('cancelado') ? 'red' : 'grey'" 
                :label="props.value || 'Rascunho'" />
        </q-td>
    ''')
    
    # Handler para clique no título
    if on_edit:
        def handle_edit(e):
            acordo_id = e.args
            if acordo_id:
                on_edit(acordo_id)
        table.on('editAcordo', handle_edit)
    
    return table


# =============================================================================
# COMPONENTES DE CLÁUSULAS
# =============================================================================

def card_clausula(
    clausula: Dict[str, Any],
    index: int,
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None
) -> None:
    """
    Renderiza card individual de cláusula.
    
    Args:
        clausula: Dicionário com dados da cláusula
        index: Índice da cláusula na lista
        on_edit: Callback para editar (recebe index)
        on_delete: Callback para deletar (recebe index)
    """
    from .business_logic import formatar_data_para_exibicao
    
    status = clausula.get('status', 'Pendente')
    tipo_clausula = clausula.get('tipo_clausula', '')
    numero = clausula.get('numero', '')
    titulo = clausula.get('titulo', 'Sem título')
    descricao = clausula.get('descricao', '')
    prazo_seg = formatar_data_para_exibicao(clausula.get('prazo_seguranca', ''))
    prazo_fatal = formatar_data_para_exibicao(clausula.get('prazo_fatal', ''))
    descricao_comprovacao = clausula.get('descricao_comprovacao', '')
    link_comprovacao = clausula.get('link_comprovacao', '')
    
    # Cor do card baseada no status
    status_colors = {
        'Cumprida': '#4CAF50',  # Verde
        'Pendente': '#FF9800',  # Amarelo/Laranja
        'Atrasada': '#F44336',  # Vermelho
    }
    border_color = status_colors.get(status, '#9E9E9E')
    
    with ui.card().classes('w-full p-4 mb-3').style(f'border-left: 4px solid {border_color};'):
        with ui.column().classes('w-full gap-2'):
            # Cabeçalho: Tipo, Número e Título
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('flex-1 gap-1'):
                    # Tipo de cláusula (badge)
                    tipo_badge = ''
                    if tipo_clausula:
                        tipo_color = '#2196F3' if tipo_clausula == 'Geral' else '#9C27B0'
                        tipo_badge = f'[{tipo_clausula}]'
                    
                    # Título com número (se houver)
                    titulo_display = f'{titulo}'
                    if numero:
                        titulo_display = f'Cláusula {numero}: {titulo}'
                    
                    with ui.row().classes('items-center gap-2 flex-wrap'):
                        if tipo_badge:
                            with ui.badge(tipo_badge).style(f'background-color: {tipo_color if tipo_clausula == "Geral" else "#9C27B0"}; color: white;'):
                                pass
                        ui.label(titulo_display).classes('text-base font-semibold text-gray-800')
                    
                    with ui.row().classes('items-center gap-4'):
                        # Status
                        with ui.badge(status).style(f'background-color: {border_color}; color: white;'):
                            pass
                        # Prazos (se existirem)
                        if prazo_seg and prazo_seg != '-' and prazo_fatal and prazo_fatal != '-':
                            ui.label(f'Prazos: {prazo_seg} | {prazo_fatal}').classes('text-xs text-gray-600')
                        elif prazo_seg and prazo_seg != '-':
                            ui.label(f'Prazo Segurança: {prazo_seg}').classes('text-xs text-gray-600')
                        elif prazo_fatal and prazo_fatal != '-':
                            ui.label(f'Prazo Fatal: {prazo_fatal}').classes('text-xs text-gray-600')
                
                # Botões de ação
                with ui.row().classes('gap-2'):
                    if on_edit:
                        ui.button(icon='edit', on_click=lambda idx=index: on_edit(idx)).props('flat dense size=sm').classes('text-blue-600')
                    if on_delete:
                        ui.button(icon='delete', on_click=lambda idx=index: on_delete(idx)).props('flat dense size=sm').classes('text-red-600')
            
            # Descrição (truncada se muito longa)
            if descricao:
                desc_truncated = descricao[:150] + '...' if len(descricao) > 150 else descricao
                ui.label(desc_truncated).classes('text-sm text-gray-600 mt-2')
            
            # Comprovação (se status = Cumprida)
            if status == 'Cumprida' and (descricao_comprovacao or link_comprovacao):
                with ui.card().classes('w-full p-3 mt-2').style('background-color: #f1f8f4; border: 1px solid #4CAF50;'):
                    ui.label('✅ Comprovação').classes('text-sm font-semibold text-green-700 mb-2')
                    if descricao_comprovacao:
                        desc_comprov_truncated = descricao_comprovacao[:200] + '...' if len(descricao_comprovacao) > 200 else descricao_comprovacao
                        ui.label(desc_comprov_truncated).classes('text-xs text-gray-700 mb-1')
                    if link_comprovacao:
                        def open_link():
                            link = link_comprovacao
                            if not link.startswith(('http://', 'https://')):
                                link = 'https://' + link
                            ui.run_javascript(f'window.open("{link}", "_blank")')
                        ui.button('Abrir Link de Comprovação', icon='open_in_new', on_click=open_link).props('flat dense size=sm').classes('text-green-700')


def lista_clausulas(
    clausulas: List[Dict[str, Any]],
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None
) -> Optional[ui.table]:
    """
    Renderiza lista de cláusulas em formato de tabela.
    
    Args:
        clausulas: Lista de dicionários com dados das cláusulas
        on_edit: Callback para editar (recebe index)
        on_delete: Callback para deletar (recebe index)
    
    Returns:
        Componente ui.table ou None se não houver cláusulas
    """
    if not clausulas:
        with ui.card().classes('w-full p-8 flex justify-center items-center'):
            ui.label('Nenhuma cláusula adicionada.').classes('text-gray-400 italic')
        return None
    
    # Prepara dados para tabela
    from .business_logic import formatar_data_para_exibicao
    
    # Função para ordenar cláusulas por número (se houver) ou mantém ordem original
    # Tenta ordenar numericamente se possível, senão alfabeticamente
    def sort_key(c):
        numero = c.get('numero', '')
        if numero:
            # Tenta converter para número se possível
            try:
                # Remove pontos e tenta converter
                num_clean = numero.replace('.', '').strip()
                if num_clean.isdigit():
                    return (0, int(num_clean))
                # Se tem pontos, tenta ordenar por partes
                parts = numero.split('.')
                if all(p.isdigit() for p in parts):
                    return (0, tuple(int(p) for p in parts))
            except:
                pass
            return (1, numero.lower())
        return (2, c.get('titulo', '').lower())
    
    # Define colunas da tabela
    columns = [
        {'name': 'numero_seq', 'label': '#', 'field': 'numero_seq', 'align': 'center', 'sortable': True, 'style': 'width: 50px;'},
        {'name': 'numero_clausula', 'label': 'Número', 'field': 'numero_clausula', 'align': 'left', 'sortable': True, 'style': 'width: 120px;'},
        {'name': 'titulo', 'label': 'Título da Cláusula', 'field': 'titulo', 'align': 'left', 'sortable': True},
        {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'center', 'sortable': True, 'style': 'width: 100px;'},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 120px;'},
        {'name': 'prazos', 'label': 'Prazos', 'field': 'prazos', 'align': 'left', 'sortable': False, 'style': 'width: 200px;'},
        {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 80px;'},
    ]
    
    # Prepara linhas - preserva índice original antes da ordenação
    # Adiciona índice original a cada cláusula antes de ordenar
    clausulas_com_indice = [(idx, clausula) for idx, clausula in enumerate(clausulas)]
    
    # Ordena mantendo o índice original
    def sort_key_with_index(item):
        idx, clausula = item
        return (sort_key(clausula), idx)  # Usa índice como desempate
    
    clausulas_ordenadas_com_indice = sorted(clausulas_com_indice, key=sort_key_with_index)
    
    rows = []
    for seq_idx, (original_idx, clausula) in enumerate(clausulas_ordenadas_com_indice):
        numero = clausula.get('numero', '')
        titulo = clausula.get('titulo', 'Sem título')
        tipo = clausula.get('tipo_clausula', '')
        status = clausula.get('status', 'Pendente')
        
        # Formata prazos
        prazo_seg = formatar_data_para_exibicao(clausula.get('prazo_seguranca', ''))
        prazo_fatal = formatar_data_para_exibicao(clausula.get('prazo_fatal', ''))
        prazos_display = ''
        if prazo_seg and prazo_seg != '-' and prazo_fatal and prazo_fatal != '-':
            prazos_display = f'{prazo_seg} | {prazo_fatal}'
        elif prazo_seg and prazo_seg != '-':
            prazos_display = f'Seg: {prazo_seg}'
        elif prazo_fatal and prazo_fatal != '-':
            prazos_display = f'Fatal: {prazo_fatal}'
        else:
            prazos_display = '-'
        
        rows.append({
            'numero_seq': seq_idx + 1,
            'numero_clausula': numero if numero else '-',
            'titulo': titulo,
            'tipo': tipo if tipo else '-',
            'status': status,
            'prazos': prazos_display,
            'acoes': '',
            '_original_index': original_idx,  # Índice original na lista não ordenada
            '_clausula_data': clausula  # Dados completos
        })
    
    # CSS para estilização da tabela de cláusulas
    clausulas_table_css = '''
        .clausulas-table .q-table__top {
            padding: 8px 12px;
        }
        .clausulas-table .q-table tbody tr:hover {
            background-color: #f9fafb !important;
        }
        .clausulas-table .q-table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        .clausulas-table .q-table tbody tr:nth-child(odd) {
            background-color: #ffffff;
        }
        .clausulas-table .q-table thead th {
            background-color: #f3f4f6;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }
    '''
    ui.add_head_html(f'<style>{clausulas_table_css}</style>')
    
    # Cria tabela
    table = ui.table(
        columns=columns,
        rows=rows,
        row_key='numero_seq',
        pagination={'rowsPerPage': 10}
    ).classes('w-full clausulas-table')
    
    # Slot para número sequencial
    table.add_slot('body-cell-numero_seq', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <span class="text-sm text-gray-600 font-medium">{{ props.value }}</span>
        </q-td>
    ''')
    
    # Slot para número da cláusula
    table.add_slot('body-cell-numero_clausula', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <span class="text-xs text-gray-700">{{ props.value || '-' }}</span>
        </q-td>
    ''')
    
    # Slot para título (pode quebrar linha)
    table.add_slot('body-cell-titulo', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <div class="text-sm font-medium text-gray-800" style="white-space: normal; word-wrap: break-word;">
                {{ props.value || 'Sem título' }}
            </div>
        </q-td>
    ''')
    
    # Slot para tipo
    table.add_slot('body-cell-tipo', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <q-badge 
                v-if="props.value && props.value !== '-'"
                :color="props.value.toLowerCase().includes('geral') ? 'blue' : 'purple'" 
                :label="props.value" 
                style="text-transform: capitalize;" />
            <span v-else class="text-gray-400 text-xs">—</span>
        </q-td>
    ''')
    
    # Slot para status com badge colorido
    table.add_slot('body-cell-status', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <q-badge 
                :color="!props.value || props.value.toLowerCase().includes('cumprida') ? 'green' : 
                        props.value.toLowerCase().includes('pendente') ? 'orange' : 
                        props.value.toLowerCase().includes('atrasada') ? 'red' : 'grey'" 
                :label="props.value || 'Pendente'" />
        </q-td>
    ''')
    
    # Slot para prazos
    table.add_slot('body-cell-prazos', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <span class="text-xs text-gray-700">{{ props.value || '-' }}</span>
        </q-td>
    ''')
    
    # Slot para ações (editar e deletar)
    table.add_slot('body-cell-acoes', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <div style="display: flex; justify-content: center; gap: 4px;">
                <q-btn 
                    flat dense round 
                    icon="edit" 
                    size="sm" 
                    color="primary"
                    @click="$parent.$emit('editClausula', props.row._original_index)"
                />
                <q-btn 
                    flat dense round 
                    icon="delete" 
                    size="sm" 
                    color="red"
                    @click="$parent.$emit('deleteClausula', props.row._original_index)"
                />
            </div>
        </q-td>
    ''')
    
    # Handlers para ações com validação de índices
    if on_edit:
        def handle_edit(e):
            try:
                index = e.args
                if index is not None and isinstance(index, int):
                    # Valida que o índice está dentro dos limites
                    if 0 <= index < len(clausulas):
                        on_edit(index)
                    else:
                        ui.notify('Índice de cláusula inválido!', type='warning')
                else:
                    ui.notify('Erro ao editar cláusula: índice inválido.', type='warning')
            except Exception as ex:
                ui.notify(f'Erro ao editar cláusula: {str(ex)}', type='negative')
        table.on('editClausula', handle_edit)
    
    if on_delete:
        def handle_delete(e):
            try:
                index = e.args
                if index is not None and isinstance(index, int):
                    # Valida que o índice está dentro dos limites
                    if 0 <= index < len(clausulas):
                        on_delete(index)
                    else:
                        ui.notify('Índice de cláusula inválido!', type='warning')
                else:
                    ui.notify('Erro ao deletar cláusula: índice inválido.', type='warning')
            except Exception as ex:
                ui.notify(f'Erro ao deletar cláusula: {str(ex)}', type='negative')
        table.on('deleteClausula', handle_delete)
    
    return table

