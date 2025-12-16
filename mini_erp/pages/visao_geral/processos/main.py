"""
Página principal do módulo Processos do workspace Visão Geral.
Rota: /visao-geral/processos
Visualização em Tabela padronizada (unificada com /processos).
"""
from nicegui import ui
from datetime import datetime
from ....core import layout, PRIMARY_COLOR
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from ....firebase_config import ensure_firebase_initialized
from .database import listar_processos, excluir_processo, buscar_processo
from .processo_dialog import abrir_dialog_processo, confirmar_exclusao
from ....pages.processos.ui_components import TABELA_PROCESSOS_CSS, BODY_SLOT_AREA, BODY_SLOT_STATUS

# Importa constantes do módulo processos principal para consistência
from ....pages.processos.models import (
    AREA_OPTIONS, STATUS_OPTIONS, PROCESS_TYPE_OPTIONS
)


def _converter_processo_para_row(processo: dict) -> dict:
    """
    Converte processo do formato vg_processos para formato esperado pela tabela.
    
    Args:
        processo: Dicionário do processo no formato vg_processos
        
    Returns:
        Dicionário no formato esperado pela tabela
    """
    # Processa data de abertura
    data_abertura_raw = processo.get('data_abertura') or ''
    data_abertura_display = ''
    data_abertura_sort = ''
    
    if data_abertura_raw:
        try:
            # Tenta converter timestamps ISO para formato DD/MM/AAAA
            if isinstance(data_abertura_raw, str) and 'T' in data_abertura_raw:
                # É um timestamp ISO
                dt = datetime.fromisoformat(data_abertura_raw.replace('Z', '+00:00'))
                data_abertura_display = dt.strftime('%d/%m/%Y')
                data_abertura_sort = dt.strftime('%Y/%m/%d')
            else:
                data_abertura_raw = str(data_abertura_raw).strip()
                
                # Formato: AAAA (apenas ano)
                if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                    data_abertura_display = data_abertura_raw
                    data_abertura_sort = f"{data_abertura_raw}/00/00"
                # Formato: MM/AAAA (mês e ano)
                elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                    partes = data_abertura_raw.split('/')
                    if len(partes) == 2:
                        data_abertura_display = data_abertura_raw
                        data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
                # Formato: DD/MM/AAAA (completa)
                elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                    partes = data_abertura_raw.split('/')
                    if len(partes) == 3:
                        data_abertura_display = data_abertura_raw
                        data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
                else:
                    data_abertura_display = data_abertura_raw
        except Exception:
            data_abertura_display = str(data_abertura_raw)
    
    # Extrai clientes (formato esperado: lista de strings)
    clientes_nomes = processo.get('clientes_nomes', [])
    if not isinstance(clientes_nomes, list):
        clientes_nomes = [str(clientes_nomes)] if clientes_nomes else []
    clients_list = [str(c).upper() for c in clientes_nomes if c]
    
    # Extrai casos vinculados
    caso_titulo = processo.get('caso_titulo', '')
    cases_list = [caso_titulo] if caso_titulo else []
    
    # Mapeia parte contrária
    parte_contraria = processo.get('parte_contraria', '')
    opposing_list = [parte_contraria.upper()] if parte_contraria else []
    
    return {
        '_id': processo.get('_id', ''),
        'data_abertura': data_abertura_display,
        'data_abertura_sort': data_abertura_sort,
        'title': processo.get('titulo', 'Sem título'),
        'title_raw': processo.get('titulo', 'Sem título'),
        'number': processo.get('numero', ''),
        'clients_list': clients_list,
        'opposing_list': opposing_list,
        'cases_list': cases_list,
        'system': processo.get('sistema_processual', ''),
        'status': processo.get('status', 'Ativo'),
        'area': processo.get('area', ''),
        'link': '',  # vg_processos não tem campo link
        'is_third_party_monitoring': False,
        'is_desdobramento': False,
    }


# Colunas da tabela (mesmas da visualização padrão)
COLUMNS = [
    {'name': 'data_abertura', 'label': 'Data', 'field': 'data_abertura_sort', 'align': 'center', 'sortable': True, 'style': 'width: 90px; min-width: 90px;'},
    {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True, 'style': 'width: 120px; max-width: 120px;'},
    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True, 'style': 'width: 280px; max-width: 280px;'},
    {'name': 'cases', 'label': 'Casos', 'field': 'cases', 'align': 'left', 'style': 'width: 180px; min-width: 180px;'},
    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 180px;'},
    {'name': 'clients', 'label': 'Clientes', 'field': 'clients', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
    {'name': 'opposing', 'label': 'Parte Contrária', 'field': 'opposing', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 150px;'},
]


@ui.page('/visao-geral/processos')
def processos_visao_geral():
    """Página de Processos do workspace Visão geral do escritório."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return

        # Garante que Firebase está inicializado
        ensure_firebase_initialized()

        # Define o workspace
        definir_workspace('visao_geral_escritorio')

        _renderizar_pagina_processos()
    except Exception as e:
        print(f"[ERRO CRÍTICO] Erro na função processos_visao_geral: {e}")
        import traceback
        traceback.print_exc()
        # Renderiza página de erro
        with layout('Processos - Erro', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Processos', None)]):
            with ui.column().classes('w-full items-center py-16'):
                ui.icon('error', size='64px', color='negative')
                ui.label('Erro ao inicializar página de processos').classes('text-xl font-bold text-gray-600 mt-4')
                ui.label(f'Erro: {str(e)}').classes('text-gray-400 mt-2')
                ui.button('Voltar ao Painel', icon='arrow_back', on_click=lambda: ui.navigate.to('/visao-geral/painel')).props('color=primary').classes('mt-4')


def _renderizar_pagina_processos():
    """Renderiza o conteúdo da página de processos."""
    try:
        with layout('Processos', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Processos', None)]):
            # Aplicar CSS padrão de tabelas de processos
            ui.add_head_html(TABELA_PROCESSOS_CSS)

            # Estado dos filtros (padronizado com visualização principal)
            filtros = {
                'busca': '',
                'area': None,
                'status': None,
            }

            # Referência para o refreshable
            refresh_ref = {'func': None}

            # Loading inicial
            loading_row = ui.row().classes('w-full justify-center py-8')
            with loading_row:
                ui.spinner('dots', size='lg', color='primary')
                ui.label('Carregando processos...').classes('ml-3 text-gray-500')

            # Barra de pesquisa e botões de ação
            with ui.row().classes('w-full items-center gap-2 sm:gap-4 mb-4 flex-wrap'):
                # Campo de busca
                with ui.input(placeholder='Pesquisar processos por título, número...').props('outlined dense clearable').classes('flex-grow w-full sm:w-auto sm:max-w-xl') as search_input:
                    with search_input.add_slot('prepend'):
                        ui.icon('search').classes('text-gray-400')
                
                # Callback para atualizar pesquisa
                def on_search_change():
                    filtros['busca'] = search_input.value if search_input.value else ''
                    if refresh_ref['func']:
                        refresh_ref['func'].refresh()
                
                search_input.on('update:model-value', on_search_change)

                # Botão Novo Processo
                def novo_processo():
                    abrir_dialog_processo(on_save=lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)

                ui.button('Novo Processo', icon='add', on_click=novo_processo).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')

            # Linha de filtros
            with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
                ui.label('Filtros:').classes('text-gray-600 font-medium text-sm w-full sm:w-auto')
                
                # Filtro por área
                area_options = [''] + [a for a in AREA_OPTIONS if a]
                area_select = ui.select(area_options, label='Área', value='').props('clearable dense outlined').classes('w-full sm:w-auto min-w-[100px] sm:min-w-[120px]')
                area_select.style('font-size: 12px; border-color: #d1d5db;')
                
                def on_area_change():
                    filtros['area'] = area_select.value if area_select.value else None
                    if refresh_ref['func']:
                        refresh_ref['func'].refresh()
                
                area_select.on('update:model-value', on_area_change)

                # Filtro por status
                status_options = [''] + [s for s in STATUS_OPTIONS if s]
                status_select = ui.select(status_options, label='Status', value='').props('clearable dense outlined').classes('w-full sm:w-auto min-w-[100px] sm:min-w-[140px]')
                status_select.style('font-size: 12px; border-color: #d1d5db;')
                
                def on_status_change():
                    filtros['status'] = status_select.value if status_select.value else None
                    if refresh_ref['func']:
                        refresh_ref['func'].refresh()
                
                status_select.on('update:model-value', on_status_change)

                # Botão limpar filtros
                def limpar_filtros():
                    filtros['busca'] = ''
                    filtros['area'] = None
                    filtros['status'] = None
                    search_input.value = ''
                    area_select.value = ''
                    status_select.value = ''
                    if refresh_ref['func']:
                        refresh_ref['func'].refresh()

                ui.button('Limpar', icon='clear_all', on_click=limpar_filtros).props('flat dense').classes('text-xs text-gray-600 w-full sm:w-auto')

            # Função para filtrar rows
            def filter_rows(rows):
                """Aplica filtros aos processos."""
                filtered = rows
                
                # Filtro de pesquisa (título/número)
                if filtros['busca']:
                    term = filtros['busca'].lower()
                    filtered = [r for r in filtered if term in (r.get('title_raw') or r.get('title') or '').lower() or term in (r.get('number') or '').lower()]
                
                # Filtro de área
                if filtros['area']:
                    filtered = [r for r in filtered if (r.get('area') or '').strip() == filtros['area'].strip()]
                
                # Filtro de status
                if filtros['status']:
                    filtered = [r for r in filtered if (r.get('status') or '').strip() == filtros['status'].strip()]
                
                return filtered

            # Função para renderizar tabela
            @ui.refreshable
            def render_table():
                """Renderiza tabela de processos."""
                # Esconde loading
                loading_row.set_visibility(False)
                
                try:
                    # Carrega processos
                    todos_processos = listar_processos(filtros)
                    
                    # Converte para formato da tabela
                    rows = [_converter_processo_para_row(p) for p in todos_processos]
                    
                    # Aplica filtros adicionais
                    filtered_rows = filter_rows(rows)
                    
                    if not filtered_rows:
                        with ui.card().classes('w-full p-8 flex justify-center items-center'):
                            ui.label('Nenhum processo encontrado para os filtros atuais.').classes('text-gray-400 italic')
                        return
                    
                    # Cria tabela
                    table = ui.table(columns=COLUMNS, rows=filtered_rows, row_key='_id', pagination={'rowsPerPage': 20}).classes('w-full')
                    
                    # Handler para clique no título (abre modal de edição)
                    def handle_title_click(e):
                        clicked_row = e.args
                        if clicked_row and '_id' in clicked_row:
                            processo_id = clicked_row['_id']
                            processo_completo = buscar_processo(processo_id)
                            if processo_completo:
                                abrir_dialog_processo(
                                    processo=processo_completo,
                                    on_save=lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None
                                )
                    
                    table.on('titleClick', handle_title_click)
                    
                    # Slots customizados
                    # Slot para data de abertura
                    table.add_slot('body-cell-data_abertura', '''
                        <q-td :props="props" 
                              style="text-align: center; padding: 8px 12px; vertical-align: middle;"
                              :data-row-id="props.row._id"
                              :data-is-third-party="false"
                              :data-status="props.row.status || ''">
                            <span v-if="props.row.data_abertura" class="text-xs text-gray-700 font-medium">{{ props.row.data_abertura }}</span>
                            <span v-else class="text-gray-400">—</span>
                        </q-td>
                    ''')
                    
                    # Slot para área
                    table.add_slot('body-cell-area', BODY_SLOT_AREA)
                    
                    # Slot para título (clicável)
                    table.add_slot('body-cell-title', '''
                        <q-td :props="props" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 280px; padding: 8px 12px; vertical-align: middle; position: relative;">
                            <span 
                                class="text-sm cursor-pointer font-medium" 
                                style="line-height: 1.4; color: #223631; user-select: none;"
                                @click="$parent.$emit('titleClick', props.row)">
                                {{ props.value }}
                            </span>
                        </q-td>
                    ''')
                    
                    # Slot para status
                    table.add_slot('body-cell-status', BODY_SLOT_STATUS)
                    
                    # Slot para clientes
                    table.add_slot('body-cell-clients', '''
                        <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 8px 8px;">
                            <div v-if="props.row.clients_list && props.row.clients_list.length > 0" class="flex flex-col gap-0.5">
                                <div v-for="(client, index) in props.row.clients_list" :key="index" class="text-xs text-gray-700 leading-tight font-medium" style="word-wrap: break-word; overflow-wrap: break-word;">
                                    {{ client }}
                                </div>
                            </div>
                            <span v-else class="text-gray-400">—</span>
                        </q-td>
                    ''')
                    
                    # Slot para parte contrária
                    table.add_slot('body-cell-opposing', '''
                        <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 8px 8px;">
                            <div v-if="props.row.opposing_list && props.row.opposing_list.length > 0" class="flex flex-col gap-0.5">
                                <div v-for="(opposing, index) in props.row.opposing_list" :key="index" class="text-xs text-gray-700 leading-tight font-medium" style="word-wrap: break-word; overflow-wrap: break-word;">
                                    {{ opposing }}
                                </div>
                            </div>
                            <span v-else class="text-gray-400">—</span>
                        </q-td>
                    ''')
                    
                    # Slot para casos
                    table.add_slot('body-cell-cases', '''
                        <q-td :props="props" style="vertical-align: middle; padding: 8px 12px;">
                            <div v-if="props.row.cases_list && props.row.cases_list.length > 0" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word;">
                                <span v-for="(caso, index) in props.row.cases_list" :key="index" class="text-xs text-gray-700 font-medium">
                                    {{ caso }}<span v-if="index < props.row.cases_list.length - 1">, </span>
                                </span>
                            </div>
                            <span v-else class="text-gray-400">—</span>
                        </q-td>
                    ''')
                    
                    # Slot para número
                    table.add_slot('body-cell-number', '''
                        <q-td :props="props" style="vertical-align: middle; padding: 6px 10px;">
                            <div style="display: flex; align-items: center; gap: 4px;">
                                <span v-if="props.value" 
                                      class="process-number-text"
                                      style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; font-family: inherit;">
                                    {{ props.value }}
                                </span>
                                <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
                                <q-btn 
                                    v-if="props.value"
                                    flat dense round 
                                    icon="content_copy" 
                                    size="xs" 
                                    color="grey"
                                    class="ml-1"
                                    @click.stop="$parent.$emit('copyNumber', props.value)"
                                >
                                    <q-tooltip>Copiar número</q-tooltip>
                                </q-btn>
                            </div>
                        </q-td>
                    ''')
                    
                    # Handler para copiar número
                    def handle_copy_number(e):
                        numero = e.args
                        if numero:
                            numero_escaped = str(numero).replace("'", "\\'")
                            ui.run_javascript(f'''
                                navigator.clipboard.writeText('{numero_escaped}').then(() => {{
                                }}).catch(err => {{
                                    console.error('Erro ao copiar:', err);
                                }});
                            ''')
                            ui.notify("Número copiado!", type="positive", position="top", timeout=1500)
                    
                    table.on('copyNumber', handle_copy_number)
                    
                except Exception as e:
                    print(f"[ERRO] Erro ao renderizar tabela: {e}")
                    import traceback
                    traceback.print_exc()
                    with ui.column().classes('w-full items-center py-8'):
                        ui.icon('error', size='48px', color='negative')
                        ui.label('Erro ao carregar processos').classes('text-lg text-gray-600 mt-2')
                        ui.label(f'Erro: {str(e)}').classes('text-sm text-gray-400')

            # Guarda referência
            refresh_ref['func'] = render_table
            
            # Renderiza tabela
            render_table()
            
    except Exception as e:
        print(f"[ERRO CRÍTICO] Erro ao renderizar página de processos: {e}")
        import traceback
        traceback.print_exc()
        with layout('Processos - Erro', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Processos', None)]):
            with ui.column().classes('w-full items-center py-16'):
                ui.icon('error', size='64px', color='negative')
                ui.label('Erro ao carregar página de processos').classes('text-xl font-bold text-gray-600 mt-4')
                ui.label(f'Erro: {str(e)}').classes('text-gray-400 mt-2')
                ui.button('Voltar ao Painel', icon='arrow_back', on_click=lambda: ui.navigate.to('/visao-geral/painel')).props('color=primary').classes('mt-4')
