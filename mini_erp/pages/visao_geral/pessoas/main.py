"""
Página principal do módulo Pessoas do workspace Visão Geral.
Rota: /visao-geral/pessoas
"""
from nicegui import ui
from ....core import layout
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from .database import listar_pessoas, excluir_pessoa
from .pessoa_dialog import abrir_dialog_pessoa, confirmar_exclusao
from .models import (
    formatar_documento,
    formatar_telefone,
    TIPO_PESSOA_OPTIONS,
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
            width: 100%;
        }
        .tabela-pessoas .q-table__top {
            padding: 0;
        }
        .tabela-pessoas th {
            font-weight: 600 !important;
            color: #374151 !important;
            background-color: #f3f4f6 !important;
        }
        .tabela-pessoas td {
            padding: 12px 16px !important;
        }
        .tabela-pessoas tbody tr:hover {
            background-color: #f9fafb !important;
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
        </style>
        ''')

        # Estado dos filtros (usando dicionário para ser reativo)
        filtros = {
            'busca': '',
            'tipo': 'Todos',
        }

        # Referência para o refreshable (será definida depois)
        refresh_ref = {'func': None}

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

            with ui.element('div').classes('p-4'):
                renderizar_conteudo()


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

    # Colunas da tabela
    colunas = [
        {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left', 'sortable': True},
        {'name': 'tipo_pessoa', 'label': 'Tipo', 'field': 'tipo_pessoa', 'align': 'center'},
        {'name': 'cpf_cnpj_formatado', 'label': 'CPF/CNPJ', 'field': 'cpf_cnpj_formatado', 'align': 'left'},
        {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
        {'name': 'telefone', 'label': 'Telefone', 'field': 'telefone', 'align': 'left'},
        {'name': 'actions', 'label': 'Ações', 'field': 'actions', 'align': 'center'},
    ]

    # Cria tabela
    tabela = ui.table(
        columns=colunas,
        rows=dados_tabela,
        row_key='_id',
        pagination={'rowsPerPage': 15},
    ).classes('w-full tabela-pessoas')

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
