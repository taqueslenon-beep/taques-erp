"""
Módulo de Acordos/parcelamentos do workspace "Visão geral do escritório".
Exibe todos os acordos de todos os clientes do escritório.
"""
from nicegui import ui
from mini_erp.core import layout, PRIMARY_COLOR
from mini_erp.auth import is_authenticated
from mini_erp.middlewares.verificar_workspace import verificar_e_definir_workspace_automatico
from .modal_acordo import abrir_dialog_acordo


@ui.page('/visao-geral/acordos')
def acordos():
    """Página de Acordos/parcelamentos do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Verifica e define workspace automaticamente
    if not verificar_e_definir_workspace_automatico():
        return

    # Dialog de seleção de tipo
    with ui.dialog() as tipo_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Qual o tipo?').classes('text-xl font-bold mb-2')
        ui.label('Selecione o tipo de registro que deseja criar').classes('text-sm text-gray-600 mb-6')

        # Funções de callback para os cards
        def ao_selecionar_acordo():
            """Fecha dialog de tipo e abre formulário de acordo."""
            tipo_dialog.close()
            abrir_dialog_acordo()

        def ao_selecionar_parcelamento():
            """Fecha dialog de tipo e mostra notificação."""
            tipo_dialog.close()
            ui.notify('Formulário de Parcelamento em desenvolvimento', type='info')

        with ui.row().classes('w-full gap-4 mb-4 justify-center'):
            # Card 1 - Acordo
            with ui.card().classes('flex-1 p-6 cursor-pointer hover:bg-gray-100 transition-colors').on('click', ao_selecionar_acordo):
                with ui.column().classes('w-full items-center gap-3'):
                    ui.icon('handshake', size='48px').style(f'color: {PRIMARY_COLOR}')
                    ui.label('Acordo').classes('text-lg font-bold')
                    ui.label('Acordo judicial ou extrajudicial').classes('text-sm text-gray-600 text-center')

            # Card 2 - Parcelamento
            with ui.card().classes('flex-1 p-6 cursor-pointer hover:bg-gray-100 transition-colors').on('click', ao_selecionar_parcelamento):
                with ui.column().classes('w-full items-center gap-3'):
                    ui.icon('payments', size='48px').style(f'color: {PRIMARY_COLOR}')
                    ui.label('Parcelamento').classes('text-lg font-bold')
                    ui.label('Parcelamento de débitos ou tributos').classes('text-sm text-gray-600 text-center')

        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Cancelar', on_click=tipo_dialog.close).props('flat')

    with layout('Acordos/parcelamentos', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Acordos/parcelamentos', None)]):
        # Header com botão de novo acordo/parcelamento
        with ui.row().classes('w-full justify-end mb-6'):
            ui.button('Novo acordo/parcelamento', icon='add', on_click=tipo_dialog.open).props('color=primary').classes('font-bold')

        # Área de listagem (placeholder)
        with ui.column().classes('w-full items-center justify-center py-16'):
            ui.icon('folder_open', size='64px').classes('text-gray-400')
            ui.label('Nenhum acordo ou parcelamento cadastrado').classes('text-lg text-gray-500 mt-4')

