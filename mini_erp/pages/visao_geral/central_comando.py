"""
Página do módulo "Central de Comando" do workspace "Visão Geral do Escritório".
Estrutura de abas para organizar diferentes funcionalidades administrativas.
"""
from nicegui import ui
from typing import Optional, Dict, Any, Callable
from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated, get_current_user
from ...gerenciadores.gerenciador_workspace import definir_workspace
from .processos_internos.database import (
    criar_processo_interno,
    listar_processos_internos,
    obter_processo_interno,
    atualizar_processo_interno,
    excluir_processo_interno
)
from .processos_internos.constants import (
    CATEGORIAS_PROCESSO_INTERNO,
    CATEGORIAS_DISPLAY,
    PRIORIDADES,
    PRIORIDADE_DISPLAY,
    PRIORIDADE_CORES,
    STATUS_PROCESSO_INTERNO,
    STATUS_DISPLAY
)


@ui.page('/visao-geral/central-comando')
def central_comando():
    """
    Página da Central de Comando do workspace "Visão Geral do Escritório".
    Estrutura de abas para organizar funcionalidades administrativas.
    """
    # Verifica autenticação
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Define workspace como "Visão Geral do Escritório"
    definir_workspace('visao_geral_escritorio')
    
    # Renderiza página com layout padrão
    with layout('Central de Comando', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Central de Comando', None)]):
        # Container principal
        with ui.column().classes('w-full gap-4'):
            # Abas principais do módulo
            with ui.tabs().classes('w-full').props('align=left no-caps') as main_tabs:
                processos_internos_tab = ui.tab('Processos Internos', icon='work')
            
            # Painéis das abas
            with ui.tab_panels(main_tabs, value=processos_internos_tab).classes('w-full bg-white p-4 rounded shadow-sm'):
                
                # ============================================
                # ABA: PROCESSOS INTERNOS
                # ============================================
                with ui.tab_panel(processos_internos_tab):
                    _render_aba_processos_internos()


def _render_aba_processos_internos():
    """
    Renderiza o conteúdo da aba "Processos Internos".
    Inclui cabeçalho, botão de cadastro, filtros e tabela de listagem.
    """
    # Container principal da aba
    with ui.column().classes('w-full gap-4'):
        # Filtros (definidos primeiro para serem usados na função refreshable)
        filtros_container = ui.column().classes('w-full gap-2')
        with filtros_container:
            with ui.row().classes('w-full gap-4 items-end'):
                # Busca por título
                busca_input = ui.input(
                    'Buscar por título',
                    placeholder='Digite para buscar...'
                ).classes('flex-1').props('clearable')
                
                # Filtro por categoria
                categoria_select = ui.select(
                    {cat: CATEGORIAS_DISPLAY[cat] for cat in CATEGORIAS_PROCESSO_INTERNO},
                    label='Categoria',
                    value=None
                ).classes('w-48').props('clearable')
                
                # Filtro por prioridade
                prioridade_select = ui.select(
                    {p: PRIORIDADE_DISPLAY[p] for p in PRIORIDADES},
                    label='Prioridade',
                    value=None
                ).classes('w-48').props('clearable')
                
                # Botão limpar filtros
                ui.button(
                    'Limpar Filtros',
                    icon='clear',
                    on_click=lambda: _limpar_filtros(
                        busca_input, categoria_select, prioridade_select
                    )
                ).props('outline')
        
        # Tabela de processos internos (refreshable)
        tabela_container = ui.column().classes('w-full')
        
        @ui.refreshable
        def _atualizar_tabela_processos():
            """Atualiza a tabela de processos internos."""
            # Limpa container anterior
            tabela_container.clear()
            
            # Obtém filtros
            filtros = {}
            if busca_input.value:
                filtros['busca'] = busca_input.value
            if categoria_select.value:
                filtros['categoria'] = categoria_select.value
            if prioridade_select.value:
                filtros['prioridade'] = prioridade_select.value
            
            # Busca processos
            processos = listar_processos_internos(filtros)
            
            # Se não há processos, mostra estado vazio
            if not processos:
                with tabela_container:
                    with ui.card().classes('w-full p-8 text-center bg-gray-50'):
                        ui.icon('inbox', size='xl').classes('text-gray-400 mb-4')
                        ui.label('Nenhum processo interno cadastrado').classes('text-gray-500 text-sm')
                        ui.label('Use o botão "Cadastrar Processo Interno" para adicionar novos processos.').classes('text-gray-400 text-xs mt-2')
                return
            
            # Prepara dados para a tabela
            linhas = []
            processos_snapshot = []
            
            for processo in processos:
                processos_snapshot.append(processo)
                cor_prioridade = PRIORIDADE_CORES.get(
                    processo.get('prioridade', 'P4'),
                    PRIORIDADE_CORES['P4']
                )
                
                categoria_display = CATEGORIAS_DISPLAY.get(
                    processo.get('categoria', ''),
                    processo.get('categoria', '')
                )
                
                prioridade_display = PRIORIDADE_DISPLAY.get(
                    processo.get('prioridade', 'P4'),
                    processo.get('prioridade', 'P4')
                )
                
                linhas.append({
                    '_id': processo.get('_id'),
                    'titulo': processo.get('titulo', ''),
                    'categoria': categoria_display,
                    'prioridade': prioridade_display,
                    'prioridade_cor_bg': cor_prioridade['bg'],
                    'prioridade_cor_text': cor_prioridade['text'],
                    'prioridade_cor_border': cor_prioridade['border'],
                    'link': processo.get('link', ''),
                })
            
            # Cria tabela
            colunas = [
                {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'sortable': True},
                {'name': 'categoria', 'label': 'Categoria', 'field': 'categoria', 'align': 'left', 'sortable': True},
                {'name': 'prioridade', 'label': 'Prioridade', 'field': 'prioridade', 'align': 'center', 'sortable': True},
                {'name': 'link', 'label': 'Link', 'field': 'link', 'align': 'left'},
                {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center'},
            ]
            
            with tabela_container:
                tabela = ui.table(
                    columns=colunas,
                    rows=linhas,
                    row_key='_id'
                ).classes('w-full').props('flat bordered')
                
                # Template customizado para prioridade (com cor)
                tabela.add_slot('body-cell-prioridade', '''
                    <q-td :props="props">
                        <q-badge 
                            :style="'background-color: ' + props.row.prioridade_cor_bg + '; color: ' + props.row.prioridade_cor_text + '; border: 1px solid ' + props.row.prioridade_cor_border"
                            :label="props.value"
                        />
                    </q-td>
                ''')
                
                # Template customizado para link
                tabela.add_slot('body-cell-link', '''
                    <q-td :props="props">
                        <a v-if="props.value" :href="props.value" target="_blank" class="text-blue-600 hover:underline">Abrir</a>
                        <span v-else class="text-gray-400">—</span>
                    </q-td>
                ''')
                
                # Template customizado para ações
                tabela.add_slot('body-cell-acoes', '''
                    <q-td :props="props">
                        <q-btn 
                            flat dense round 
                            icon="edit" 
                            color="primary"
                            @click="$parent.$emit('edit', props.row)"
                            size="sm"
                        />
                        <q-btn 
                            flat dense round 
                            icon="delete" 
                            color="negative"
                            @click="$parent.$emit('delete', props.row)"
                            size="sm"
                        />
                    </q-td>
                ''')
                
                # Handlers para eventos de edição e exclusão
                def handle_edit(e):
                    processo_row = e.args
                    processo_id = processo_row.get('_id')
                    if processo_id:
                        _abrir_modal_processo_interno(processo_id, _atualizar_tabela_processos)
                
                def handle_delete(e):
                    processo_row = e.args
                    processo_id = processo_row.get('_id')
                    if processo_id:
                        _confirmar_exclusao_processo(processo_id, _atualizar_tabela_processos)
                
                tabela.on('edit', handle_edit)
                tabela.on('delete', handle_delete)
        
        # Cabeçalho da seção com botão de cadastro
        with ui.row().classes('w-full items-center justify-between mb-4'):
            # Título da seção
            ui.label('Processos Internos').classes('text-xl font-bold text-gray-800')
            
            # Botão de cadastro - destacado no canto superior direito
            ui.button(
                'Cadastrar Processo Interno',
                icon='add',
                on_click=lambda: _abrir_modal_processo_interno(None, _atualizar_tabela_processos)
            ).props('unelevated').style(f'background-color: {PRIMARY_COLOR}; color: white;') \
             .classes('font-medium')
        
        # Separador visual
        ui.separator()
        
        # Conecta eventos de filtros
        busca_input.on('update:model-value', lambda: _atualizar_tabela_processos.refresh())
        categoria_select.on('update:model-value', lambda: _atualizar_tabela_processos.refresh())
        prioridade_select.on('update:model-value', lambda: _atualizar_tabela_processos.refresh())
        
        # Renderiza tabela inicial
        _atualizar_tabela_processos()


def _limpar_filtros(busca_input, categoria_select, prioridade_select):
    """Limpa todos os filtros."""
    busca_input.value = ''
    categoria_select.value = None
    prioridade_select.value = None


def _abrir_modal_processo_interno(
    processo_id: Optional[str],
    callback_atualizar: Optional[Callable] = None
):
    """
    Abre modal para criar ou editar processo interno.
    
    Args:
        processo_id: ID do processo para edição (None para criar novo)
        callback_atualizar: Função para atualizar tabela após salvar
    """
    # Obtém dados do processo se estiver editando
    processo = None
    if processo_id:
        processo = obter_processo_interno(processo_id)
        if not processo:
            ui.notify('Processo interno não encontrado', type='negative')
            return
    
    # Obtém usuário atual
    usuario = get_current_user()
    usuario_uid = usuario.get('uid', '') if usuario else ''
    usuario_email = usuario.get('email', 'Usuário desconhecido') if usuario else 'Usuário desconhecido'
    
    # Cria modal
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl p-6'):
        ui.label(
            'Editar Processo Interno' if processo_id else 'Novo Processo Interno'
        ).classes('text-2xl font-bold text-gray-800 mb-6')
        
        # Campos do formulário
        with ui.column().classes('w-full gap-4'):
            # Título (obrigatório)
            titulo_input = ui.input(
                'Título do Processo Interno *',
                value=processo.get('titulo', '') if processo else ''
            ).classes('w-full').props('outlined dense')
            
            # Link (opcional)
            link_input = ui.input(
                'Link do Processo',
                placeholder='https://...',
                value=processo.get('link', '') if processo else ''
            ).classes('w-full').props('outlined dense')
            
            # Linha: Categoria e Prioridade
            with ui.row().classes('w-full gap-4'):
                categoria_select = ui.select(
                    {cat: CATEGORIAS_DISPLAY[cat] for cat in CATEGORIAS_PROCESSO_INTERNO},
                    label='Categoria *',
                    value=processo.get('categoria', '') if processo else None
                ).classes('flex-1').props('outlined dense')
                
                prioridade_select = ui.select(
                    {p: PRIORIDADE_DISPLAY[p] for p in PRIORIDADES},
                    label='Prioridade *',
                    value=processo.get('prioridade', '') if processo else None
                ).classes('flex-1').props('outlined dense')
        
        # Botões de ação
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button(
                'Cancelar',
                on_click=dialog.close
            ).props('outline')
            
            def salvar():
                """Salva o processo interno."""
                # Valida campos obrigatórios
                if not titulo_input.value or len(titulo_input.value.strip()) < 3:
                    ui.notify('Título deve ter pelo menos 3 caracteres', type='negative')
                    return
                
                if not categoria_select.value:
                    ui.notify('Categoria é obrigatória', type='negative')
                    return
                
                if not prioridade_select.value:
                    ui.notify('Prioridade é obrigatória', type='negative')
                    return
                
                # Prepara dados
                dados = {
                    'titulo': titulo_input.value.strip(),
                    'categoria': categoria_select.value,
                    'prioridade': prioridade_select.value,
                    'status': processo.get('status', 'ativo') if processo else 'ativo'
                }
                
                # Link (opcional)
                if link_input.value and link_input.value.strip():
                    link = link_input.value.strip()
                    if not (link.startswith('http://') or link.startswith('https://')):
                        ui.notify('Link deve começar com http:// ou https://', type='negative')
                        return
                    dados['link'] = link
                else:
                    dados['link'] = ''
                
                # Adiciona informações de criação/atualização
                if not processo_id:
                    dados['criado_por'] = usuario_uid
                    dados['criado_por_nome'] = usuario_email
                
                try:
                    # Salva no banco
                    if processo_id:
                        # Atualiza
                        sucesso = atualizar_processo_interno(processo_id, dados)
                        if sucesso:
                            ui.notify('Processo interno atualizado com sucesso!', type='positive')
                            dialog.close()
                            if callback_atualizar:
                                callback_atualizar.refresh()
                        else:
                            ui.notify('Erro ao atualizar processo interno', type='negative')
                    else:
                        # Cria novo
                        novo_id = criar_processo_interno(dados)
                        if novo_id:
                            ui.notify('Processo interno criado com sucesso!', type='positive')
                            dialog.close()
                            if callback_atualizar:
                                callback_atualizar.refresh()
                        else:
                            ui.notify('Erro ao criar processo interno', type='negative')
                except ValueError as e:
                    # Erro de validação
                    ui.notify(str(e), type='negative')
                except Exception as e:
                    ui.notify(f'Erro ao salvar: {str(e)}', type='negative')
            
            ui.button(
                'Salvar',
                icon='save',
                on_click=salvar
            ).props('unelevated').style(f'background-color: {PRIMARY_COLOR}; color: white;')
    
    dialog.open()


def _confirmar_exclusao_processo(
    processo_id: str,
    callback_atualizar: Optional[Callable] = None
):
    """
    Confirma e executa exclusão de processo interno.
    
    Args:
        processo_id: ID do processo a excluir
        callback_atualizar: Função para atualizar tabela após excluir
    """
    # Busca dados do processo para exibir no diálogo
    processo = obter_processo_interno(processo_id)
    titulo = processo.get('titulo', 'este processo') if processo else 'este processo'
    
    # Cria diálogo de confirmação
    with ui.dialog() as dialog_confirmacao, ui.card().classes('w-full max-w-md p-6'):
        ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800 mb-4')
        ui.label(f'Tem certeza que deseja excluir o processo interno "{titulo}"?').classes('text-gray-600 mb-6')
        ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-600 mb-6')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button(
                'Cancelar',
                on_click=dialog_confirmacao.close
            ).props('outline')
            
            def confirmar():
                """Confirma e executa exclusão."""
                try:
                    sucesso = excluir_processo_interno(processo_id)
                    if sucesso:
                        ui.notify('Processo interno excluído com sucesso!', type='positive')
                        dialog_confirmacao.close()
                        if callback_atualizar:
                            callback_atualizar.refresh()
                    else:
                        ui.notify('Erro ao excluir processo interno', type='negative')
                except Exception as e:
                    ui.notify(f'Erro ao excluir: {str(e)}', type='negative')
            
            ui.button(
                'Excluir',
                icon='delete',
                on_click=confirmar
            ).props('unelevated color=negative')
    
    dialog_confirmacao.open()

