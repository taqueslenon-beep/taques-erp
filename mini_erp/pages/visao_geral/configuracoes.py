"""
Módulo de Configurações do workspace "Visão geral do escritório".
Configurações específicas do workspace.
"""
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated
from ...middlewares.verificar_workspace import verificar_e_definir_workspace_automatico


@ui.page('/visao-geral/configuracoes')
def configuracoes():
    """Página de Configurações do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Verifica e define workspace automaticamente
    if not verificar_e_definir_workspace_automatico():
        return

    with layout('Configurações', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Configurações', None)]):
        with ui.column().classes('w-full items-center justify-center py-16'):
            ui.icon('construction', size='64px').classes('text-gray-400')
            ui.label('Módulo em desenvolvimento').classes('text-xl font-bold text-gray-500 mt-4')
            ui.label('Este módulo estará disponível em breve.').classes('text-gray-400')



