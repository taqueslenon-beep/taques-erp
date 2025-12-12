"""
Página principal do workspace "Visão geral do escritório".
Exibe o painel com visão consolidada de todos os casos e processos do escritório.
"""
from nicegui import ui, app
from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace
from .pessoas.database import listar_pessoas


@ui.page('/visao-geral/painel')
def painel():
    """Página principal do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace diretamente (sem middleware complexo)
    definir_workspace('visao_geral_escritorio')

    # Carregar dados de pessoas do workspace
    try:
        todas_pessoas = listar_pessoas()
        total_pessoas = len(todas_pessoas) if todas_pessoas else 0
        
        # Separar por tipo
        total_pf = sum(1 for p in todas_pessoas if p.get('tipo_pessoa') == 'PF')
        total_pj = sum(1 for p in todas_pessoas if p.get('tipo_pessoa') == 'PJ')
    except Exception:
        # Em caso de erro, mostra zeros
        total_pessoas = 0
        total_pf = 0
        total_pj = 0

    with layout('Painel', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Painel', None)]):
        # Cards de resumo
        with ui.row().classes('w-full gap-4 flex-wrap mb-6'):
            # Card Pessoas Cadastradas (funcional)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: {PRIMARY_COLOR}'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('people', size='24px').classes('text-gray-400')
                    ui.label('Pessoas Cadastradas').classes('text-sm text-gray-500')
                ui.label(str(total_pessoas)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR}')
                ui.label(f'{total_pf} PF, {total_pj} PJ').classes('text-xs text-gray-400 mt-1')
            
            # Card Processos Ativos (placeholder)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 border-gray-300'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('gavel', size='24px').classes('text-gray-300')
                    ui.label('Processos Ativos').classes('text-sm text-gray-500')
                ui.label('-').classes('text-3xl font-bold text-gray-300')
                ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')
            
            # Card Casos Abertos (placeholder)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 border-gray-300'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('folder', size='24px').classes('text-gray-300')
                    ui.label('Casos Abertos').classes('text-sm text-gray-500')
                ui.label('-').classes('text-3xl font-bold text-gray-300')
                ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')
            
            # Card Acordos (placeholder)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 border-gray-300'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('handshake', size='24px').classes('text-gray-300')
                    ui.label('Acordos').classes('text-sm text-gray-500')
                ui.label('-').classes('text-3xl font-bold text-gray-300')
                ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')
        
        # Seção em desenvolvimento
        with ui.card().classes('w-full p-6 mt-4'):
            with ui.row().classes('items-center justify-center gap-3'):
                ui.icon('construction', size='32px').classes('text-gray-400')
                ui.label('Mais visualizações em breve...').classes('text-gray-400 italic')



