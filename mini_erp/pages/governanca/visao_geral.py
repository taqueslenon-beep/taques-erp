# Módulo de Visão Geral
# Dashboard, matriz de responsabilidades e riscos

from nicegui import ui
from ...core import PRIMARY_COLOR


def render_visao_geral():
    """Renderiza a aba de visão geral com sub-abas"""
    
    # Sub-abas da Visão Geral - estilo mais discreto e hierárquico
    with ui.tabs().classes('w-full bg-gray-50 rounded-lg p-1').props('dense inline-label no-caps align=left indicator-color="' + PRIMARY_COLOR + '"') as overview_tabs:
        dashboard_tab = ui.tab('Dashboard', icon='analytics').classes('text-sm text-gray-600')
        matriz_tab = ui.tab('Matriz de Responsabilidades', icon='grid_view').classes('text-sm text-gray-600')
        riscos_tab = ui.tab('Riscos e Alertas', icon='warning').classes('text-sm text-gray-600')
    
    with ui.tab_panels(overview_tabs, value=dashboard_tab).classes('w-full mt-3 bg-white rounded-lg border border-gray-100 p-4'):
        # Dashboard
        with ui.tab_panel(dashboard_tab):
            _render_dashboard()
        
        # Matriz de Responsabilidades
        with ui.tab_panel(matriz_tab):
            _render_matriz()
        
        # Riscos e Alertas
        with ui.tab_panel(riscos_tab):
            _render_riscos()


def _render_dashboard():
    """Renderiza o dashboard com cards de resumo"""
    # Cards de resumo
    with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
        with ui.card().classes('flex-1 min-w-48 p-4'):
            ui.label('Total de Processos').classes('text-sm text-gray-500')
            ui.label('12').classes('text-2xl font-bold text-gray-800')
            ui.label('3 criminais, 5 administrativos, 4 cíveis').classes('text-xs text-gray-500')
        
        with ui.card().classes('flex-1 min-w-48 p-4'):
            ui.label('Condenações Ativas').classes('text-sm text-gray-500')
            ui.label('2').classes('text-2xl font-bold text-orange-600')
            ui.label('Em cumprimento').classes('text-xs text-gray-500')
        
        with ui.card().classes('flex-1 min-w-48 p-4'):
            ui.label('Benefícios Penais').classes('text-sm text-gray-500')
            ui.label('5').classes('text-2xl font-bold').style(f'color: {PRIMARY_COLOR}')
            ui.label('3 deferidos, 2 em análise').classes('text-xs text-gray-500')
        
        with ui.card().classes('flex-1 min-w-48 p-4'):
            ui.label('Alertas Ativos').classes('text-sm text-gray-500')
            ui.label('8').classes('text-2xl font-bold text-red-600')
            ui.label('Requerem atenção').classes('text-xs text-gray-500')
    
    # Gráficos e análises
    with ui.card().classes('w-full p-4'):
        ui.label('Análises e Gráficos').classes('font-bold text-lg mb-3')
        ui.label('Visualizações em desenvolvimento...').classes('text-gray-400 italic')


def _render_matriz():
    """Renderiza a matriz de responsabilidades"""
    with ui.card().classes('w-full'):
        ui.label('Matriz de Responsabilidades').classes('font-bold text-lg mb-3')
        ui.label('Mapeamento de responsáveis e suas obrigações em desenvolvimento...').classes('text-gray-400 italic')


def _render_riscos():
    """Renderiza a seção de riscos e alertas"""
    with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
        with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
            ui.label('Risco Geral').classes('text-sm text-gray-500')
            ui.label('Médio').classes('text-xl font-bold text-orange-600')
            ui.linear_progress(value=0.5, color='orange').classes('mt-2')
        
        with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
            ui.label('Processos Potenciais').classes('text-sm text-gray-500')
            ui.label('3').classes('text-xl font-bold text-gray-800')
        
        with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
            ui.label('Alertas Críticos').classes('text-sm text-gray-500')
            ui.label('1').classes('text-xl font-bold text-red-600')
    
    with ui.card().classes('w-full'):
        ui.label('Detalhamento de Riscos e Alertas').classes('font-bold text-lg mb-3')
        ui.label('Sistema de alertas em desenvolvimento...').classes('text-gray-400 italic')

