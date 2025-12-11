"""
inteligencia_page.py - Página de Inteligência.

Módulo de análises estratégicas e cenários de risco.
"""

from nicegui import ui
from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated
from .riscos_penais.dados_processos import PROCESSOS


@ui.page('/inteligencia')
def inteligencia():
    """Página principal do módulo Inteligência."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        # Calcular métricas
        total_crimes = sum(len(p.get('crimes', [])) for p in PROCESSOS)
        comarcas = set(p['comarca'] for p in PROCESSOS)
        
        with layout('Módulo de Inteligência', breadcrumbs=[('Inteligência', None)]):
            with ui.column().classes('w-full gap-6 p-6'):
                # Subtítulo
                ui.label('Análises estratégicas e cenários de risco').classes('text-gray-600 text-sm mb-4')
                
                # INDICADOR VISUAL ÚNICO - Se você vê isso, o código novo está rodando!
                ui.label('🟢 VERSÃO ATUALIZADA - Dashboard Completo').classes('text-xs text-green-600 font-bold mb-2').style('display: block;')
                
                # Card: Riscos Penais - Carlos
                def navegar_riscos_penais():
                    ui.navigate.to('/inteligencia/riscos-penais/carlos')
                
                with ui.card().classes('w-full cursor-pointer hover:shadow-lg transition-all duration-200 border-l-4').style('border-left-color: #dc2626;').on('click', navegar_riscos_penais):
                    with ui.row().classes('items-center gap-4 p-4'):
                        ui.icon('gavel', size='48px').classes('text-red-600')
                        with ui.column().classes('gap-2 flex-1'):
                            with ui.row().classes('items-center gap-3'):
                                ui.label('Riscos Penais - Carlos Schmidmeier').classes('text-xl font-bold text-gray-800')
                                with ui.badge('RISCO ALTO').classes('px-3 py-1').style('background-color: #dc2626; color: white; font-weight: bold;'):
                                    pass
                            
                            ui.label(f'{len(PROCESSOS)} processos criminais ativos • {total_crimes} crimes imputados').classes('text-sm text-gray-500')
                            
                            # Métricas rápidas
                            with ui.row().classes('items-center gap-3 mt-2 flex-wrap'):
                                ui.badge('Pena máx: 44 anos').classes('px-2 py-1 text-xs').style('background-color: #fee2e2; color: #991b1b;')
                                ui.badge('Pena realista: 7-18 anos').classes('px-2 py-1 text-xs').style('background-color: #fef3c7; color: #92400e;')
                                ui.badge(f'{len(comarcas)} comarcas').classes('px-2 py-1 text-xs').style('background-color: #e5e7eb; color: #374151;')
                        
                        ui.icon('chevron_right', size='24px').classes('text-gray-400')
        
    except Exception as e:
        print(f"Erro ao carregar página de Inteligência: {e}")
        import traceback
        traceback.print_exc()






