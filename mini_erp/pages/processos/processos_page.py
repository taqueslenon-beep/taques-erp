"""
processos_page.py - Página simplificada do módulo de Processos.

Exibe todos os processos cadastrados no Firebase em uma tabela limpa.
"""

from nicegui import ui
from ...core import layout, get_processes_list, get_clients_list, get_opposing_parties_list, get_cases_list, invalidate_cache
from ...auth import is_authenticated
from .ui_components import BODY_SLOT_AREA, BODY_SLOT_STATUS
from .process_dialog import render_process_dialog


def _get_priority_name(name: str, people_list: list) -> str:
    """
    Busca pessoa na lista e retorna nome com prioridade:
    sigla (nickname) > display_name > full_name
    Sempre em MAIÚSCULAS.
    """
    if not name:
        return ''
    
    # Busca pessoa na lista pelo nome
    person = None
    for p in people_list:
        full_name = p.get('full_name') or p.get('name', '')
        if full_name == name or p.get('_id') == name:
            person = p
            break
    
    if person:
        # Prioridade: nickname (sigla) > display_name > full_name
        if person.get('nickname'):
            return person['nickname'].upper()
        if person.get('display_name'):
            return person['display_name'].upper()
        return (person.get('full_name') or person.get('name', '')).upper()
    
    # Se não encontrou, retorna o nome original em maiúsculas
    return name.upper() if name else ''


def _format_names_list(names_raw, people_list: list) -> list:
    """
    Formata lista de nomes aplicando prioridade e MAIÚSCULAS.
    Retorna lista para exibição vertical.
    """
    if not names_raw:
        return []
    
    if isinstance(names_raw, list):
        formatted = [_get_priority_name(str(n), people_list) for n in names_raw if n]
        return formatted
    else:
        name = _get_priority_name(str(names_raw), people_list)
        return [name] if name else []


def fetch_processes():
    """
    Busca processos do Firestore e formata para exibição.
    
    Returns:
        Lista de dicionários prontos para a tabela.
    """
    try:
        raw = get_processes_list()
        
        # Carrega listas de pessoas para buscar siglas/display_names
        clients_list = get_clients_list()
        opposing_list = get_opposing_parties_list()
        all_people = clients_list + opposing_list
        
        rows = []
        for proc in raw:
            # Extrai e formata clientes (prioridade + MAIÚSCULAS) - retorna lista
            clients_raw = proc.get('clients') or proc.get('client') or []
            clients_list = _format_names_list(clients_raw, all_people)

            # Extrai e formata partes contrárias (prioridade + MAIÚSCULAS) - retorna lista
            opposing_raw = proc.get('opposing_parties') or []
            opposing_list = _format_names_list(opposing_raw, all_people)

            # Extrai casos vinculados - retorna lista
            cases_raw = proc.get('cases') or []
            if isinstance(cases_raw, list):
                cases_list = [str(c) for c in cases_raw if c]
            else:
                cases_list = [str(cases_raw)] if cases_raw else []

            rows.append({
                '_id': proc.get('_id', ''),
                'title': proc.get('title') or proc.get('searchable_title') or '(sem título)',
                'number': proc.get('number') or '',
                'clients_list': clients_list,
                'opposing_list': opposing_list,
                'cases_list': cases_list,
                'system': proc.get('system') or '',
                'status': proc.get('status') or '',
                'area': proc.get('area') or proc.get('area_direito') or '',
                'link': proc.get('link') or '',
            })
        # Ordena por título
        rows.sort(key=lambda r: (r.get('title') or '').lower())
        return rows
    except Exception as e:
        print(f"Erro ao buscar processos: {e}")
        return []


# Colunas da tabela com larguras otimizadas
COLUMNS = [
    {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True, 'style': 'width: 120px; max-width: 120px;'},
    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True, 'style': 'width: 280px; max-width: 280px;'},
    {'name': 'cases', 'label': 'Casos', 'field': 'cases', 'align': 'left', 'style': 'width: 180px; min-width: 180px;'},
    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 180px;'},
    {'name': 'clients', 'label': 'Clientes', 'field': 'clients', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
    {'name': 'opposing', 'label': 'Parte Contrária', 'field': 'opposing', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 150px;'},
]


@ui.page('/processos')
def processos():
    """Página principal de processos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    with layout('Processos', breadcrumbs=[('Processos', None)]):
        # Função de callback para atualizar após salvar processo
        def on_process_saved():
            invalidate_cache('processes')
            refresh_table()
        
        # Criar modal completo com barra lateral (uma vez para toda a página)
        process_dialog, open_process_modal = render_process_dialog(
            on_success=on_process_saved
        )
        
        # Estado dos filtros (usando variáveis Python simples)
        search_term = {'value': ''}
        filter_area = {'value': ''}
        filter_case = {'value': ''}
        filter_client = {'value': ''}
        filter_parte = {'value': ''}
        filter_opposing = {'value': ''}
        filter_status = {'value': ''}
        
        # Referência para render_table (será definida depois)
        render_table_ref = {'func': None}
        
        # Função para atualizar tabela
        def refresh_table():
            if render_table_ref['func']:
                render_table_ref['func'].refresh()
        
        # Função para extrair opções únicas dos dados
        def get_filter_options():
            all_rows = fetch_processes()
            return {
                'area': [''] + sorted(set([r.get('area', '') for r in all_rows if r.get('area')])),
                'cases': [''] + sorted(set([c for r in all_rows for c in r.get('cases_list', []) if c])),
                'clients': [''] + sorted(set([c for r in all_rows for c in r.get('clients_list', []) if c])),
                'parte': [''] + sorted(set([c for r in all_rows for c in r.get('clients_list', []) if c])),
                'opposing': [''] + sorted(set([c for r in all_rows for c in r.get('opposing_list', []) if c])),
                'status': [''] + sorted(set([r.get('status', '') for r in all_rows if r.get('status')]))
            }
        
        # Filtros discretos em uma linha
        filter_options = get_filter_options()
        filter_selects = {}
        
        # Função auxiliar para criar filtros discretos
        def create_filter_dropdown(label, options, state_dict, icon=None):
            select = ui.select(options, label=label, value='').props('clearable dense outlined').classes('min-w-[140px]')
            if icon:
                select.props(f'prefix={icon}')
            # Estilo discreto e minimalista
            select.style('font-size: 12px; border-color: #d1d5db;')
            select.classes('filter-select')
            
            # Callback para atualizar filtro quando valor mudar
            def on_filter_change():
                state_dict['value'] = select.value if select.value else ''
                refresh_table()
            
            # Registrar callback
            select.on('update:model-value', on_filter_change)
            return select
        
        # Barra de pesquisa
        with ui.row().classes('w-full items-center mb-3 gap-2'):
            search_input = ui.input('', placeholder='Pesquisar processos...').props('clearable').classes('flex-1')
            search_input.props('prefix=search')
            search_input.style('max-width: 400px; font-size: 13px;')
            
            # Callback para atualizar pesquisa quando valor mudar
            def on_search_change():
                search_term['value'] = search_input.value if search_input.value else ''
                refresh_table()
            
            search_input.on('update:model-value', on_search_change)
            
            # Botões de ação
            ui.button('Novo Processo', icon='add', on_click=lambda: open_process_modal()).props('color=primary')
            
            # Função para atualizar filtros e tabela
            def update_filters_and_table():
                options = get_filter_options()
                filter_selects['area'].options = options['area']
                filter_selects['case'].options = options['cases']
                filter_selects['client'].options = options['clients']
                filter_selects['parte'].options = options['parte']
                filter_selects['opposing'].options = options['opposing']
                filter_selects['status'].options = options['status']
                refresh_table()
            
            ui.button('Atualizar lista', icon='refresh', on_click=lambda: (invalidate_cache('processes'), update_filters_and_table())).props('flat')
            
            # Botão para acessar a visualização "Acesso aos Processos"
            ui.button('Acesso aos Processos', icon='lock_open', on_click=lambda: ui.navigate.to('/processos/acesso')).props('flat')
        
        # Linha de filtros
        with ui.row().classes('w-full items-center mb-4 gap-2 flex-wrap'):
            # Criar filtros
            filter_selects['area'] = create_filter_dropdown('Área', filter_options['area'], filter_area, 'category')
            filter_selects['case'] = create_filter_dropdown('Casos', filter_options['cases'], filter_case, 'folder')
            filter_selects['client'] = create_filter_dropdown('Clientes', filter_options['clients'], filter_client, 'person')
            filter_selects['parte'] = create_filter_dropdown('Parte', filter_options['parte'], filter_parte, 'people')
            filter_selects['opposing'] = create_filter_dropdown('Parte Contrária', filter_options['opposing'], filter_opposing, 'gavel')
            filter_selects['status'] = create_filter_dropdown('Status', filter_options['status'], filter_status, 'flag')
            
            # Botão limpar filtros
            def clear_filters():
                filter_area['value'] = ''
                filter_case['value'] = ''
                filter_client['value'] = ''
                filter_parte['value'] = ''
                filter_opposing['value'] = ''
                filter_status['value'] = ''
                search_term['value'] = ''
                # Limpar valores dos selects
                filter_selects['area'].value = ''
                filter_selects['case'].value = ''
                filter_selects['client'].value = ''
                filter_selects['parte'].value = ''
                filter_selects['opposing'].value = ''
                filter_selects['status'].value = ''
                search_input.value = ''
                refresh_table()
            
            ui.button('Limpar', icon='clear_all', on_click=clear_filters).props('flat dense').classes('text-xs text-gray-600')
        
        # Função de filtragem
        def filter_rows(rows):
            filtered = rows
            
            # Filtro de pesquisa (título)
            if search_term['value']:
                term = search_term['value'].lower()
                filtered = [r for r in filtered if term in (r.get('title') or '').lower()]
            
            # Filtro de área
            if filter_area['value']:
                filtered = [r for r in filtered if r.get('area') == filter_area['value']]
            
            # Filtro de casos
            if filter_case['value']:
                filtered = [r for r in filtered if filter_case['value'] in (r.get('cases_list') or [])]
            
            # Filtro de clientes
            if filter_client['value']:
                filtered = [r for r in filtered if filter_client['value'] in (r.get('clients_list') or [])]
            
            # Filtro de parte
            if filter_parte['value']:
                filtered = [r for r in filtered if filter_parte['value'] in (r.get('clients_list') or [])]
            
            # Filtro de parte contrária
            if filter_opposing['value']:
                filtered = [r for r in filtered if filter_opposing['value'] in (r.get('opposing_list') or [])]
            
            # Filtro de status
            if filter_status['value']:
                filtered = [r for r in filtered if r.get('status') == filter_status['value']]
            
            return filtered

        @ui.refreshable
        def render_table():
            rows = fetch_processes()
            
            # Aplicar filtros
            rows = filter_rows(rows)
            
            if not rows:
                with ui.card().classes('w-full p-8 flex justify-center items-center'):
                    ui.label('Nenhum processo encontrado.').classes('text-gray-400 italic')
                return

            # Slots customizados
            table = ui.table(columns=COLUMNS, rows=rows, row_key='_id', pagination={'rowsPerPage': 20}).classes('w-full')
            
            # Handler para clique no título (abre modal de edição)
            def handle_title_click(e):
                clicked_row = e.args
                if clicked_row and '_id' in clicked_row:
                    # Buscar índice do processo pelo _id
                    process_id = clicked_row['_id']
                    all_processes = get_processes_list()
                    for idx, proc in enumerate(all_processes):
                        if proc.get('_id') == process_id:
                            open_process_modal(idx)
                            break
            
            table.on('titleClick', handle_title_click)
            
            # Slot para área com chips coloridos (pastel)
            table.add_slot('body-cell-area', BODY_SLOT_AREA)
            
            # Slot para título - clicável para abrir modal de edição
            table.add_slot('body-cell-title', '''
                <q-td :props="props" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 280px; padding: 8px 12px;">
                    <span class="text-sm cursor-pointer font-medium" 
                          style="line-height: 1.4; color: #223631;"
                          @click="$parent.$emit('titleClick', props.row)">
                        {{ props.value }}
                    </span>
                </q-td>
            ''')
            
            # Slot para status (idêntico ao módulo Casos)
            table.add_slot('body-cell-status', BODY_SLOT_STATUS)
            
            # Slot para clientes - exibe múltiplos verticalmente em espaço compacto
            table.add_slot('body-cell-clients', '''
                <q-td :props="props" style="white-space: normal; vertical-align: top; max-width: 100px; padding: 8px 8px;">
                    <div v-if="props.row.clients_list && props.row.clients_list.length > 0" class="flex flex-col gap-0.5">
                        <div v-for="(client, index) in props.row.clients_list" :key="index" class="text-xs text-gray-700 leading-tight font-medium" style="word-wrap: break-word; overflow-wrap: break-word;">
                            {{ client }}
                        </div>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para parte contrária - exibe múltiplos verticalmente em espaço compacto
            table.add_slot('body-cell-opposing', '''
                <q-td :props="props" style="white-space: normal; vertical-align: top; max-width: 100px; padding: 8px 8px;">
                    <div v-if="props.row.opposing_list && props.row.opposing_list.length > 0" class="flex flex-col gap-0.5">
                        <div v-for="(opposing, index) in props.row.opposing_list" :key="index" class="text-xs text-gray-700 leading-tight font-medium" style="word-wrap: break-word; overflow-wrap: break-word;">
                            {{ opposing }}
                        </div>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para casos - exibe em linha única com ajuste automático
            table.add_slot('body-cell-cases', '''
                <q-td :props="props" style="vertical-align: top; padding: 8px 12px;">
                    <div v-if="props.row.cases_list && props.row.cases_list.length > 0" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word;">
                        <span v-for="(caso, index) in props.row.cases_list" :key="index" class="text-xs text-gray-700 font-medium">
                            {{ caso }}<span v-if="index < props.row.cases_list.length - 1">, </span>
                        </span>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para número - hyperlink clicável
            table.add_slot('body-cell-number', '''
                <q-td :props="props">
                    <a v-if="props.row.link && props.value" 
                       :href="props.row.link" 
                       target="_blank" 
                       class="text-blue-600 hover:text-blue-800 underline hover:no-underline cursor-pointer">
                        {{ props.value }}
                    </a>
                    <span v-else-if="props.value" class="text-gray-700">{{ props.value }}</span>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
        
        render_table_ref['func'] = render_table
        render_table()
