# Módulo de Cumprimento de Penas
# Gestão e acompanhamento de cumprimento de penas

from nicegui import ui


def render_cumprimento_penas():
    """Renderiza a aba de cumprimento de penas com cards de semáforo"""
    
    # Cards de semáforo
    with ui.row().classes('w-full gap-4 flex-wrap'):
        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4 border-green-500 bg-green-50'):
            with ui.row().classes('items-center gap-2 mb-2'):
                ui.icon('check_circle', color='green', size='md')
                ui.label('Em Dia').classes('font-bold text-green-700')
            ui.label('3 pessoas/empresas').classes('text-2xl font-bold text-green-800')
            ui.label('Cumprindo penas regularmente').classes('text-sm text-green-600')
        
        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4 border-amber-500 bg-amber-50'):
            with ui.row().classes('items-center gap-2 mb-2'):
                ui.icon('warning', color='orange', size='md')
                ui.label('Atenção').classes('font-bold text-amber-700')
            ui.label('1 pessoa/empresa').classes('text-2xl font-bold text-amber-800')
            ui.label('Próximo de vencer prazo').classes('text-sm text-amber-600')
        
        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4 border-red-500 bg-red-50'):
            with ui.row().classes('items-center gap-2 mb-2'):
                ui.icon('error', color='red', size='md')
                ui.label('Irregular').classes('font-bold text-red-700')
            ui.label('0 pessoas/empresas').classes('text-2xl font-bold text-red-800')
            ui.label('Requer ação imediata').classes('text-sm text-red-600')
    
    with ui.card().classes('w-full mt-4'):
        ui.label('Detalhamento de Cumprimento de Penas').classes('font-bold text-lg mb-3')
        ui.label('Sistema de acompanhamento em desenvolvimento...').classes('text-gray-400 italic')




