"""
Página principal do módulo Pessoas do workspace Visão Geral.
Rota: /visao-geral/pessoas
"""
from typing import Optional, Callable
from nicegui import ui
from ....core import layout
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from .database import (
    listar_pessoas, excluir_pessoa,
    listar_envolvidos, criar_envolvido, atualizar_envolvido, excluir_envolvido, contar_envolvidos
)
from .pessoa_dialog import abrir_dialog_pessoa, confirmar_exclusao
from .models import (
    formatar_documento,
    formatar_telefone,
    TIPO_PESSOA_OPTIONS,
    TIPOS_ENVOLVIDO,
    TIPO_ENVOLVIDO_LABELS,
    criar_envolvido_vazio,
    extrair_digitos,
)


@ui.page('/visao-geral/pessoas')
def pessoas_visao_geral():
    """Página de Pessoas do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace
    definir_workspace('visao_geral_escritorio')

    _renderizar_pagina_pessoas()


def _renderizar_pagina_pessoas():
    """Renderiza o conteúdo da página de pessoas."""
    with layout('Pessoas', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Pessoas', None)]):
        # Estilos CSS customizados
        ui.add_head_html('''
        <style>
        .filtros-container {
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .tabela-pessoas {
            width: 100% !important;
        }
        .tabela-pessoas .q-table__container {
            width: 100% !important;
        }
        .tabela-pessoas .q-table {
            width: 100% !important;
            table-layout: fixed !important;
        }
        .tabela-pessoas .q-table__top {
            padding: 0;
        }
        .tabela-pessoas th {
            font-weight: 600 !important;
            color: #374151 !important;
            background-color: #f3f4f6 !important;
            padding: 12px 16px !important;
        }
        .tabela-pessoas td {
            padding: 12px 16px !important;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .tabela-pessoas tbody tr:hover {
            background-color: #f9fafb !important;
            transition: background-color 0.2s ease;
        }
        /* Larguras proporcionais das colunas - 3 colunas apenas */
        .tabela-pessoas .q-table thead th:nth-child(1),
        .tabela-pessoas .q-table tbody td:nth-child(1) {
            width: 70% !important;
            min-width: 300px;
        }
        .tabela-pessoas .q-table thead th:nth-child(2),
        .tabela-pessoas .q-table tbody td:nth-child(2) {
            width: 15% !important;
            min-width: 100px;
        }
        .tabela-pessoas .q-table thead th:nth-child(3),
        .tabela-pessoas .q-table tbody td:nth-child(3) {
            width: 15% !important;
            min-width: 120px;
        }
        .contador-resultados {
            font-size: 0.875rem;
            color: #6b7280;
        }
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 4rem 2rem;
            text-align: center;
        }
        /* Estilos para abas - seguindo padrão do módulo pessoas */
        .main-tabs .q-tab {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #1f2937 !important;
            margin-right: 2rem !important;
        }
        </style>
        ''')

        # Estado dos filtros (usando dicionário para ser reativo)
        filtros = {
            'busca': '',
            'tipo': 'Todos',
        }

        # Referência para o refreshable (será definida depois)
        refresh_ref = {'func': None}

        # Container principal com abas
        with ui.column().classes('w-full gap-0'):
            # Abas principais - alinhadas à esquerda
            with ui.tabs().classes('w-full justify-start main-tabs').props('no-caps align=left') as main_tabs:
                clientes_tab = ui.tab('Clientes')
                outros_envolvidos_tab = ui.tab('Outros Envolvidos')
                parceiros_tab = ui.tab('Parceiros')

            # Painel de conteúdo das abas
            with ui.tab_panels(main_tabs, value=clientes_tab).classes('w-full bg-white p-4 rounded shadow-sm'):
                # ========== ABA: CLIENTES ==========
                with ui.tab_panel(clientes_tab):
                    # Container principal com card
                    with ui.card().classes('w-full'):
                        # Header
                        with ui.row().classes('w-full justify-between items-center p-4'):
                            with ui.column().classes('gap-0'):
                                ui.label('Pessoas').classes('text-xl font-bold text-gray-800')
                                ui.label('Gerenciamento de pessoas do escritório').classes('text-sm text-gray-500')

                            # Botão Nova Pessoa
                            def nova_pessoa():
                                if refresh_ref['func']:
                                    abrir_dialog_pessoa(on_save=lambda: refresh_ref['func'].refresh())
                                else:
                                    abrir_dialog_pessoa()

                            ui.button('Nova Pessoa', icon='add', on_click=nova_pessoa).props('color=primary')

                        ui.separator()

                        # Container dos filtros
                        with ui.element('div').classes('filtros-container mx-4 mt-4'):
                            with ui.row().classes('w-full items-end gap-4'):
                                # Campo de busca
                                busca_input = ui.input(
                                    label='Buscar',
                                    placeholder='Nome, email ou documento...'
                                ).classes('flex-1').props('dense outlined clearable')

                                # Filtro por tipo
                                tipo_select = ui.select(
                                    options=['Todos'] + TIPO_PESSOA_OPTIONS,
                                    value='Todos',
                                    label='Tipo'
                                ).classes('w-32').props('dense outlined')

                                # Botão limpar filtros
                                def limpar_filtros():
                                    busca_input.value = ''
                                    tipo_select.value = 'Todos'
                                    filtros['busca'] = ''
                                    filtros['tipo'] = 'Todos'
                                    if refresh_ref['func']:
                                        refresh_ref['func'].refresh()

                                ui.button('Limpar', icon='clear', on_click=limpar_filtros).props('flat dense')

                                # Eventos de filtro
                                def aplicar_filtros():
                                    filtros['busca'] = busca_input.value or ''
                                    filtros['tipo'] = tipo_select.value
                                    if refresh_ref['func']:
                                        refresh_ref['func'].refresh()

                                busca_input.on('update:model-value', lambda: aplicar_filtros())
                                tipo_select.on('update:model-value', lambda: aplicar_filtros())

                        # Conteúdo principal (tabela)
                        @ui.refreshable
                        def renderizar_conteudo():
                            _renderizar_tabela(filtros, renderizar_conteudo)

                        # Guarda referência para uso posterior
                        refresh_ref['func'] = renderizar_conteudo

                        with ui.element('div').classes('w-full p-4').style('width: 100%; overflow-x: auto'):
                            renderizar_conteudo()

                # ========== ABA: OUTROS ENVOLVIDOS ==========
                with ui.tab_panel(outros_envolvidos_tab):
                    # Estado dos filtros para envolvidos
                    filtros_envolvidos = {
                        'busca': '',
                        'tipo': 'Todos',
                    }

                    # Referência para o refreshable (será definida depois)
                    refresh_ref_envolvidos = {'func': None}

                    # Container principal com card
                    with ui.card().classes('w-full'):
                        # Header
                        with ui.row().classes('w-full justify-between items-center p-4'):
                            with ui.column().classes('gap-0'):
                                ui.label('Outros Envolvidos').classes('text-xl font-bold text-gray-800')
                                ui.label('Gerenciamento de outros envolvidos nos processos').classes('text-sm text-gray-500')

                            # Botão Novo Envolvido
                            def novo_envolvido():
                                if refresh_ref_envolvidos['func']:
                                    abrir_dialog_envolvido(on_save=lambda: refresh_ref_envolvidos['func'].refresh())
                                else:
                                    abrir_dialog_envolvido()

                            ui.button('Novo Envolvido', icon='add', on_click=novo_envolvido).props('color=primary')

                        ui.separator()

                        # Container dos filtros
                        with ui.element('div').classes('filtros-container mx-4 mt-4'):
                            with ui.row().classes('w-full items-end gap-4'):
                                # Campo de busca
                                busca_input_envolvidos = ui.input(
                                    label='Buscar',
                                    placeholder='Nome...'
                                ).classes('flex-1').props('dense outlined clearable')

                                # Filtro por tipo
                                tipo_select_envolvidos = ui.select(
                                    options=['Todos'] + TIPOS_ENVOLVIDO,
                                    value='Todos',
                                    label='Tipo'
                                ).classes('w-40').props('dense outlined')

                                # Botão limpar filtros
                                def limpar_filtros_envolvidos():
                                    busca_input_envolvidos.value = ''
                                    tipo_select_envolvidos.value = 'Todos'
                                    filtros_envolvidos['busca'] = ''
                                    filtros_envolvidos['tipo'] = 'Todos'
                                    if refresh_ref_envolvidos['func']:
                                        refresh_ref_envolvidos['func'].refresh()

                                ui.button('Limpar', icon='clear', on_click=limpar_filtros_envolvidos).props('flat dense')

                                # Eventos de filtro
                                def aplicar_filtros_envolvidos():
                                    filtros_envolvidos['busca'] = busca_input_envolvidos.value or ''
                                    filtros_envolvidos['tipo'] = tipo_select_envolvidos.value
                                    if refresh_ref_envolvidos['func']:
                                        refresh_ref_envolvidos['func'].refresh()

                                busca_input_envolvidos.on('update:model-value', lambda: aplicar_filtros_envolvidos())
                                tipo_select_envolvidos.on('update:model-value', lambda: aplicar_filtros_envolvidos())

                        # Conteúdo principal (tabela)
                        @ui.refreshable
                        def renderizar_conteudo_envolvidos():
                            _renderizar_tabela_envolvidos(filtros_envolvidos, renderizar_conteudo_envolvidos)

                        # Guarda referência para uso posterior
                        refresh_ref_envolvidos['func'] = renderizar_conteudo_envolvidos

                        with ui.element('div').classes('w-full p-4').style('width: 100%; overflow-x: auto'):
                            renderizar_conteudo_envolvidos()

                # ========== ABA: PARCEIROS ==========
                with ui.tab_panel(parceiros_tab):
                    with ui.column().classes('w-full items-center justify-center py-16'):
                        ui.icon('construction', size='64px').classes('text-gray-400')
                        ui.label('Em desenvolvimento').classes('text-xl font-bold text-gray-500 mt-4')
                        ui.label('Esta funcionalidade estará disponível em breve.').classes('text-gray-400')


def _renderizar_tabela(filtros: dict, refresh_callback):
    """Renderiza a tabela de pessoas com filtros aplicados."""
    # Carrega pessoas
    try:
        todas_pessoas = listar_pessoas()
    except Exception as e:
        print(f"Erro ao carregar pessoas: {e}")
        with ui.column().classes('w-full items-center py-8'):
            ui.icon('error', size='48px', color='negative')
            ui.label('Erro ao carregar pessoas').classes('text-lg text-gray-600 mt-2')
            ui.label('Tente recarregar a página.').classes('text-sm text-gray-400')
        return

    # Aplica filtros
    pessoas_filtradas = _aplicar_filtros(todas_pessoas, filtros)

    # Contador de resultados
    total = len(pessoas_filtradas)
    total_geral = len(todas_pessoas)

    if filtros['busca'] or filtros['tipo'] != 'Todos':
        ui.label(f'{total} de {total_geral} pessoas encontradas').classes('contador-resultados mb-3')
    else:
        ui.label(f'{total} pessoa(s) cadastrada(s)').classes('contador-resultados mb-3')

    # Estado vazio
    if not pessoas_filtradas:
        with ui.column().classes('w-full items-center py-12'):
            if todas_pessoas:
                # Tem pessoas, mas filtro não encontrou
                ui.icon('search_off', size='64px').classes('text-gray-300')
                ui.label('Nenhuma pessoa encontrada').classes('text-lg text-gray-500 mt-4')
                ui.label('Tente ajustar os filtros de busca.').classes('text-sm text-gray-400')
            else:
                # Não tem nenhuma pessoa cadastrada
                ui.icon('people_outline', size='64px').classes('text-gray-300')
                ui.label('Nenhuma pessoa cadastrada').classes('text-lg text-gray-500 mt-4')
                ui.label('Clique em "Nova Pessoa" para começar.').classes('text-sm text-gray-400')
        return

    # Prepara dados para a tabela (sem campos de timestamp para evitar erro de serialização)
    dados_tabela = []
    for pessoa in pessoas_filtradas:
        # Cria cópia dos dados sem timestamps para serialização segura
        dados_seguros = {
            k: v for k, v in pessoa.items()
            if k not in ['created_at', 'updated_at', 'data_criacao', 'data_atualizacao']
        }
        dados_tabela.append({
            '_id': pessoa.get('_id', ''),
            'nome_exibicao': pessoa.get('nome_exibicao') or pessoa.get('full_name', 'Sem nome'),
            'tipo_pessoa': pessoa.get('tipo_pessoa', 'PF'),
            'cpf_cnpj_formatado': formatar_documento(pessoa),
            'email': pessoa.get('email', '') or '-',
            'telefone': formatar_telefone(pessoa.get('telefone', '')) or '-',
            '_dados_completos': dados_seguros,
        })

    # Colunas da tabela - apenas Nome, Tipo e Ações
    colunas = [
        {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left', 'sortable': True, 'style': 'width: 70%'},
        {'name': 'tipo_pessoa', 'label': 'Tipo', 'field': 'tipo_pessoa', 'align': 'center', 'style': 'width: 15%'},
        {'name': 'actions', 'label': 'Ações', 'field': 'actions', 'align': 'center', 'style': 'width: 15%'},
    ]

    # Cria tabela com largura total
    tabela = ui.table(
        columns=colunas,
        rows=dados_tabela,
        row_key='_id',
        pagination={'rowsPerPage': 15},
    ).classes('w-full tabela-pessoas').style('width: 100%')

    # Slot para coluna de tipo (badge colorido)
    tabela.add_slot('body-cell-tipo_pessoa', '''
        <q-td :props="props">
            <q-badge
                :color="props.row.tipo_pessoa === 'PJ' ? 'amber-3' : 'blue-2'"
                :text-color="props.row.tipo_pessoa === 'PJ' ? 'amber-10' : 'blue-10'"
                class="text-weight-medium q-px-sm"
            >
                {{ props.row.tipo_pessoa }}
            </q-badge>
        </q-td>
    ''')

    # Slot para coluna de ações
    tabela.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <div class="q-gutter-xs">
                <q-btn flat dense icon="edit" color="primary" @click="$parent.$emit('editar', props.row)">
                    <q-tooltip>Editar</q-tooltip>
                </q-btn>
                <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('excluir', props.row)">
                    <q-tooltip>Excluir</q-tooltip>
                </q-btn>
            </div>
        </q-td>
    ''')

    # Handlers de eventos
    def ao_editar(evento):
        linha = evento.args
        pessoa_completa = linha.get('_dados_completos', {})
        abrir_dialog_pessoa(pessoa=pessoa_completa, on_save=lambda: refresh_callback.refresh())

    def ao_excluir(evento):
        linha = evento.args
        pessoa_completa = linha.get('_dados_completos', {})

        def executar_exclusao():
            pessoa_id = pessoa_completa.get('_id')
            nome = pessoa_completa.get('nome_exibicao', 'Pessoa')
            if excluir_pessoa(pessoa_id):
                ui.notify(f'"{nome}" excluída com sucesso!', type='positive')
                refresh_callback.refresh()
            else:
                ui.notify('Erro ao excluir. Tente novamente.', type='negative')

        confirmar_exclusao(pessoa_completa, on_confirm=executar_exclusao)

    tabela.on('editar', ao_editar)
    tabela.on('excluir', ao_excluir)


def _renderizar_tabela_envolvidos(filtros: dict, refresh_callback):
    """Renderiza a tabela de envolvidos com filtros aplicados."""
    # Carrega envolvidos
    try:
        todos_envolvidos = listar_envolvidos()
    except Exception as e:
        print(f"Erro ao carregar envolvidos: {e}")
        with ui.column().classes('w-full items-center py-8'):
            ui.icon('error', size='48px', color='negative')
            ui.label('Erro ao carregar envolvidos').classes('text-lg text-gray-600 mt-2')
            ui.label('Tente recarregar a página.').classes('text-sm text-gray-400')
        return

    # Aplica filtros
    envolvidos_filtrados = _aplicar_filtros_envolvidos(todos_envolvidos, filtros)

    # Contador de resultados
    total = len(envolvidos_filtrados)
    total_geral = len(todos_envolvidos)

    if filtros['busca'] or filtros['tipo'] != 'Todos':
        ui.label(f'{total} de {total_geral} envolvidos encontrados').classes('contador-resultados mb-3')
    else:
        ui.label(f'{total} envolvido(s) cadastrado(s)').classes('contador-resultados mb-3')

    # Estado vazio
    if not envolvidos_filtrados:
        with ui.column().classes('w-full items-center py-12'):
            if todos_envolvidos:
                # Tem envolvidos, mas filtro não encontrou
                ui.icon('search_off', size='64px').classes('text-gray-300')
                ui.label('Nenhum envolvido encontrado').classes('text-lg text-gray-500 mt-4')
                ui.label('Tente ajustar os filtros de busca.').classes('text-sm text-gray-400')
            else:
                # Não tem nenhum envolvido cadastrado
                ui.icon('people_outline', size='64px').classes('text-gray-300')
                ui.label('Nenhum envolvido cadastrado').classes('text-lg text-gray-500 mt-4')
                ui.label('Clique em "Novo Envolvido" para começar.').classes('text-sm text-gray-400')
        return

    # Prepara dados para a tabela (sem campos de timestamp para evitar erro de serialização)
    dados_tabela = []
    for envolvido in envolvidos_filtrados:
        # Cria cópia dos dados sem timestamps para serialização segura
        dados_seguros = {
            k: v for k, v in envolvido.items()
            if k not in ['created_at', 'updated_at', 'data_criacao', 'data_atualizacao']
        }
        dados_tabela.append({
            '_id': envolvido.get('_id', ''),
            'nome_exibicao': envolvido.get('nome_exibicao') or envolvido.get('nome_completo', 'Sem nome'),
            'tipo_envolvido': envolvido.get('tipo_envolvido', 'PF'),
            '_dados_completos': dados_seguros,
        })

    # Colunas da tabela - apenas Nome, Tipo e Ações
    colunas = [
        {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left', 'sortable': True, 'style': 'width: 70%'},
        {'name': 'tipo_envolvido', 'label': 'Tipo', 'field': 'tipo_envolvido', 'align': 'center', 'style': 'width: 15%'},
        {'name': 'actions', 'label': 'Ações', 'field': 'actions', 'align': 'center', 'style': 'width: 15%'},
    ]

    # Cria tabela com largura total
    tabela = ui.table(
        columns=colunas,
        rows=dados_tabela,
        row_key='_id',
        pagination={'rowsPerPage': 15},
    ).classes('w-full tabela-pessoas').style('width: 100%')

    # Slot para coluna de tipo (badge colorido)
    tabela.add_slot('body-cell-tipo_envolvido', '''
        <q-td :props="props">
            <q-badge
                :color="props.row.tipo_envolvido === 'PJ' ? 'green-3' : (props.row.tipo_envolvido === 'Ente Público' ? 'purple-3' : 'blue-2')"
                :text-color="props.row.tipo_envolvido === 'PJ' ? 'green-10' : (props.row.tipo_envolvido === 'Ente Público' ? 'purple-10' : 'blue-10')"
                class="text-weight-medium q-px-sm"
            >
                {{ props.row.tipo_envolvido }}
            </q-badge>
        </q-td>
    ''')

    # Slot para coluna de ações
    tabela.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <div class="q-gutter-xs">
                <q-btn flat dense icon="edit" color="primary" @click="$parent.$emit('editar', props.row)">
                    <q-tooltip>Editar</q-tooltip>
                </q-btn>
                <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('excluir', props.row)">
                    <q-tooltip>Excluir</q-tooltip>
                </q-btn>
            </div>
        </q-td>
    ''')

    # Handlers de eventos
    def ao_editar_envolvido(evento):
        linha = evento.args
        envolvido_completo = linha.get('_dados_completos', {})
        abrir_dialog_envolvido(envolvido=envolvido_completo, on_save=lambda: refresh_callback.refresh())

    def ao_excluir_envolvido(evento):
        linha = evento.args
        envolvido_completo = linha.get('_dados_completos', {})

        def executar_exclusao():
            envolvido_id = envolvido_completo.get('_id')
            nome = envolvido_completo.get('nome_exibicao', 'Envolvido')
            if excluir_envolvido(envolvido_id):
                ui.notify(f'"{nome}" excluído com sucesso!', type='positive')
                refresh_callback.refresh()
            else:
                ui.notify('Erro ao excluir. Tente novamente.', type='negative')

        confirmar_exclusao_envolvido(envolvido_completo, on_confirm=executar_exclusao)

    tabela.on('editar', ao_editar_envolvido)
    tabela.on('excluir', ao_excluir_envolvido)


def abrir_dialog_envolvido(
    envolvido: Optional[dict] = None,
    on_save: Optional[Callable] = None
):
    """
    Abre dialog para criar ou editar um envolvido.

    Args:
        envolvido: Dados do envolvido para edição (None para criar novo)
        on_save: Callback chamado após salvar com sucesso
    """
    is_edicao = envolvido is not None
    titulo = 'Editar Envolvido' if is_edicao else 'Novo Envolvido'

    # Dados iniciais
    dados = envolvido.copy() if envolvido else criar_envolvido_vazio()

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label(titulo).classes('text-xl font-bold text-gray-800')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round')

        ui.separator().classes('mb-4')

        # Container do formulário
        with ui.column().classes('w-full gap-4'):
            # Tipo de envolvido
            tipo_select = ui.select(
                options=TIPOS_ENVOLVIDO,
                value=dados.get('tipo_envolvido', 'PF'),
                label='Tipo de Envolvido'
            ).classes('w-full').props('dense outlined')

            # Nome completo
            nome_completo_input = ui.input(
                label='Nome Completo',
                value=dados.get('nome_completo', ''),
                placeholder='Digite o nome completo'
            ).classes('w-full').props('dense outlined')

            # Nome de exibição
            nome_exibicao_input = ui.input(
                label='Nome de Exibição',
                value=dados.get('nome_exibicao', ''),
                placeholder='Nome para exibição no sistema'
            ).classes('w-full').props('dense outlined')

            # CPF/CNPJ
            cpf_cnpj_input = ui.input(
                label='CPF/CNPJ',
                value=dados.get('cpf_cnpj', ''),
                placeholder='000.000.000-00 ou 00.000.000/0000-00'
            ).classes('w-full').props('dense outlined')

            # Email e Telefone (na mesma linha)
            with ui.row().classes('w-full gap-4'):
                email_input = ui.input(
                    label='Email',
                    value=dados.get('email', ''),
                    placeholder='email@exemplo.com'
                ).classes('flex-1').props('dense outlined type=email')

                telefone_input = ui.input(
                    label='Telefone',
                    value=dados.get('telefone', ''),
                    placeholder='(00) 00000-0000'
                ).classes('flex-1').props('dense outlined')

            # Observações
            observacoes_input = ui.textarea(
                label='Observações',
                value=dados.get('observacoes', ''),
                placeholder='Observações adicionais...'
            ).classes('w-full').props('dense outlined rows=3')

        ui.separator().classes('my-4')

        # Botões de ação
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def salvar():
                """Valida e salva os dados do envolvido."""
                # Coleta dados do formulário
                novos_dados = {
                    'tipo_envolvido': tipo_select.value or 'PF',
                    'nome_completo': nome_completo_input.value.strip(),
                    'nome_exibicao': nome_exibicao_input.value.strip(),
                    'cpf_cnpj': extrair_digitos(cpf_cnpj_input.value.strip()),
                    'email': email_input.value.strip(),
                    'telefone': telefone_input.value.strip(),
                    'observacoes': observacoes_input.value.strip(),
                }

                # Salva no Firebase
                try:
                    if is_edicao:
                        envolvido_id = dados.get('_id')
                        sucesso = atualizar_envolvido(envolvido_id, novos_dados)
                        if sucesso:
                            ui.notify('Envolvido atualizado com sucesso!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao atualizar. Tente novamente.', type='negative')
                    else:
                        envolvido_id = criar_envolvido(novos_dados)
                        if envolvido_id:
                            ui.notify('Envolvido cadastrado com sucesso!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao salvar. Tente novamente.', type='negative')
                except Exception as e:
                    print(f"Erro ao salvar envolvido: {e}")
                    ui.notify('Erro ao salvar. Verifique os dados.', type='negative')

            ui.button('Salvar', on_click=salvar, icon='save').props('color=primary')

    dialog.open()


def confirmar_exclusao_envolvido(envolvido: dict, on_confirm: Optional[Callable] = None):
    """
    Exibe dialog de confirmação para exclusão de envolvido.

    Args:
        envolvido: Dados do envolvido a excluir
        on_confirm: Callback chamado após confirmar exclusão
    """
    nome = envolvido.get('nome_exibicao') or envolvido.get('nome_completo', 'este envolvido')

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        with ui.column().classes('w-full gap-4'):
            # Header com ícone de alerta
            with ui.row().classes('w-full items-center gap-3'):
                ui.icon('warning', color='negative', size='md')
                ui.label('Confirmar exclusão').classes('text-lg font-bold text-gray-800')

            # Mensagem
            ui.label(f'Deseja realmente excluir "{nome}"?').classes('text-gray-600')
            ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-gray-400')

            # Botões
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

                def confirmar():
                    dialog.close()
                    if on_confirm:
                        on_confirm()

                ui.button('Excluir', on_click=confirmar, icon='delete').props('color=negative')

    dialog.open()


def _aplicar_filtros_envolvidos(envolvidos: list, filtros: dict) -> list:
    """
    Aplica filtros à lista de envolvidos.

    Args:
        envolvidos: Lista completa de envolvidos
        filtros: Dicionário com filtros ativos

    Returns:
        Lista filtrada de envolvidos
    """
    resultado = envolvidos

    # Filtro por tipo
    tipo_filtro = filtros.get('tipo', 'Todos')
    if tipo_filtro and tipo_filtro != 'Todos':
        resultado = [e for e in resultado if e.get('tipo_envolvido') == tipo_filtro]

    # Filtro por busca textual
    busca = filtros.get('busca', '').strip().lower()
    if busca:
        def match_busca(envolvido):
            nome = (envolvido.get('nome_exibicao') or envolvido.get('nome_completo') or '').lower()
            return busca in nome

        resultado = [e for e in resultado if match_busca(e)]

    return resultado


def _aplicar_filtros(pessoas: list, filtros: dict) -> list:
    """
    Aplica filtros à lista de pessoas.

    Args:
        pessoas: Lista completa de pessoas
        filtros: Dicionário com filtros ativos

    Returns:
        Lista filtrada de pessoas
    """
    resultado = pessoas

    # Filtro por tipo
    tipo_filtro = filtros.get('tipo', 'Todos')
    if tipo_filtro and tipo_filtro != 'Todos':
        resultado = [p for p in resultado if p.get('tipo_pessoa') == tipo_filtro]

    # Filtro por busca textual
    busca = filtros.get('busca', '').strip().lower()
    if busca:
        def match_busca(pessoa):
            nome = (pessoa.get('nome_exibicao') or pessoa.get('full_name') or '').lower()
            email = (pessoa.get('email') or '').lower()
            cpf = pessoa.get('cpf', '')
            cnpj = pessoa.get('cnpj', '')
            telefone = pessoa.get('telefone', '')

            return (
                busca in nome or
                busca in email or
                busca in cpf or
                busca in cnpj or
                busca in telefone
            )

        resultado = [p for p in resultado if match_busca(p)]

    return resultado
