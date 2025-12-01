"""
acordos_page.py - Página de Acordos.
"""

from nicegui import ui
from ...core import layout
from ...auth import is_authenticated
from .modais import render_acordo_dialog


@ui.page('/acordos')
def acordos():
    """Página de Acordos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Criar dialog
    dialog, open_dialog = render_acordo_dialog()
    
    with layout('Acordos', breadcrumbs=[('Acordos', None)]):
        # Header com botão
        with ui.row().classes('w-full gap-4 mb-6'):
            ui.button('+ NOVO ACORDO', on_click=open_dialog).props(
                'color=primary'
            ).classes('font-bold')
        
        # Mensagem de desenvolvimento
        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
            ui.icon('construction', size='48px').classes('text-yellow-500 mb-4')
            ui.label('⚙️ Em Desenvolvimento').classes('text-2xl font-bold mb-2')
            ui.label(
                'O módulo de Acordos está sendo desenvolvido.'
            ).classes('text-gray-600 text-center')
