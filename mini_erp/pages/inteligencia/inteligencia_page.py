"""
inteligencia_page.py - Página de Inteligência.

Módulo em desenvolvimento - placeholder para funcionalidades futuras.
"""

from nicegui import ui
from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated


@ui.page('/inteligencia')
def inteligencia():
    """Página principal do módulo Inteligência."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        with layout('Inteligência', breadcrumbs=[('Inteligência', None)]):
            # Container centralizado
            with ui.column().classes('w-full items-center justify-center').style('min-height: 60vh; gap: 24px;'):
                # Ícone grande
                ui.label('🧠').classes('text-8xl mb-4')
                
                # Título
                ui.label('Em desenvolvimento').classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR};')
                
                # Mensagem
                ui.label('Este módulo está sendo desenvolvido e em breve estará disponível.').classes('text-lg text-gray-600 text-center max-w-md')
                
                # Ícone de construção (opcional)
                with ui.row().classes('items-center gap-2 mt-4'):
                    ui.icon('construction', size='md').classes('text-gray-400')
                    ui.label('Funcionalidades em breve').classes('text-sm text-gray-500')
        
    except Exception as e:
        print(f"Erro ao carregar página de Inteligência: {e}")
        import traceback
        traceback.print_exc()

