"""
Página principal do workspace "Visão geral do escritório".
Exibe o painel com visão consolidada de todos os casos e processos do escritório.
"""
from nicegui import ui, app
from ...core import layout
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace


@ui.page('/visao-geral/painel')
def painel():
    """Página principal do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace diretamente (sem middleware complexo)
    definir_workspace('visao_geral_escritorio')

    with layout('Painel', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Painel', None)]):
        with ui.column().classes('w-full items-center justify-center py-16'):
            ui.icon('construction', size='64px').classes('text-gray-400')
            ui.label('Módulo em desenvolvimento').classes('text-xl font-bold text-gray-500 mt-4')
            ui.label('Este módulo estará disponível em breve.').classes('text-gray-400')



