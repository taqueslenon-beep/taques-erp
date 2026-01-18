"""
Página principal do módulo Processos do workspace Visão Geral.
Rota: /visao-geral/processos

CORREÇÃO (23/12/2025): Adicionado logging detalhado e tratamento robusto
para identificar e corrigir erros "Invalid value" em componentes UI.
"""
import logging
import traceback
from nicegui import ui
from mini_erp.core import layout
from mini_erp.auth import is_authenticated
from mini_erp.gerenciadores.gerenciador_workspace import definir_workspace
from mini_erp.firebase_config import ensure_firebase_initialized
from ..database import listar_processos, buscar_processo
from ..modal.modal_processo import abrir_modal_processo
from .tabela import (
    TABELA_PROCESSOS_CSS, COLUMNS, BODY_SLOT_AREA, BODY_SLOT_STATUS, BODY_SLOT_ACOES,
    BODY_SLOT_NUCLEO, converter_processo_para_row
)
from .filtros import (
    criar_barra_pesquisa, criar_filtros, criar_botao_limpar_filtros, filtrar_rows
)

# Configura logger do módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    """
    Renderiza o conteúdo da página de processos.
    
    CORREÇÃO (23/12/2025): Adicionado logging detalhado em cada etapa
    para identificar origem de erros "Invalid value".
    """
    logger.info("[PROCESSOS] ========== INICIANDO RENDERIZAÇÃO ==========")
    
    try:
        with layout('Processos', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Processos', None)]):
            logger.debug("[PROCESSOS] Layout criado com sucesso")
            
            # Aplicar CSS padrão de tabelas de processos
            ui.add_head_html(TABELA_PROCESSOS_CSS)
            logger.debug("[PROCESSOS] CSS aplicado")

            # Estado dos filtros (busca, área, status e prioridade)
            # CORREÇÃO: Usar string vazia em vez de None para evitar "Invalid value"
            filtros = {
                'busca': '',      # String vazia, não None
                'area': '',       # CORRIGIDO: era None
                'status': '',     # CORRIGIDO: era None  
                'prioridade': '', # CORRIGIDO: era None
            }
            logger.debug(f"[PROCESSOS] Filtros inicializados: {filtros}")

            # Referência para o refreshable e loading
            refresh_ref = {'func': None}
            loading_ref = {'row': None, 'hidden': False}

            # Loading inicial
            loading_row = ui.row().classes('w-full justify-center py-8')
            with loading_row:
                ui.spinner('dots', size='lg', color='primary')
                ui.label('Carregando processos...').classes('ml-3 text-gray-500')
            loading_ref['row'] = loading_row

            def hide_loading():
                """Esconde loading de forma segura."""
                try:
                    if not loading_ref['hidden'] and loading_ref['row']:
                        loading_ref['row'].set_visibility(False)
                        loading_ref['hidden'] = True
                except Exception as e:
                    logger.warning(f"Erro ao esconder loading: {e}")

            # Barra de pesquisa e botões de ação
            try:
                with ui.row().classes('w-full items-center gap-2 sm:gap-4 mb-4 flex-wrap'):
                    search_input = criar_barra_pesquisa(filtros, lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)

                    # Botão Novo Processo
                    def novo_processo():
                        abrir_modal_processo(on_save=lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)

                    ui.button('Novo Processo', icon='add', on_click=novo_processo).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')
            except Exception as e:
                logger.error(f"Erro ao criar barra de pesquisa: {e}")
                hide_loading()
                raise

            # Linha de filtros
            try:
                with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
                    filtro_components = criar_filtros(filtros, lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)
                    criar_botao_limpar_filtros(filtros, search_input, filtro_components, lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None)
            except Exception as e:
                logger.error(f"Erro ao criar filtros: {e}")
                hide_loading()
                raise

            # Função para renderizar tabela
            @ui.refreshable
            def render_table():
                """
                Renderiza tabela de processos.
                
                CORREÇÃO (23/12/2025): Adicionado logging detalhado e validação
                de cada row antes de passar para ui.table.
                """
                logger.info("[PROCESSOS] ========== RENDER_TABLE INICIADO ==========")
                
                # Esconde loading PRIMEIRO (antes de qualquer operação)
                hide_loading()
                
                try:
                    # Carrega processos com log de debug
                    logger.info("[PROCESSOS] Buscando processos do Firestore...")
                    
                    # CORREÇÃO: Converte filtros vazios para None antes de consultar
                    filtros_query = {}
                    for key, value in filtros.items():
                        if value and value != '':
                            filtros_query[key] = value
                    logger.debug(f"[PROCESSOS] Filtros para query: {filtros_query}")
                    
                    todos_processos = listar_processos(filtros_query if filtros_query else None)
                    total = len(todos_processos) if todos_processos else 0
                    logger.info(f"[PROCESSOS] {total} processos encontrados")
                    
                    if not todos_processos:
                        logger.warning("[PROCESSOS] Nenhum processo retornado do Firestore")
                        with ui.card().classes('w-full p-8 flex justify-center items-center'):
                            ui.label('Nenhum processo encontrado.').classes('text-gray-400 italic')
                        return
                    
                    # Converte para formato da tabela COM VALIDAÇÃO
                    logger.info("[PROCESSOS] Convertendo processos para formato de tabela...")
                    rows = []
                    for idx, p in enumerate(todos_processos):
                        try:
                            row = converter_processo_para_row(p)
                            
                            # Validação: verifica se há valores None que podem causar erro
                            valores_none = [k for k, v in row.items() if v is None]
                            if valores_none:
                                logger.warning(f"[PROCESSOS] Row {idx} tem valores None: {valores_none}")
                                # Corrige valores None
                                for k in valores_none:
                                    if k.endswith('_list'):
                                        row[k] = []
                                    elif k.startswith('is_'):
                                        row[k] = False
                                    else:
                                        row[k] = ''
                            
                            rows.append(row)
                        except Exception as e:
                            logger.error(f"[PROCESSOS] Erro ao converter processo {idx}: {e}")
                            logger.error(f"[PROCESSOS] Dados do processo: {p.get('_id', 'SEM_ID')}")
                            traceback.print_exc()
                    
                    logger.info(f"[PROCESSOS] {len(rows)} rows convertidas com sucesso")
                    
                    # Aplica filtros adicionais
                    logger.debug("[PROCESSOS] Aplicando filtros adicionais...")
                    filtered_rows = filtrar_rows(rows, filtros)
                    logger.info(f"[PROCESSOS] {len(filtered_rows)} rows após filtros")
                    
                    if not filtered_rows:
                        with ui.card().classes('w-full p-8 flex justify-center items-center'):
                            ui.label('Nenhum processo encontrado para os filtros atuais.').classes('text-gray-400 italic')
                        return
                    
                    # VALIDAÇÃO FINAL: Log de amostra de dados
                    if filtered_rows:
                        amostra = filtered_rows[0]
                        logger.debug(f"[PROCESSOS] Amostra de row (primeira): {list(amostra.keys())}")
                        for campo, valor in amostra.items():
                            logger.debug(f"[PROCESSOS]   {campo}: {type(valor).__name__} = {repr(valor)[:50]}")
                    
                    # Cria tabela com evento row-click habilitado
                    logger.info("[PROCESSOS] Criando ui.table...")
                    table = ui.table(columns=COLUMNS, rows=filtered_rows, row_key='_id', pagination={'rowsPerPage': 20}).classes('w-full')
                    logger.info("[PROCESSOS] ui.table criada com sucesso")
                    
                    # Handler para clique no botão editar - abre modal de edição
                    def handle_edit_click(e):
                        """Handler para clique no botão editar do processo."""
                        from datetime import datetime
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] ========== BOTÃO EDITAR ==========")
                        print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] Args: {e.args}")
                        
                        clicked_row = e.args
                        if clicked_row and '_id' in clicked_row:
                            processo_id = clicked_row['_id']
                            titulo_preview = clicked_row.get('title', clicked_row.get('titulo', 'SEM_TITULO'))[:50]
                            print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] Processo ID: {processo_id}")
                            print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] Título: {titulo_preview}")
                            
                            # Busca dados completos do Firestore
                            print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] Buscando no Firestore...")
                            processo_completo = buscar_processo(processo_id)
                            
                            if processo_completo:
                                print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] ✓ Dados encontrados!")
                                print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] Campos: {list(processo_completo.keys())}")
                                
                                abrir_modal_processo(
                                    processo=processo_completo,
                                    on_save=lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None
                                )
                                print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] ✓ Modal aberto com sucesso")
                            else:
                                print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] ❌ Processo NÃO encontrado!")
                                ui.notify(f'Processo não encontrado: {processo_id}', type='negative')
                        else:
                            print(f"[{timestamp}] [PROCESSOS_VG] [EDIT] ❌ Dados inválidos")
                            ui.notify('Erro: dados do processo não recebidos.', type='negative')
                    
                    # Registra evento 'edit' emitido pelo botão no slot
                    table.on('edit', handle_edit_click)
                    
                    # Slots customizados
                    # Slot para coluna de ações (botão editar)
                    table.add_slot('body-cell-acoes', BODY_SLOT_ACOES)
                    
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
                    
                    # Slot para núcleo
                    table.add_slot('body-cell-nucleo', BODY_SLOT_NUCLEO)
                    
                    # Slot para área
                    table.add_slot('body-cell-area', BODY_SLOT_AREA)
                    
                    # Slot para título - estilização (clique é capturado pelo row-click)
                    table.add_slot('body-cell-title', '''
                        <q-td :props="props" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 280px; padding: 8px 12px; vertical-align: middle; position: relative; cursor: pointer;">
                            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                <span 
                                    class="text-sm font-medium hover:text-[#00523C] hover:underline" 
                                    style="line-height: 1.4; color: #223631; user-select: none;">
                                    {{ props.value }}
                                </span>
                                <q-badge 
                                    v-if="props.row.prioridade"
                                    :style="props.row.prioridade === 'P1' ? 'background-color: #DC2626; color: white;' : 
                                            props.row.prioridade === 'P2' ? 'background-color: #CA8A04; color: white;' : 
                                            props.row.prioridade === 'P3' ? 'background-color: #2563EB; color: white;' : 
                                            'background-color: #6B7280; color: white;'"
                                    class="px-2 py-0.5"
                                    style="font-weight: 600; font-size: 10px; border-radius: 9999px;"
                                >
                                    {{ props.row.prioridade }}
                                </q-badge>
                            </div>
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
                    
                    # Slot para número (com link clicável se houver)
                    table.add_slot('body-cell-number', '''
                        <q-td :props="props" style="vertical-align: middle; padding: 6px 10px;">
                            <div style="display: flex; align-items: center; gap: 4px;">
                                <a v-if="props.value && props.row.link" 
                                   :href="props.row.link"
                                   target="_blank"
                                   class="process-number-link"
                                   style="font-size: 11px; font-weight: normal; color: #0066cc; line-height: 1.4; font-family: inherit; text-decoration: underline; cursor: pointer;"
                                   @click.stop>
                                    {{ props.value }}
                                </a>
                                <span v-else-if="props.value" 
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
                    logger.error(f"[PROCESSOS] Erro ao renderizar tabela: {e}")
                    import traceback
                    traceback.print_exc()
                    # Garante que loading está escondido mesmo em caso de erro
                    hide_loading()
                    with ui.column().classes('w-full items-center py-8'):
                        ui.icon('error', size='48px', color='negative')
                        ui.label('Erro ao carregar processos').classes('text-lg text-gray-600 mt-2')
                        ui.label(f'Erro: {str(e)}').classes('text-sm text-gray-400')
                        # Botão para tentar novamente
                        ui.button('Tentar novamente', icon='refresh', on_click=lambda: refresh_ref['func'].refresh() if refresh_ref['func'] else None).props('color=primary outline').classes('mt-4')

            # Guarda referência
            refresh_ref['func'] = render_table
            
            # Renderiza tabela com tratamento de erro
            try:
                logger.info("[PROCESSOS] Iniciando renderização da tabela...")
                render_table()
                logger.info("[PROCESSOS] Tabela renderizada com sucesso")
            except Exception as e:
                logger.error(f"[PROCESSOS] Erro crítico ao renderizar tabela: {e}")
                hide_loading()
                import traceback
                traceback.print_exc()
            
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

