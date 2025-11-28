# Módulo Tributária
# Gestão de processos e obrigações tributárias

from nicegui import ui


def render_tributaria():
    """Renderiza a aba tributária"""
    
    with ui.card().classes('w-full p-4'):
        ui.label('Questões Tributárias').classes('font-bold text-xl mb-2')
        ui.label('Gestão de processos e obrigações tributárias').classes('text-gray-500 text-sm mb-4')
        
        # Estatísticas
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Processos Tributários').classes('text-sm text-gray-500')
                ui.label('2').classes('text-2xl font-bold text-gray-800')
            
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Débitos Ativos').classes('text-sm text-gray-500')
                ui.label('R$ 450K').classes('text-2xl font-bold text-red-600')
            
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Parcelamentos').classes('text-sm text-gray-500')
                ui.label('1').classes('text-2xl font-bold text-blue-600')
        
        ui.label('Sistema de gestão tributária em desenvolvimento...').classes('text-gray-400 italic')




