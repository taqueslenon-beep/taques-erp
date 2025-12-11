"""
Módulo de Acordos do workspace "Visão geral do escritório".
Exibe todos os acordos de todos os clientes do escritório.
"""
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated
from ...middlewares.verificar_workspace import verificar_e_definir_workspace_automatico


@ui.page('/visao-geral/acordos')
def acordos():
    """Página de Acordos do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Verifica e define workspace automaticamente
    if not verificar_e_definir_workspace_automatico():
        return

    with layout('Acordos', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Acordos', None)]):
        ui.label('Módulo em desenvolvimento').classes('text-xl text-gray-500 text-center mt-8')
        ui.label('Esta funcionalidade estará disponível em breve.').classes('text-sm text-gray-400 text-center mt-2')

