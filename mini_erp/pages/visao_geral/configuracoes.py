"""
Módulo de Configurações do workspace "Visão geral do escritório".
Redireciona para página de configurações principal.
"""
from nicegui import ui
from ...auth import is_authenticated


@ui.page('/visao-geral/configuracoes')
def configuracoes():
    """Página de Configurações do workspace Visão geral do escritório."""
    # Verifica autenticação
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Redireciona para página de configurações principal
    # (mesma funcionalidade para todos os workspaces)
    ui.navigate.to('/configuracoes')



