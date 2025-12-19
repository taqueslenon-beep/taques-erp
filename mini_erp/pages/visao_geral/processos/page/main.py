"""
Página principal do módulo Processos do workspace Visão Geral.
Rota: /visao-geral/processos
"""
from nicegui import ui
from mini_erp.core import layout
from mini_erp.auth import is_authenticated
from mini_erp.gerenciadores.gerenciador_workspace import definir_workspace
from mini_erp.firebase_config import ensure_firebase_initialized
from ..database import listar_processos, buscar_processo
from ..modal.modal_processo import abrir_modal_processo
from .tabela import (
    TABELA_PROCESSOS_CSS, COLUMNS, BODY_SLOT_AREA, BODY_SLOT_STATUS,
    converter_processo_para_row
)
from .filtros import (
    criar_barra_pesquisa, criar_filtros, criar_botao_limpar_filtros, filtrar_rows
)


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

            # Estado dos filtros
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
                search_input = criar_barra_pesquisa(filtros, lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)

                # Botão Novo Processo
                def novo_processo():
                    abrir_modal_processo(on_save=lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)

                ui.button('Novo Processo', icon='add', on_click=novo_processo).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')

            # Linha de filtros
            with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
                filtro_components = criar_filtros(filtros, lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)
                criar_botao_limpar_filtros(filtros, search_input, filtro_components, lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)

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
                    rows = [converter_processo_para_row(p) for p in todos_processos]
                    
                    # Aplica filtros adicionais
                    filtered_rows = filtrar_rows(rows, filtros)
                    
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
                                abrir_modal_processo(
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

