# Módulo Cível
# Gestão de processos e ações cíveis

from nicegui import ui


def render_civil():
    """Renderiza a aba cível"""
    
    with ui.card().classes('w-full p-4'):
        ui.label('Processos Cíveis').classes('font-bold text-xl mb-2')
        ui.label('Gestão de processos e ações cíveis').classes('text-gray-500 text-sm mb-4')
        
        # Estatísticas
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Ações Ativas').classes('text-sm text-gray-500')
                ui.label('4').classes('text-2xl font-bold text-gray-800')
            
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Valor em Disputa').classes('text-sm text-gray-500')
                ui.label('R$ 1.2M').classes('text-2xl font-bold text-blue-600')
            
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Acordos Cíveis').classes('text-sm text-gray-500')
                ui.label('1').classes('text-2xl font-bold text-green-600')
        
        ui.label('Sistema de gestão cível em desenvolvimento...').classes('text-gray-400 italic')




