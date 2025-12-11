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
        ui.label('Módulo em desenvolvimento').classes('text-xl text-gray-500 text-center mt-8')
        ui.label('Esta funcionalidade estará disponível em breve.').classes('text-sm text-gray-400 text-center mt-2')

