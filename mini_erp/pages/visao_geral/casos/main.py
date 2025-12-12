"""
Página principal do módulo Casos do workspace Visão Geral.
Rota: /visao-geral/casos
Visualização em Cards responsivos.

Campos simplificados:
- titulo, nucleo, status, categoria, estado, clientes, descricao
- REMOVIDOS: ano, mes, parte_contraria

Abas na página de detalhes:
- Dados básicos, Processos, Relatório geral, Vistorias,
- Estratégia geral, Próximas ações, Slack, Links úteis
"""
import asyncio
from nicegui import ui
from ....core import layout, PRIMARY_COLOR
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from .database import listar_casos, excluir_caso, buscar_caso, atualizar_caso, atualizar_prioridade_caso
from .caso_dialog import abrir_dialog_caso, confirmar_exclusao
from .models import (
    NUCLEO_OPTIONS,
    STATUS_OPTIONS,
    CATEGORIA_OPTIONS,
    ESTADOS,
    PRIORIDADE_OPTIONS,
    PRIORIDADE_PADRAO,
    obter_cor_nucleo,
    sanitizar_estado,
)
from .componentes import criar_badge_prioridade
from ..pessoas.database import listar_pessoas_colecao_people


# =============================================================================
# TIPOS DE LINKS PARA ABA "LINKS ÚTEIS"
# =============================================================================

LINK_TYPES = ['Google Drive', 'NotebookLM', 'Ayoa', 'Slack', 'Outros']

LINK_ICONS = {
    'Google Drive': 'folder',
    'NotebookLM': 'auto_stories',
    'Ayoa': 'hub',
    'Slack': 'chat',
    'Outros': 'link',
}


# =============================================================================
# SISTEMA DE AUTOSAVE
# =============================================================================

# Estado global do autosave (por sessão)
_autosave_states = {}


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


def _get_autosave_state(caso_id: str) -> dict:
    """Obtém o estado de autosave para um caso específico."""
    if caso_id not in _autosave_states:
        _autosave_states[caso_id] = {
            'timer': None,
            'is_saving': False,
            'refresh_callbacks': []
        }
    return _autosave_states[caso_id]


def _register_autosave_refresh(caso_id: str, callback):
    """Registra callback para atualizar indicadores de salvamento."""
    state = _get_autosave_state(caso_id)
    if callback not in state['refresh_callbacks']:
        state['refresh_callbacks'].append(callback)


def _refresh_all_indicators(caso_id: str):
    """Atualiza todos os indicadores de salvamento."""
    state = _get_autosave_state(caso_id)
    for callback in state['refresh_callbacks']:
        try:
            callback.refresh()
        except Exception:
            pass


async def _autosave_with_debounce(caso: dict, caso_id: str, delay: float = 2.0):
    """
    Salva o caso após um delay (debounce).
    Cancela salvamentos pendentes se houver nova edição.
    """
    state = _get_autosave_state(caso_id)

    # Cancela timer anterior se existir
    if state['timer']:
        state['timer'].cancel()

    async def delayed_save():
        await asyncio.sleep(delay)
        state['is_saving'] = True
        _refresh_all_indicators(caso_id)

        await asyncio.sleep(0.3)  # Mostra o indicador brevemente

        try:
            # Remove campos que não devem ser salvos diretamente
            dados_para_salvar = {k: v for k, v in caso.items() if k != '_id'}
            atualizar_caso(caso_id, dados_para_salvar)
        except Exception as e:
            print(f'Erro no autosave do caso {caso_id}: {e}')

        state['is_saving'] = False
        _refresh_all_indicators(caso_id)

    state['timer'] = asyncio.create_task(delayed_save())


def _trigger_autosave(caso: dict, caso_id: str):
    """Dispara o salvamento automático com debounce."""
    asyncio.create_task(_autosave_with_debounce(caso, caso_id))


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
            'prioridade': None,  # None = Todas as prioridades
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

                    # Filtro por prioridade
                    prioridade_select = ui.select(
                        options=[{'label': 'Todas', 'value': None}] + [
                            {'label': p, 'value': p} for p in PRIORIDADE_OPTIONS
                        ],
                        value=None,
                        label='Prioridade'
                    ).classes('w-32').props('dense outlined')

                    # Botão limpar filtros
                    def limpar_filtros():
                        busca_input.value = ''
                        nucleo_select.value = 'Todos'
                        status_select.value = 'Todos'
                        categoria_select.value = 'Todos'
                        estado_select.value = 'Todos'
                        prioridade_select.value = None
                        filtros['busca'] = ''
                        filtros['nucleo'] = 'Todos'
                        filtros['status'] = 'Todos'
                        filtros['categoria'] = 'Todos'
                        filtros['estado'] = 'Todos'
                        filtros['prioridade'] = None
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
                        filtros['prioridade'] = prioridade_select.value
                        if refresh_ref['func']:
                            refresh_ref['func'].refresh()

                    busca_input.on('update:model-value', lambda: aplicar_filtros())
                    nucleo_select.on('update:model-value', lambda: aplicar_filtros())
                    status_select.on('update:model-value', lambda: aplicar_filtros())
                    categoria_select.on('update:model-value', lambda: aplicar_filtros())
                    estado_select.on('update:model-value', lambda: aplicar_filtros())
                    prioridade_select.on('update:model-value', lambda: aplicar_filtros())

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

    # Ordena por prioridade (P1 primeiro, P4 por último)
    # Se mesma prioridade, mantém ordem original (mais recente primeiro já vem do banco)
    def obter_ordem_prioridade(caso):
        prioridade = caso.get('prioridade', PRIORIDADE_PADRAO)
        ordem_map = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
        return ordem_map.get(prioridade, 4)
    
    casos_filtrados.sort(key=lambda c: obter_ordem_prioridade(c))

    # Contador de resultados
    total = len(casos_filtrados)
    total_geral = len(todos_casos)

    tem_filtros = (
        filtros['busca'] or
        filtros['nucleo'] != 'Todos' or
        filtros['status'] != 'Todos' or
        filtros['categoria'] != 'Todos' or
        filtros['estado'] != 'Todos' or
        filtros['prioridade'] is not None
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
            # Linha 2: Badges (Núcleo + Prioridade)
            with ui.row().classes('w-full gap-2 items-center'):
                # Badge do Núcleo
                ui.label(nucleo).classes('caso-badge').style(
                    f'background-color: {cor_nucleo}; color: white;'
                )
                # Badge de Prioridade
                prioridade = caso.get('prioridade', PRIORIDADE_PADRAO)
                criar_badge_prioridade(prioridade)

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

    # Filtro por prioridade
    prioridade_filtro = filtros.get('prioridade')
    if prioridade_filtro:
        # Normaliza prioridade para comparação (garante P4 se não tiver)
        resultado = [
            c for c in resultado
            if (c.get('prioridade') or PRIORIDADE_PADRAO) == prioridade_filtro
        ]

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
    """
    Renderiza a página de detalhes de um caso com 8 abas:
    1. Dados básicos
    2. Processos
    3. Relatório geral do caso
    4. Vistorias
    5. Estratégia geral
    6. Próximas ações
    7. Slack
    8. Links úteis
    """
    titulo = caso.get('titulo', 'Caso sem título')
    caso_id = caso.get('_id', '')

    # Carregar clientes da coleção 'people' (principal do sistema)
    todas_pessoas = listar_pessoas_colecao_people()
    print(f"[DETALHES CASO] {len(todas_pessoas)} pessoas carregadas para seleção")

    with layout(
        f'Caso: {titulo}',
        breadcrumbs=[
            ('Visão geral do escritório', '/visao-geral/painel'),
            ('Casos', '/visao-geral/casos'),
            (titulo, None)
        ]
    ):
        # CSS adicional para detalhes e abas
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
        .link-card {
            transition: all 0.2s ease;
        }
        .link-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        </style>
        ''')

        # Header com título, badge de prioridade e botão excluir
        with ui.row().classes('w-full justify-between items-center mb-4'):
            with ui.row().classes('items-center gap-3'):
                ui.label(f'Caso: {titulo}').classes('text-2xl font-bold text-gray-800')
                
                # Badge de prioridade no header
                @ui.refreshable
                def badge_prioridade_header_refresh():
                    prioridade = caso.get('prioridade', PRIORIDADE_PADRAO)
                    criar_badge_prioridade(prioridade)
                
                # Guarda referência para uso em outras abas
                badge_refresh_ref = {'func': badge_prioridade_header_refresh}
                
                badge_prioridade_header_refresh()

            with ui.row().classes('gap-2'):
                # Indicador de salvamento automático
                @ui.refreshable
                def save_indicator_header():
                    state = _get_autosave_state(caso_id)
                    if state['is_saving']:
                        with ui.row().classes('items-center gap-1'):
                            ui.spinner('dots', size='xs').classes('text-yellow-600')
                            ui.label('Salvando...').classes('text-xs text-yellow-600')
                    else:
                        ui.label('Salvamento automático ativado').classes(
                            'text-xs text-green-600 italic'
                        )

                _register_autosave_refresh(caso_id, save_indicator_header)
                save_indicator_header()

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

        # Sistema de Abas (8 abas)
        with ui.tabs().classes('w-full bg-white').props('align=left no-caps') as tabs:
            tab_dados = ui.tab('Dados básicos')
            tab_processos = ui.tab('Processos')
            tab_relatorio = ui.tab('Relatório geral do caso')
            tab_vistorias = ui.tab('Vistorias')
            tab_estrategia = ui.tab('Estratégia geral')
            tab_acoes = ui.tab('Próximas ações')
            tab_slack = ui.tab('Slack')
            tab_links = ui.tab('Links úteis')

        with ui.tab_panels(tabs, value=tab_dados).classes('w-full'):
            # Aba 1: Dados Básicos
            with ui.tab_panel(tab_dados).classes('p-0'):
                _renderizar_aba_dados_basicos(caso, todas_pessoas, caso_id, badge_refresh_ref)

            # Aba 2: Processos
            with ui.tab_panel(tab_processos).classes('p-0'):
                _renderizar_aba_processos(caso, caso_id)

            # Aba 3: Relatório geral do caso
            with ui.tab_panel(tab_relatorio).classes('p-0'):
                _renderizar_aba_texto_rico(
                    caso, caso_id,
                    campo='relatorio_geral',
                    titulo='Relatório Geral do Caso',
                    placeholder='Digite o relatório geral do caso aqui...'
                )

            # Aba 4: Vistorias
            with ui.tab_panel(tab_vistorias).classes('p-0'):
                _renderizar_aba_texto_rico(
                    caso, caso_id,
                    campo='vistorias',
                    titulo='Vistorias',
                    placeholder='Registre informações sobre vistorias...'
                )

            # Aba 5: Estratégia geral
            with ui.tab_panel(tab_estrategia).classes('p-0'):
                _renderizar_aba_texto_rico(
                    caso, caso_id,
                    campo='estrategia_geral',
                    titulo='Estratégia Geral',
                    placeholder='Descreva a estratégia geral do caso...'
                )

            # Aba 6: Próximas ações
            with ui.tab_panel(tab_acoes).classes('p-0'):
                _renderizar_aba_texto_rico(
                    caso, caso_id,
                    campo='proximas_acoes',
                    titulo='Próximas Ações',
                    placeholder='Liste as próximas ações a serem tomadas...'
                )

            # Aba 7: Slack
            with ui.tab_panel(tab_slack).classes('p-0'):
                _renderizar_aba_slack()

            # Aba 8: Links úteis
            with ui.tab_panel(tab_links).classes('p-0'):
                _renderizar_aba_links(caso, caso_id)


def _renderizar_aba_dados_basicos(caso: dict, todas_pessoas: list, caso_id: str, badge_refresh_ref: dict = None):
    """Renderiza a aba de dados básicos do caso com autosave."""
    # Estado local para clientes selecionados (cópia para manipulação)
    clientes_selecionados = list(caso.get('clientes', []))

    with ui.card().classes('w-full detail-card p-6'):
        with ui.column().classes('w-full gap-4'):

            # Funções de autosave para cada campo
            def on_titulo_change(e):
                caso['titulo'] = e.value.strip() if e.value else ''
                _trigger_autosave(caso, caso_id)

            def on_nucleo_change(e):
                caso['nucleo'] = e.value or 'Generalista'
                _trigger_autosave(caso, caso_id)

            def on_status_change(e):
                caso['status'] = e.value or 'Em andamento'
                _trigger_autosave(caso, caso_id)

            def on_categoria_change(e):
                caso['categoria'] = e.value or 'Contencioso'
                _trigger_autosave(caso, caso_id)

            def on_estado_change(e):
                caso['estado'] = e.value or ''
                _trigger_autosave(caso, caso_id)

            def on_descricao_change(e):
                caso['descricao'] = e.value.strip() if e.value else ''
                _trigger_autosave(caso, caso_id)

            # Título
            ui.input(
                label='Título do Caso *',
                value=caso.get('titulo', ''),
                on_change=on_titulo_change
            ).classes('w-full').props('dense outlined')

            # Linha 1: Núcleo, Status, Categoria, Prioridade
            with ui.row().classes('w-full gap-4'):
                ui.select(
                    options=NUCLEO_OPTIONS,
                    value=caso.get('nucleo', 'Generalista'),
                    label='Núcleo *',
                    on_change=on_nucleo_change
                ).classes('flex-1').props('dense outlined')

                ui.select(
                    options=STATUS_OPTIONS,
                    value=caso.get('status', 'Em andamento'),
                    label='Status',
                    on_change=on_status_change
                ).classes('flex-1').props('dense outlined')

                ui.select(
                    options=CATEGORIA_OPTIONS,
                    value=caso.get('categoria', 'Contencioso'),
                    label='Categoria',
                    on_change=on_categoria_change
                ).classes('flex-1').props('dense outlined')

                # Select de Prioridade
                prioridade_atual = caso.get('prioridade', PRIORIDADE_PADRAO)
                
                def on_prioridade_change(e):
                    nova_prioridade = e.value or PRIORIDADE_PADRAO
                    caso['prioridade'] = nova_prioridade
                    # Atualiza diretamente no banco usando função específica
                    if atualizar_prioridade_caso(caso_id, nova_prioridade):
                        ui.notify('Prioridade atualizada!', type='positive')
                        _trigger_autosave(caso, caso_id)
                        # Atualiza badge visual no header (se referência disponível)
                        if badge_refresh_ref and badge_refresh_ref.get('func'):
                            badge_refresh_ref['func'].refresh()
                    else:
                        ui.notify('Erro ao atualizar prioridade.', type='negative')

                ui.select(
                    options=PRIORIDADE_OPTIONS,
                    value=prioridade_atual,
                    label='Prioridade',
                    on_change=on_prioridade_change
                ).classes('flex-1').props('dense outlined')

            # Linha 2: Estado (com sanitização para evitar erro SC/PR)
            ui.select(
                options=[''] + ESTADOS,
                value=sanitizar_estado(caso.get('estado', '')),
                label='Estado',
                on_change=on_estado_change
            ).classes('w-full').props('dense outlined clearable')

            # Seção Clientes Vinculados (editável)
            ui.separator().classes('my-2')
            ui.label('CLIENTES VINCULADOS').classes('text-sm font-bold text-gray-600 mb-2')

            # Preparar opções de clientes para o select
            opcoes_clientes = [
                {
                    'label': p.get('nome_exibicao', p.get('full_name', 'Sem nome')),
                    'value': p['_id']
                }
                for p in todas_pessoas
            ]

            # Criar dicionário de opcoes_pessoas (id -> nome) para uso nos chips
            opcoes_pessoas = {
                p['_id']: p.get('nome_exibicao', p.get('full_name', 'Sem nome'))
                for p in todas_pessoas
            }

            # Linha com select + botão adicionar
            with ui.row().classes('w-full gap-2 items-end'):
                cliente_select = ui.select(
                    options=opcoes_clientes,
                    label='Buscar pessoa...',
                    with_input=True
                ).classes('flex-grow').props('dense outlined clearable use-input input-debounce="300"')
                if len(opcoes_pessoas) > 0:
                    select_cliente = ui.select(
                        options=opcoes_pessoas,
                        label='Buscar pessoa...',
                        with_input=True
                    ).props('dense outlined clearable use-input input-debounce="200"').classes('flex-1')
                else:
                    ui.label('⚠️ Erro: Nenhuma pessoa encontrada').classes('text-red-500 flex-1')
                    select_cliente = None
                
                def ao_clicar_adicionar():
                    nonlocal clientes_selecionados
                    if select_cliente and select_cliente.value:
                        cliente_id = select_cliente.value
                        if cliente_id not in clientes_selecionados:
                            clientes_selecionados.append(cliente_id)
                            
                            # Atualiza IDs
                            caso['clientes'] = clientes_selecionados
                            
                            # Atualiza Nomes (para visualização nos cards)
                            caso['clientes_nomes'] = [
                                opcoes_pessoas.get(cid, '') 
                                for cid in clientes_selecionados
                            ]
                            
                            # Disparar autosave
                            _trigger_autosave(caso, caso_id)
                            atualizar_chips_clientes()
                        
                        select_cliente.value = None
                
                ui.button(icon='add', on_click=ao_clicar_adicionar).props('flat dense').classes('text-primary')

            # Container dos chips
            container_chips = ui.column().classes('w-full mt-2')

            def atualizar_chips_clientes():
                container_chips.clear()
                with container_chips:
                    if not clientes_selecionados:
                        ui.label('Nenhum cliente vinculado').classes('text-gray-400 italic text-sm')
                    else:
                        with ui.row().classes('gap-2 flex-wrap'):
                            for cid in clientes_selecionados:
                                nome_exibir = opcoes_pessoas.get(cid, cid)
                                
                                def criar_remover(cliente_id_para_remover):
                                    def remover():
                                        nonlocal clientes_selecionados
                                        if cliente_id_para_remover in clientes_selecionados:
                                            clientes_selecionados.remove(cliente_id_para_remover)
                                            
                                            caso['clientes'] = clientes_selecionados
                                            caso['clientes_nomes'] = [
                                                opcoes_pessoas.get(c, '') 
                                                for c in clientes_selecionados
                                            ]
                                            
                                            _trigger_autosave(caso, caso_id)
                                            atualizar_chips_clientes()
                                    return remover
                                
                                chip = ui.chip(
                                    text=nome_exibir,
                                    removable=True,
                                    color='primary'
                                ).props('outline')
                                chip.on('remove', criar_remover(cid))

            # Renderizar chips iniciais
            atualizar_chips_clientes()

            # Descrição
            ui.separator().classes('my-2')
            ui.textarea(
                label='Descrição',
                value=caso.get('descricao', ''),
                on_change=on_descricao_change
            ).classes('w-full').props('dense outlined rows=4')


# =============================================================================
# ABA: PROCESSOS
# =============================================================================


def _renderizar_aba_processos(caso: dict, caso_id: str):
    """
    Renderiza a aba de processos vinculados ao caso.
    Inclui tabela com CRUD e botões de ação.
    """
    with ui.card().classes('w-full detail-card p-6'):
        # Header com botões
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label('Processos Vinculados').classes('text-lg font-bold text-gray-800')

            with ui.row().classes('gap-2'):
                @ui.refreshable
                def render_processos_table():
                    """Renderiza a tabela de processos vinculados."""
                    # Por enquanto, processos são armazenados como array no caso
                    processos = caso.get('processos_vinculados', [])

                    if not processos:
                        with ui.column().classes('w-full items-center py-8'):
                            ui.icon('gavel', size='48px').classes('text-gray-300')
                            ui.label('Nenhum processo vinculado').classes(
                                'text-gray-500 mt-2'
                            )
                            ui.label('Clique em "Novo Processo" para adicionar.').classes(
                                'text-sm text-gray-400'
                            )
                        return

                    # Colunas da tabela
                    columns = [
                        {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True},
                        {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'sortable': True},
                        {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left'},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                        {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center'},
                    ]

                    # Preparar rows
                    rows = []
                    for i, proc in enumerate(processos):
                        rows.append({
                            '_index': i,
                            'area': proc.get('area', '-'),
                            'titulo': proc.get('titulo', 'Sem título'),
                            'numero': proc.get('numero', '-'),
                            'status': proc.get('status', 'Em andamento'),
                        })

                    table = ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='_index',
                        pagination={'rowsPerPage': 10}
                    ).classes('w-full').props('flat bordered dense')

                    # Slot para botões de ação
                    table.add_slot('body-cell-acoes', '''
                        <q-td :props="props">
                            <q-btn flat dense round icon="edit" size="sm"
                                   @click="$parent.$emit('editar', props.row)" />
                            <q-btn flat dense round icon="delete" size="sm" color="negative"
                                   @click="$parent.$emit('excluir', props.row)" />
                        </q-td>
                    ''')

                    def editar_processo(e):
                        idx = e.args['_index']
                        _abrir_dialog_processo(caso, caso_id, idx, render_processos_table)

                    def excluir_processo(e):
                        idx = e.args['_index']
                        _confirmar_exclusao_processo(caso, caso_id, idx, render_processos_table)

                    table.on('editar', editar_processo)
                    table.on('excluir', excluir_processo)

                def atualizar_lista():
                    render_processos_table.refresh()

                ui.button('Atualizar', icon='refresh', on_click=atualizar_lista).props(
                    'flat dense'
                )

                def novo_processo():
                    _abrir_dialog_processo(caso, caso_id, None, render_processos_table)

                ui.button('Novo Processo', icon='add', on_click=novo_processo).props(
                    'color=primary'
                )

        ui.separator().classes('mb-4')

        # Tabela de processos
        render_processos_table()


def _abrir_dialog_processo(caso: dict, caso_id: str, index: int = None, refresh_func=None):
    """
    Abre dialog para criar ou editar um processo vinculado ao caso.

    Args:
        caso: Dicionário do caso
        caso_id: ID do caso
        index: Índice do processo (None para novo)
        refresh_func: Função para atualizar a tabela
    """
    is_edicao = index is not None
    processos = caso.get('processos_vinculados', [])

    if is_edicao:
        processo = processos[index].copy()
    else:
        processo = {
            'area': 'Administrativo',
            'titulo': '',
            'numero': '',
            'status': 'Em andamento',
            'clientes': '',
            'parte_contraria': '',
            'descricao': '',
        }

    AREA_OPTIONS = ['Administrativo', 'Criminal', 'Civil', 'Tributário', 'Técnicos/projetos']
    STATUS_PROCESSO_OPTIONS = ['Em andamento', 'Suspenso', 'Arquivado', 'Concluído']

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        # Header
        with ui.row().classes('w-full items-center justify-between p-4').style(
            f'background: {PRIMARY_COLOR};'
        ):
            ui.label('Editar Processo' if is_edicao else 'Novo Processo').classes(
                'text-white font-bold text-lg'
            )
            ui.button(icon='close', on_click=dialog.close).props('flat round color=white')

        # Formulário
        with ui.scroll_area().classes('w-full').style('max-height: 70vh'):
            with ui.column().classes('w-full gap-4 p-4'):
                # Linha 1: Área e Status
                with ui.row().classes('w-full gap-4'):
                    area_select = ui.select(
                        options=AREA_OPTIONS,
                        value=processo.get('area', 'Administrativo'),
                        label='Área *'
                    ).classes('flex-1').props('dense outlined')

                    status_select = ui.select(
                        options=STATUS_PROCESSO_OPTIONS,
                        value=processo.get('status', 'Em andamento'),
                        label='Status'
                    ).classes('flex-1').props('dense outlined')

                # Título
                titulo_input = ui.input(
                    label='Título do Processo *',
                    value=processo.get('titulo', '')
                ).classes('w-full').props('dense outlined')

                # Número do processo
                numero_input = ui.input(
                    label='Número do Processo',
                    value=processo.get('numero', ''),
                    placeholder='0000000-00.0000.0.00.0000'
                ).classes('w-full').props('dense outlined')

                # Clientes e Parte Contrária
                with ui.row().classes('w-full gap-4'):
                    clientes_input = ui.input(
                        label='Clientes',
                        value=processo.get('clientes', '')
                    ).classes('flex-1').props('dense outlined')

                    parte_contraria_input = ui.input(
                        label='Parte Contrária',
                        value=processo.get('parte_contraria', '')
                    ).classes('flex-1').props('dense outlined')

                # Descrição
                descricao_input = ui.textarea(
                    label='Descrição',
                    value=processo.get('descricao', '')
                ).classes('w-full').props('dense outlined rows=3')

        ui.separator()

        # Botões
        with ui.row().classes('w-full justify-end gap-2 p-4'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def salvar():
                # Validação
                if not titulo_input.value or not titulo_input.value.strip():
                    ui.notify('Título é obrigatório.', type='negative')
                    return

                # Coleta dados
                novo_processo = {
                    'area': area_select.value,
                    'titulo': titulo_input.value.strip(),
                    'numero': numero_input.value.strip() if numero_input.value else '',
                    'status': status_select.value,
                    'clientes': clientes_input.value.strip() if clientes_input.value else '',
                    'parte_contraria': parte_contraria_input.value.strip() if parte_contraria_input.value else '',
                    'descricao': descricao_input.value.strip() if descricao_input.value else '',
                }

                # Atualiza lista de processos
                if 'processos_vinculados' not in caso:
                    caso['processos_vinculados'] = []

                if is_edicao:
                    caso['processos_vinculados'][index] = novo_processo
                    msg = 'Processo atualizado com sucesso!'
                else:
                    caso['processos_vinculados'].append(novo_processo)
                    msg = 'Processo adicionado com sucesso!'

                # Salva o caso
                _trigger_autosave(caso, caso_id)

                ui.notify(msg, type='positive')
                dialog.close()

                if refresh_func:
                    refresh_func.refresh()

            ui.button('Salvar', icon='save', on_click=salvar).props('color=primary')

    dialog.open()


def _confirmar_exclusao_processo(caso: dict, caso_id: str, index: int, refresh_func=None):
    """Dialog de confirmação de exclusão de processo."""
    processos = caso.get('processos_vinculados', [])
    if index >= len(processos):
        return

    processo = processos[index]
    titulo = processo.get('titulo', 'Processo')

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('warning', color='negative', size='32px')
            ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800')

        ui.label(f'Deseja excluir o processo "{titulo}"?').classes('text-gray-600 mb-2')
        ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def executar():
                caso['processos_vinculados'].pop(index)
                _trigger_autosave(caso, caso_id)
                ui.notify('Processo excluído com sucesso!', type='positive')
                dialog.close()
                if refresh_func:
                    refresh_func.refresh()

            ui.button('Excluir', on_click=executar).props('color=negative')

    dialog.open()


# =============================================================================
# ABA: TEXTO RICO (Relatório, Vistorias, Estratégia, Próximas Ações)
# =============================================================================


def _renderizar_aba_texto_rico(caso: dict, caso_id: str, campo: str, titulo: str, placeholder: str):
    """
    Renderiza uma aba com editor de texto rico e autosave.

    Args:
        caso: Dicionário do caso
        caso_id: ID do caso
        campo: Nome do campo no dicionário (ex: 'relatorio_geral')
        titulo: Título exibido na aba
        placeholder: Texto placeholder do editor
    """
    with ui.card().classes('w-full detail-card p-6'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label(titulo).classes('text-lg font-bold text-gray-800')

            # Indicador de salvamento
            @ui.refreshable
            def save_indicator():
                state = _get_autosave_state(caso_id)
                if state['is_saving']:
                    with ui.row().classes('items-center gap-1'):
                        ui.spinner('dots', size='xs').classes('text-yellow-600')
                        ui.label('Salvando...').classes('text-xs text-yellow-600')
                else:
                    ui.label('Salvamento automático').classes('text-xs text-green-600 italic')

            _register_autosave_refresh(caso_id, save_indicator)
            save_indicator()

        # Editor de texto rico
        def on_change(e):
            caso[campo] = e.value
            _trigger_autosave(caso, caso_id)

        ui.editor(
            value=caso.get(campo, ''),
            placeholder=placeholder,
            on_change=on_change
        ).classes('w-full').style('min-height: 350px')


# =============================================================================
# ABA: SLACK (Placeholder)
# =============================================================================


def _renderizar_aba_slack():
    """Renderiza a aba de Slack (placeholder para integração futura)."""
    with ui.card().classes('w-full detail-card p-6'):
        with ui.column().classes('w-full items-center py-12'):
            ui.icon('chat', size='64px').classes('text-gray-300')
            ui.label('Integração com Slack').classes('text-lg font-bold text-gray-500 mt-4')
            ui.label('No futuro, o Slack do escritório será integrado neste local.').classes(
                'text-sm text-gray-400 text-center max-w-md'
            )


# =============================================================================
# ABA: LINKS ÚTEIS
# =============================================================================


def _renderizar_aba_links(caso: dict, caso_id: str):
    """
    Renderiza a aba de links úteis com CRUD.
    Tipos: Google Drive, NotebookLM, Ayoa, Slack, Outros.
    """
    with ui.card().classes('w-full detail-card p-6'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label('Links Úteis').classes('text-lg font-bold text-gray-800')

            def novo_link():
                _abrir_dialog_link(caso, caso_id, None, render_links_list)

            ui.button('Adicionar Link', icon='add_link', on_click=novo_link).props(
                'color=primary'
            )

        ui.separator().classes('mb-4')

        # Lista de links
        @ui.refreshable
        def render_links_list():
            links = caso.get('links', [])

            if not links:
                with ui.column().classes('w-full items-center py-8'):
                    ui.icon('link_off', size='48px').classes('text-gray-300')
                    ui.label('Nenhum link cadastrado').classes('text-gray-500 mt-2')
                    ui.label('Clique em "Adicionar Link" para começar.').classes(
                        'text-sm text-gray-400'
                    )
                return

            # Grid de cards de links
            with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'):
                for i, link in enumerate(links):
                    _renderizar_card_link(link, i, caso, caso_id, render_links_list)

        render_links_list()


def _renderizar_card_link(link: dict, index: int, caso: dict, caso_id: str, refresh_func):
    """Renderiza um card de link."""
    titulo = link.get('titulo', 'Sem título')
    url = link.get('url', '#')
    tipo = link.get('tipo', 'Outros')
    icon = LINK_ICONS.get(tipo, 'link')

    with ui.card().classes('p-4 link-card border').style(f'border-color: {PRIMARY_COLOR};'):
        with ui.row().classes('w-full justify-between items-start'):
            # Ícone e título
            with ui.row().classes('items-center gap-2 flex-1'):
                ui.icon(icon, size='24px').style(f'color: {PRIMARY_COLOR};')
                with ui.column().classes('gap-0'):
                    ui.link(titulo, url, new_tab=True).classes(
                        'text-base font-medium text-gray-800 hover:underline'
                    )
                    ui.label(tipo).classes('text-xs text-gray-500')

            # Menu de ações
            with ui.button(icon='more_vert').props('flat round dense size=sm'):
                with ui.menu():
                    def editar(idx=index):
                        _abrir_dialog_link(caso, caso_id, idx, refresh_func)

                    def excluir(idx=index):
                        _confirmar_exclusao_link(caso, caso_id, idx, refresh_func)

                    ui.menu_item('Editar', on_click=editar)
                    ui.menu_item('Excluir', on_click=excluir)


def _abrir_dialog_link(caso: dict, caso_id: str, index: int = None, refresh_func=None):
    """
    Abre dialog para criar ou editar um link.

    Args:
        caso: Dicionário do caso
        caso_id: ID do caso
        index: Índice do link (None para novo)
        refresh_func: Função para atualizar a lista
    """
    is_edicao = index is not None
    links = caso.get('links', [])

    if is_edicao:
        link = links[index].copy()
    else:
        link = {
            'titulo': '',
            'url': '',
            'tipo': 'Google Drive',
        }

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
        # Header
        with ui.row().classes('w-full items-center justify-between p-4').style(
            f'background: {PRIMARY_COLOR};'
        ):
            ui.label('Editar Link' if is_edicao else 'Novo Link').classes(
                'text-white font-bold text-lg'
            )
            ui.button(icon='close', on_click=dialog.close).props('flat round color=white')

        # Formulário
        with ui.column().classes('w-full gap-4 p-4'):
            titulo_input = ui.input(
                label='Título *',
                value=link.get('titulo', ''),
                placeholder='Nome do link'
            ).classes('w-full').props('dense outlined')

            url_input = ui.input(
                label='URL *',
                value=link.get('url', ''),
                placeholder='https://...'
            ).classes('w-full').props('dense outlined')

            tipo_select = ui.select(
                options=LINK_TYPES,
                value=link.get('tipo', 'Google Drive'),
                label='Tipo'
            ).classes('w-full').props('dense outlined')

        ui.separator()

        # Botões
        with ui.row().classes('w-full justify-end gap-2 p-4'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def salvar():
                # Validação
                if not titulo_input.value or not titulo_input.value.strip():
                    ui.notify('Título é obrigatório.', type='negative')
                    return

                if not url_input.value or not url_input.value.strip():
                    ui.notify('URL é obrigatória.', type='negative')
                    return

                # Coleta dados
                novo_link = {
                    'titulo': titulo_input.value.strip(),
                    'url': url_input.value.strip(),
                    'tipo': tipo_select.value,
                }

                # Atualiza lista de links
                if 'links' not in caso:
                    caso['links'] = []

                if is_edicao:
                    caso['links'][index] = novo_link
                    msg = 'Link atualizado com sucesso!'
                else:
                    caso['links'].append(novo_link)
                    msg = 'Link adicionado com sucesso!'

                # Salva o caso
                _trigger_autosave(caso, caso_id)

                ui.notify(msg, type='positive')
                dialog.close()

                if refresh_func:
                    refresh_func.refresh()

            ui.button('Salvar', icon='save', on_click=salvar).props('color=primary')

    dialog.open()


def _confirmar_exclusao_link(caso: dict, caso_id: str, index: int, refresh_func=None):
    """Dialog de confirmação de exclusão de link."""
    links = caso.get('links', [])
    if index >= len(links):
        return

    link = links[index]
    titulo = link.get('titulo', 'Link')

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('warning', color='negative', size='32px')
            ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800')

        ui.label(f'Deseja excluir o link "{titulo}"?').classes('text-gray-600 mb-2')
        ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def executar():
                caso['links'].pop(index)
                _trigger_autosave(caso, caso_id)
                ui.notify('Link excluído com sucesso!', type='positive')
                dialog.close()
                if refresh_func:
                    refresh_func.refresh()

            ui.button('Excluir', on_click=executar).props('color=negative')

    dialog.open()
