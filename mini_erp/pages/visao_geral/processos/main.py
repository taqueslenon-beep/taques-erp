"""
Página principal do módulo Processos do workspace Visão Geral.
Rota: /visao-geral/processos
Visualização em Cards responsivos.
"""
from nicegui import ui
from ....core import layout, PRIMARY_COLOR
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from ....firebase_config import ensure_firebase_initialized
from .database import listar_processos, excluir_processo, buscar_processo
from .processo_dialog import abrir_dialog_processo, confirmar_exclusao
from .models import (
    TIPOS_PROCESSO, STATUS_PROCESSO, RESULTADOS_PROCESSO,
    AREAS_PROCESSO, SISTEMAS_PROCESSUAIS, ESTADOS,
    obter_cor_status, obter_cor_resultado, obter_cor_area
)

# =============================================================================
# CSS CUSTOMIZADO PARA CARDS
# =============================================================================

PROCESSO_CARD_CSS = '''
<style>
.processo-card {
    transition: all 0.2s ease-in-out;
    border-radius: 12px;
    overflow: hidden;
}
.processo-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
.processo-titulo {
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.processo-badge {
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
            # Adiciona CSS customizado
            ui.add_head_html(PROCESSO_CARD_CSS)

            # Estado dos filtros
            filtros = {
                'busca': '',
                'area': None,
                'status': None,
                'tipo': None,
                'caso_id': None,
                'grupo_nome': None,
            }

            # Referência para o refreshable
            refresh_ref = {'func': None}

            # Container principal com card
            with ui.card().classes('w-full'):
                # Header
                with ui.row().classes('w-full justify-between items-center p-4'):
                    with ui.column().classes('gap-0'):
                        ui.label('Gerenciamento de processos do escritório').classes('text-sm text-gray-500 -mt-2 mb-2')

                    # Botão Novo Processo
                    def novo_processo():
                        abrir_dialog_processo(on_save=lambda: refresh_ref['func'].refresh())

                    ui.button('Novo Processo', icon='add', on_click=novo_processo).props('color=primary')

                ui.separator()

                # Container dos filtros
                with ui.element('div').classes('filtros-container mx-4 mt-4'):
                    with ui.row().classes('w-full items-end gap-4 flex-wrap'):
                        # Campo de busca
                        busca_input = ui.input(
                            label='Buscar',
                            placeholder='Título ou número do processo...'
                        ).classes('flex-1 min-w-48').props('dense outlined clearable')

                        # Filtro por área
                        area_select = ui.select(
                            options=['Todas'] + AREAS_PROCESSO,
                            value='Todas',
                            label='Área'
                        ).classes('w-40').props('dense outlined')

                        # Filtro por status
                        status_select = ui.select(
                            options=['Todos'] + STATUS_PROCESSO,
                            value='Todos',
                            label='Status'
                        ).classes('w-36').props('dense outlined')

                        # Filtro por tipo
                        tipo_select = ui.select(
                            options=['Todos'] + TIPOS_PROCESSO,
                            value='Todos',
                            label='Tipo'
                        ).classes('w-36').props('dense outlined')

                        # Botão limpar filtros
                        def limpar_filtros():
                            busca_input.value = ''
                            area_select.value = 'Todas'
                            status_select.value = 'Todos'
                            tipo_select.value = 'Todos'
                            filtros['busca'] = ''
                            filtros['area'] = None
                            filtros['status'] = None
                            filtros['tipo'] = None
                            filtros['caso_id'] = None
                            filtros['grupo_nome'] = None
                            if refresh_ref['func']:
                                refresh_ref['func'].refresh()

                        ui.button('Limpar', icon='clear', on_click=limpar_filtros).props('flat dense')

                        # Eventos de filtro
                        def aplicar_filtros():
                            filtros['busca'] = busca_input.value or ''
                            filtros['area'] = area_select.value if area_select.value != 'Todas' else None
                            filtros['status'] = status_select.value if status_select.value != 'Todos' else None
                            filtros['tipo'] = tipo_select.value if tipo_select.value != 'Todos' else None
                            if refresh_ref['func']:
                                refresh_ref['func'].refresh()

                        busca_input.on('update:model-value', lambda: aplicar_filtros())
                        area_select.on('update:model-value', lambda: aplicar_filtros())
                        status_select.on('update:model-value', lambda: aplicar_filtros())
                        tipo_select.on('update:model-value', lambda: aplicar_filtros())

                # Conteúdo principal (grid de cards)
                @ui.refreshable
                def renderizar_conteudo():
                    try:
                        _renderizar_grid_cards(filtros, refresh_ref)
                    except Exception as e:
                        print(f"[ERRO] Erro ao renderizar conteúdo: {e}")
                        import traceback
                        traceback.print_exc()
                        with ui.column().classes('w-full items-center py-8'):
                            ui.icon('error', size='48px', color='negative')
                            ui.label('Erro ao renderizar processos').classes('text-lg text-gray-600 mt-2')
                            ui.label(f'Erro: {str(e)}').classes('text-sm text-gray-400')

                # Guarda referência para uso posterior
                refresh_ref['func'] = renderizar_conteudo

                # Container para o conteúdo (usar column ao invés de element para melhor compatibilidade)
                with ui.column().classes('w-full p-4'):
                    try:
                        renderizar_conteudo()
                    except Exception as e:
                        print(f"[ERRO CRÍTICO] Erro na renderização inicial da página: {e}")
                        import traceback
                        traceback.print_exc()
                        ui.icon('error', size='48px', color='negative')
                        ui.label('Erro ao carregar página').classes('text-lg text-gray-600 mt-2')
                        ui.label(f'Erro: {str(e)}').classes('text-sm text-gray-400')
    except Exception as e:
        print(f"[ERRO CRÍTICO] Erro ao renderizar página de processos: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: renderiza uma página de erro básica
        try:
            with layout('Processos - Erro', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Processos', None)]):
                with ui.column().classes('w-full items-center py-16'):
                    ui.icon('error', size='64px', color='negative')
                    ui.label('Erro ao carregar página de processos').classes('text-xl font-bold text-gray-600 mt-4')
                    ui.label(f'Erro: {str(e)}').classes('text-gray-400 mt-2')
                    ui.button('Voltar ao Painel', icon='arrow_back', on_click=lambda: ui.navigate.to('/visao-geral/painel')).props('color=primary').classes('mt-4')
        except Exception as e2:
            print(f"[ERRO CRÍTICO] Erro ao renderizar página de erro: {e2}")

            # Conteúdo principal (grid de cards)
            @ui.refreshable
            def renderizar_conteudo():
                try:
                    _renderizar_grid_cards(filtros, refresh_ref)
                except Exception as e:
                    print(f"[ERRO] Erro ao renderizar conteúdo: {e}")
                    import traceback
                    traceback.print_exc()
                    with ui.column().classes('w-full items-center py-8'):
                        ui.icon('error', size='48px', color='negative')
                        ui.label('Erro ao renderizar processos').classes('text-lg text-gray-600 mt-2')
                        ui.label(f'Erro: {str(e)}').classes('text-sm text-gray-400')

            # Guarda referência para uso posterior
            refresh_ref['func'] = renderizar_conteudo

            # Container para o conteúdo (usar column ao invés de element para melhor compatibilidade)
            with ui.column().classes('w-full p-4'):
                try:
                    renderizar_conteudo()
                except Exception as e:
                    print(f"[ERRO CRÍTICO] Erro na renderização inicial da página: {e}")
                    import traceback
                    traceback.print_exc()
                    ui.icon('error', size='48px', color='negative')
                    ui.label('Erro ao carregar página').classes('text-lg text-gray-600 mt-2')
                    ui.label(f'Erro: {str(e)}').classes('text-sm text-gray-400')
    except Exception as e:
        print(f"[ERRO CRÍTICO] Erro ao renderizar página de processos: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: renderiza uma página de erro básica
        with layout('Processos - Erro', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Processos', None)]):
            with ui.column().classes('w-full items-center py-16'):
                ui.icon('error', size='64px', color='negative')
                ui.label('Erro ao carregar página de processos').classes('text-xl font-bold text-gray-600 mt-4')
                ui.label(f'Erro: {str(e)}').classes('text-gray-400 mt-2')
                ui.button('Voltar ao Painel', icon='arrow_back', on_click=lambda: ui.navigate.to('/visao-geral/painel')).props('color=primary').classes('mt-4')


def _renderizar_grid_cards(filtros: dict, refresh_ref: dict):
    """Renderiza o grid de cards de processos."""
    # Carrega processos
    try:
        todos_processos = listar_processos(filtros)
    except Exception as e:
        print(f"Erro ao carregar processos: {e}")
        import traceback
        traceback.print_exc()
        with ui.column().classes('w-full items-center py-8'):
            ui.icon('error', size='48px', color='negative')
            ui.label('Erro ao carregar processos').classes('text-lg text-gray-600 mt-2')
            ui.label('Tente recarregar a página.').classes('text-sm text-gray-400')
        return

    # Contador de resultados
    total = len(todos_processos)

    tem_filtros = (
        filtros['busca'] or
        filtros['area'] or
        filtros['status'] or
        filtros['tipo'] or
        filtros['caso_id'] or
        filtros['grupo_nome']
    )

    if tem_filtros:
        ui.label(f'{total} processo(s) encontrado(s)').classes('text-sm text-gray-500 mb-4')
    else:
        ui.label(f'{total} processo(s) cadastrado(s)').classes('text-sm text-gray-500 mb-4')

    # Estado vazio
    if not todos_processos:
        with ui.column().classes('w-full items-center py-12'):
            ui.icon('folder_open', size='64px').classes('text-gray-300')
            ui.label('Nenhum processo cadastrado').classes('text-lg text-gray-500 mt-4')
            ui.label('Clique em "Novo Processo" para começar.').classes('text-sm text-gray-400')
        return

    # Grid de cards responsivo (usar div com CSS Grid como na página de casos)
    with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'):
        for processo in todos_processos:
            _renderizar_card_processo(processo, refresh_ref)


def _renderizar_card_processo(processo: dict, refresh_ref: dict):
    """Renderiza um card de processo."""
    processo_id = processo.get('_id')
    titulo = processo.get('titulo', 'Sem título')
    numero = processo.get('numero', '')
    tipo = processo.get('tipo', '')
    status = processo.get('status', 'Ativo')
    area = processo.get('area', '')
    caso_titulo = processo.get('caso_titulo', '')
    clientes = processo.get('clientes_nomes', [])
    resultado = processo.get('resultado', 'Pendente')

    # Cores dos badges
    cor_status = obter_cor_status(status)
    cor_area = obter_cor_area(area)
    cor_resultado = obter_cor_resultado(resultado)

    with ui.card().classes('processo-card w-full'):
        # Header do card
        with ui.column().classes('w-full gap-2'):
            # Título
            ui.label(titulo).classes('processo-titulo text-base font-semibold text-gray-800')

            # Número e Tipo
            with ui.row().classes('w-full items-center gap-2 flex-wrap'):
                if numero:
                    ui.label(numero).classes('text-xs text-gray-500')
                if tipo:
                    ui.label(f'• {tipo}').classes('text-xs text-gray-500')

            # Badges: Status, Área, Resultado
            with ui.row().classes('w-full gap-2 flex-wrap items-center'):
                # Badge Status
                with ui.element('div').classes('processo-badge').style(
                    f'background-color: {cor_status["bg"]}; color: {cor_status["text"]};'
                ):
                    ui.label(status).classes('text-xs font-semibold')

                # Badge Área
                if area:
                    with ui.element('div').classes('processo-badge').style(
                        f'background-color: {cor_area["bg"]}; color: {cor_area["text"]}; border: 1px solid {cor_area["border"]};'
                    ):
                        ui.label(area).classes('text-xs font-semibold')

                # Badge Resultado
                if resultado and resultado != 'Pendente' and resultado != '-':
                    with ui.element('div').classes('processo-badge').style(
                        f'background-color: {cor_resultado["bg"]}; color: {cor_resultado["text"]};'
                    ):
                        ui.label(resultado).classes('text-xs font-semibold')

            # Caso vinculado
            if caso_titulo:
                with ui.row().classes('w-full items-center gap-1 mt-1'):
                    ui.icon('folder', size='14px').classes('text-gray-400')
                    ui.label(f'Caso: {caso_titulo}').classes('text-xs text-gray-600')

            # Clientes
            if clientes:
                with ui.row().classes('w-full items-center gap-1 mt-1'):
                    ui.icon('people', size='14px').classes('text-gray-400')
                    clientes_texto = ', '.join(clientes[:2])
                    if len(clientes) > 2:
                        clientes_texto += f' +{len(clientes) - 2}'
                    ui.label(clientes_texto).classes('text-xs text-gray-600')

            # Ações do card
            with ui.row().classes('w-full justify-end gap-2 mt-3 pt-3 border-t'):
                # Botão Editar
                def editar_processo():
                    processo_completo = buscar_processo(processo_id)
                    if processo_completo:
                        abrir_dialog_processo(
                            processo=processo_completo,
                            on_save=lambda: refresh_ref['func'].refresh()
                        )

                ui.button('Editar', icon='edit', on_click=editar_processo).props('flat dense size=sm')

                # Botão Excluir
                def excluir_processo_callback():
                    processo_completo = buscar_processo(processo_id)
                    if processo_completo:
                        def confirmar():
                            if excluir_processo(processo_id):
                                ui.notify('Processo excluído com sucesso!', type='positive')
                                refresh_ref['func'].refresh()
                            else:
                                ui.notify('Erro ao excluir processo.', type='negative')

                        confirmar_exclusao(processo_completo, on_confirm=confirmar)

                ui.button('Excluir', icon='delete', on_click=excluir_processo_callback).props('flat dense size=sm color=negative')
