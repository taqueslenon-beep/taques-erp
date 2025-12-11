"""
Página principal do módulo Casos do workspace Visão Geral.
Rota: /visao-geral/casos
Visualização em Cards responsivos.

Campos simplificados:
- titulo, nucleo, status, categoria, estado, clientes, descricao
- REMOVIDOS: ano, mes, parte_contraria
"""
from nicegui import ui
from ....core import layout, PRIMARY_COLOR
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from .database import listar_casos, excluir_caso, buscar_caso, atualizar_caso
from .caso_dialog import abrir_dialog_caso, confirmar_exclusao
from .models import (
    NUCLEO_OPTIONS,
    STATUS_OPTIONS,
    CATEGORIA_OPTIONS,
    ESTADOS,
    obter_cor_nucleo,
)
from ..pessoas.database import listar_pessoas


# =============================================================================
# CSS CUSTOMIZADO PARA CARDS
# =============================================================================

CASO_CARD_CSS = '''
<style>
.caso-card {
    transition: all 0.2s ease-in-out;
    border-radius: 12px;
    overflow: hidden;
}
.caso-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
.caso-titulo {
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.caso-clientes {
    line-height: 1.4;
}
.caso-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    width: fit-content;
}
.filtros-container {
    background-color: #f9fafb;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
</style>
'''


@ui.page('/visao-geral/casos')
def casos_visao_geral():
    """Página de Casos do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace
    definir_workspace('visao_geral_escritorio')

    _renderizar_pagina_casos()


def _renderizar_pagina_casos():
    """Renderiza o conteúdo da página de casos."""
    with layout('Casos', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Casos', None)]):
        # Adiciona CSS customizado
        ui.add_head_html(CASO_CARD_CSS)

        # Estado dos filtros (simplificado)
        filtros = {
            'busca': '',
            'nucleo': 'Todos',
            'status': 'Todos',
            'categoria': 'Todos',
            'estado': 'Todos',
        }

        # Referência para o refreshable
        refresh_ref = {'func': None}

        # Container principal com card
        with ui.card().classes('w-full'):
            # Header
            with ui.row().classes('w-full justify-between items-center p-4'):
                with ui.column().classes('gap-0'):
                    ui.label('Casos').classes('text-xl font-bold text-gray-800')
                    ui.label('Gerenciamento de casos do escritório').classes('text-sm text-gray-500')

                # Botão Novo Caso
                def novo_caso():
                    abrir_dialog_caso(on_save=lambda: refresh_ref['func'].refresh())

                ui.button('Novo Caso', icon='add', on_click=novo_caso).props('color=primary')

            ui.separator()

            # Container dos filtros
            with ui.element('div').classes('filtros-container mx-4 mt-4'):
                with ui.row().classes('w-full items-end gap-4 flex-wrap'):
                    # Campo de busca
                    busca_input = ui.input(
                        label='Buscar',
                        placeholder='Título ou cliente...'
                    ).classes('flex-1 min-w-48').props('dense outlined clearable')

                    # Filtro por núcleo
                    nucleo_select = ui.select(
                        options=['Todos'] + NUCLEO_OPTIONS,
                        value='Todos',
                        label='Núcleo'
                    ).classes('w-36').props('dense outlined')

                    # Filtro por status
                    status_select = ui.select(
                        options=['Todos'] + STATUS_OPTIONS,
                        value='Todos',
                        label='Status'
                    ).classes('w-36').props('dense outlined')

                    # Filtro por categoria
                    categoria_select = ui.select(
                        options=['Todos'] + CATEGORIA_OPTIONS,
                        value='Todos',
                        label='Categoria'
                    ).classes('w-36').props('dense outlined')

                    # Filtro por estado
                    estado_select = ui.select(
                        options=['Todos'] + ESTADOS,
                        value='Todos',
                        label='Estado'
                    ).classes('w-40').props('dense outlined')

                    # Botão limpar filtros
                    def limpar_filtros():
                        busca_input.value = ''
                        nucleo_select.value = 'Todos'
                        status_select.value = 'Todos'
                        categoria_select.value = 'Todos'
                        estado_select.value = 'Todos'
                        filtros['busca'] = ''
                        filtros['nucleo'] = 'Todos'
                        filtros['status'] = 'Todos'
                        filtros['categoria'] = 'Todos'
                        filtros['estado'] = 'Todos'
                        if refresh_ref['func']:
                            refresh_ref['func'].refresh()

                    ui.button('Limpar', icon='clear', on_click=limpar_filtros).props('flat dense')

                    # Eventos de filtro
                    def aplicar_filtros():
                        filtros['busca'] = busca_input.value or ''
                        filtros['nucleo'] = nucleo_select.value
                        filtros['status'] = status_select.value
                        filtros['categoria'] = categoria_select.value
                        filtros['estado'] = estado_select.value
                        if refresh_ref['func']:
                            refresh_ref['func'].refresh()

                    busca_input.on('update:model-value', lambda: aplicar_filtros())
                    nucleo_select.on('update:model-value', lambda: aplicar_filtros())
                    status_select.on('update:model-value', lambda: aplicar_filtros())
                    categoria_select.on('update:model-value', lambda: aplicar_filtros())
                    estado_select.on('update:model-value', lambda: aplicar_filtros())

            # Conteúdo principal (grid de cards)
            @ui.refreshable
            def renderizar_conteudo():
                _renderizar_grid_cards(filtros, refresh_ref)

            # Guarda referência para uso posterior
            refresh_ref['func'] = renderizar_conteudo

            with ui.element('div').classes('p-4'):
                renderizar_conteudo()


def _renderizar_grid_cards(filtros: dict, refresh_ref: dict):
    """Renderiza o grid de cards de casos."""
    # Carrega casos
    try:
        todos_casos = listar_casos()
    except Exception as e:
        print(f"Erro ao carregar casos: {e}")
        with ui.column().classes('w-full items-center py-8'):
            ui.icon('error', size='48px', color='negative')
            ui.label('Erro ao carregar casos').classes('text-lg text-gray-600 mt-2')
            ui.label('Tente recarregar a página.').classes('text-sm text-gray-400')
        return

    # Aplica filtros
    casos_filtrados = _aplicar_filtros(todos_casos, filtros)

    # Contador de resultados
    total = len(casos_filtrados)
    total_geral = len(todos_casos)

    tem_filtros = (
        filtros['busca'] or
        filtros['nucleo'] != 'Todos' or
        filtros['status'] != 'Todos' or
        filtros['categoria'] != 'Todos' or
        filtros['estado'] != 'Todos'
    )

    if tem_filtros:
        ui.label(f'{total} de {total_geral} casos encontrados').classes('text-sm text-gray-500 mb-4')
    else:
        ui.label(f'{total} caso(s) cadastrado(s)').classes('text-sm text-gray-500 mb-4')

    # Estado vazio
    if not casos_filtrados:
        with ui.column().classes('w-full items-center py-12'):
            if todos_casos:
                ui.icon('search_off', size='64px').classes('text-gray-300')
                ui.label('Nenhum caso encontrado').classes('text-lg text-gray-500 mt-4')
                ui.label('Tente ajustar os filtros de busca.').classes('text-sm text-gray-400')
            else:
                ui.icon('folder_open', size='64px').classes('text-gray-300')
                ui.label('Nenhum caso cadastrado').classes('text-lg text-gray-500 mt-4')
                ui.label('Clique em "Novo Caso" para começar.').classes('text-sm text-gray-400')
        return

    # Grid de cards responsivo
    with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'):
        for caso in casos_filtrados:
            _renderizar_card_caso(caso, refresh_ref)


def _renderizar_card_caso(caso: dict, refresh_ref: dict):
    """Renderiza um card individual de caso (simplificado - visual Schmidmeier)."""
    caso_id = caso.get('_id', '')
    titulo = caso.get('titulo', 'Sem título')
    nucleo = caso.get('nucleo', 'Generalista')
    clientes_nomes = caso.get('clientes_nomes', [])

    # Cor do núcleo
    cor_nucleo = obter_cor_nucleo(nucleo)

    # Card com estilo Schmidmeier (borda verde PRIMARY_COLOR)
    with ui.card().classes(
        'w-full p-4 shadow-md hover:shadow-xl transition-all duration-200 border caso-card cursor-pointer'
    ).style(f'border-color: {PRIMARY_COLOR}; border-width: 1px;'):

        # Linha 1: Título + Menu
        with ui.row().classes('w-full justify-between items-start'):
            ui.label(titulo).classes(
                'text-base font-bold text-gray-800 flex-1 caso-titulo'
            ).on('click', lambda: ui.navigate.to(f'/visao-geral/casos/{caso_id}'))

            # Menu de ações
            with ui.button(icon='more_vert').props('flat round dense size=sm'):
                with ui.menu():
                    # Editar
                    def ao_editar(c=caso):
                        abrir_dialog_caso(
                            caso=c,
                            on_save=lambda: refresh_ref['func'].refresh()
                        )

                    ui.menu_item('Editar', on_click=ao_editar)

                    # Excluir
                    def ao_excluir(c=caso):
                        def executar():
                            if excluir_caso(c.get('_id')):
                                ui.notify('Caso excluído com sucesso!', type='positive')
                                refresh_ref['func'].refresh()
                            else:
                                ui.notify('Erro ao excluir. Tente novamente.', type='negative')

                        confirmar_exclusao(c, on_confirm=executar)

                    ui.menu_item('Excluir', on_click=ao_excluir)

        # Área clicável para navegação
        with ui.column().classes('w-full gap-2 mt-2 cursor-pointer').on(
            'click', lambda: ui.navigate.to(f'/visao-geral/casos/{caso_id}')
        ):
            # Linha 2: Badge do Núcleo
            ui.label(nucleo).classes('caso-badge').style(
                f'background-color: {cor_nucleo}; color: white;'
            )

            # Linha 3: Clientes (todos)
            if clientes_nomes:
                clientes_texto = ', '.join(clientes_nomes)
                ui.label(clientes_texto).classes('text-sm text-gray-600 mt-2 caso-clientes')
            else:
                ui.label('Sem clientes vinculados').classes('text-sm text-gray-400 italic mt-2')


def _aplicar_filtros(casos: list, filtros: dict) -> list:
    """
    Aplica filtros à lista de casos.

    Args:
        casos: Lista completa de casos
        filtros: Dicionário com filtros ativos

    Returns:
        Lista filtrada de casos
    """
    resultado = casos

    # Filtro por núcleo
    nucleo_filtro = filtros.get('nucleo', 'Todos')
    if nucleo_filtro and nucleo_filtro != 'Todos':
        resultado = [c for c in resultado if c.get('nucleo') == nucleo_filtro]

    # Filtro por status
    status_filtro = filtros.get('status', 'Todos')
    if status_filtro and status_filtro != 'Todos':
        resultado = [c for c in resultado if c.get('status') == status_filtro]

    # Filtro por categoria
    categoria_filtro = filtros.get('categoria', 'Todos')
    if categoria_filtro and categoria_filtro != 'Todos':
        resultado = [c for c in resultado if c.get('categoria') == categoria_filtro]

    # Filtro por estado
    estado_filtro = filtros.get('estado', 'Todos')
    if estado_filtro and estado_filtro != 'Todos':
        resultado = [c for c in resultado if c.get('estado') == estado_filtro]

    # Filtro por busca textual
    busca = filtros.get('busca', '').strip().lower()
    if busca:
        def match_busca(caso):
            titulo = (caso.get('titulo') or '').lower()
            descricao = (caso.get('descricao') or '').lower()
            clientes = ' '.join(caso.get('clientes_nomes', [])).lower()

            return (
                busca in titulo or
                busca in descricao or
                busca in clientes
            )

        resultado = [c for c in resultado if match_busca(c)]

    return resultado


# =============================================================================
# PÁGINA DE DETALHES DO CASO
# =============================================================================


@ui.page('/visao-geral/casos/{caso_id}')
def caso_detalhes(caso_id: str):
    """Página de detalhes de um caso específico."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    definir_workspace('visao_geral_escritorio')

    caso = buscar_caso(caso_id)
    if not caso:
        ui.navigate.to('/visao-geral/casos')
        ui.notify('Caso não encontrado.', type='negative')
        return

    _renderizar_detalhes_caso(caso)


def _renderizar_detalhes_caso(caso: dict):
    """Renderiza a página de detalhes de um caso (simplificada)."""
    titulo = caso.get('titulo', 'Caso sem título')
    caso_id = caso.get('_id', '')

    # Carregar clientes para o formulário de edição
    todas_pessoas = listar_pessoas()

    with layout(
        f'Caso: {titulo}',
        breadcrumbs=[
            ('Visão geral do escritório', '/visao-geral/painel'),
            ('Casos', '/visao-geral/casos'),
            (titulo, None)
        ]
    ):
        # CSS adicional
        ui.add_head_html('''
        <style>
        .detail-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .detail-label {
            font-size: 12px;
            color: #6b7280;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .detail-value {
            font-size: 14px;
            color: #374151;
        }
        </style>
        ''')

        # Header com título e botão excluir
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label(f'Caso: {titulo}').classes('text-2xl font-bold text-gray-800')

            def ao_excluir():
                def executar():
                    if excluir_caso(caso_id):
                        ui.notify('Caso excluído com sucesso!', type='positive')
                        ui.navigate.to('/visao-geral/casos')
                    else:
                        ui.notify('Erro ao excluir caso.', type='negative')

                confirmar_exclusao(caso, on_confirm=executar)

            ui.button('Excluir Caso', icon='delete', on_click=ao_excluir).props(
                'color=negative outline'
            )

        # Abas
        with ui.tabs().classes('w-full').props('align=left no-caps dense') as tabs:
            tab_dados = ui.tab('Dados básicos')
            tab_processos = ui.tab('Processos')

        with ui.tab_panels(tabs, value=tab_dados).classes('w-full'):
            # Aba Dados Básicos
            with ui.tab_panel(tab_dados).classes('p-0'):
                _renderizar_aba_dados_basicos(caso, todas_pessoas, caso_id)

            # Aba Processos
            with ui.tab_panel(tab_processos).classes('p-0'):
                _renderizar_aba_processos()


def _renderizar_aba_dados_basicos(caso: dict, todas_pessoas: list, caso_id: str):
    """Renderiza a aba de dados básicos do caso (simplificada)."""
    with ui.card().classes('w-full detail-card p-6'):
        with ui.column().classes('w-full gap-4'):
            # Título
            titulo_input = ui.input(
                label='Título do Caso *',
                value=caso.get('titulo', '')
            ).classes('w-full').props('dense outlined')

            # Linha 1: Núcleo, Status, Categoria
            with ui.row().classes('w-full gap-4'):
                nucleo_select = ui.select(
                    options=NUCLEO_OPTIONS,
                    value=caso.get('nucleo', 'Generalista'),
                    label='Núcleo *'
                ).classes('flex-1').props('dense outlined')

                status_select = ui.select(
                    options=STATUS_OPTIONS,
                    value=caso.get('status', 'Em andamento'),
                    label='Status'
                ).classes('flex-1').props('dense outlined')

                categoria_select = ui.select(
                    options=CATEGORIA_OPTIONS,
                    value=caso.get('categoria', 'Contencioso'),
                    label='Categoria'
                ).classes('flex-1').props('dense outlined')

            # Linha 2: Estado
            estado_select = ui.select(
                options=[''] + ESTADOS,
                value=caso.get('estado', ''),
                label='Estado'
            ).classes('w-full').props('dense outlined clearable')

            # Seção Clientes
            ui.separator().classes('my-2')
            ui.label('CLIENTES VINCULADOS').classes('text-sm font-bold text-gray-600')

            clientes_atuais = caso.get('clientes', [])
            clientes_nomes = caso.get('clientes_nomes', [])

            if clientes_nomes:
                with ui.row().classes('w-full gap-2 flex-wrap'):
                    for nome in clientes_nomes:
                        ui.label(nome).classes(
                            'px-3 py-1 rounded-full text-sm bg-gray-200'
                        )
            else:
                ui.label('Nenhum cliente vinculado').classes('text-sm text-gray-400 italic')

            ui.label('Para editar clientes, use o botão "Editar" na página de listagem.').classes(
                'text-xs text-gray-400 mt-1'
            )

            # Descrição
            ui.separator().classes('my-2')
            descricao_input = ui.textarea(
                label='Descrição',
                value=caso.get('descricao', '')
            ).classes('w-full').props('dense outlined rows=4')

            # Botão Salvar
            ui.separator().classes('my-2')

            def salvar_dados():
                novos_dados = {
                    'titulo': titulo_input.value.strip() if titulo_input.value else '',
                    'nucleo': nucleo_select.value or 'Generalista',
                    'status': status_select.value or 'Em andamento',
                    'categoria': categoria_select.value or 'Contencioso',
                    'estado': estado_select.value or '',
                    'clientes': clientes_atuais,
                    'clientes_nomes': clientes_nomes,
                    'descricao': descricao_input.value.strip() if descricao_input.value else '',
                }

                # Validação básica
                if not novos_dados['titulo']:
                    ui.notify('Título é obrigatório.', type='negative')
                    return

                if len(novos_dados['titulo']) < 3:
                    ui.notify('Título deve ter pelo menos 3 caracteres.', type='negative')
                    return

                try:
                    if atualizar_caso(caso_id, novos_dados):
                        ui.notify('Dados salvos com sucesso!', type='positive')
                    else:
                        ui.notify('Erro ao salvar dados.', type='negative')
                except Exception as e:
                    print(f"Erro ao salvar caso: {e}")
                    ui.notify(f'Erro: {str(e)}', type='negative')

            with ui.row().classes('w-full justify-end'):
                ui.button('Salvar Alterações', icon='save', on_click=salvar_dados).props(
                    'color=primary'
                )


def _renderizar_aba_processos():
    """Renderiza a aba de processos (placeholder)."""
    with ui.card().classes('w-full detail-card p-6'):
        with ui.column().classes('w-full items-center py-12'):
            ui.icon('gavel', size='64px').classes('text-gray-300')
            ui.label('Módulo de Processos').classes('text-lg font-bold text-gray-500 mt-4')
            ui.label('Em desenvolvimento').classes('text-sm text-gray-400')
