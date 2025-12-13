"""
prazos.py - Página de Prazos (Placeholder)

Módulo para controle de prazos e datas importantes.
Atualmente em desenvolvimento.
"""
from nicegui import ui
from ..core import layout
from ..auth import is_authenticated


@ui.page('/prazos')
def prazos():
    """Página principal do módulo Prazos - placeholder em desenvolvimento."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        with layout('Prazos', breadcrumbs=[('Prazos', None)]):
            # Container centralizado com conteúdo placeholder
            with ui.column().classes('w-full h-full items-center justify-center gap-6 p-6'):
                # Ícone grande
                ui.icon('calendar_month', size='96px').classes('text-gray-400')
                
                # Título
                ui.label('Prazos').classes('text-4xl font-bold text-gray-700')
                
                # Mensagem secundária
                ui.label('Em desenvolvimento').classes('text-lg text-gray-500')
                
    except Exception as e:
        print(f"Erro na página Prazos: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f'Erro ao carregar página: {str(e)}', type='negative')


