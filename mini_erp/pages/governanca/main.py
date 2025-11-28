# Página Principal de Governança
# Orquestra todas as abas e submódulos

from nicegui import ui
from ...core import layout, PRIMARY_COLOR

# Estilo customizado para tabs secundárias
SUBTABS_STYLE = '''
    <style>
        /* Deixa as sub-tabs mais discretas */
        .q-tabs--dense .q-tab {
            min-height: 36px !important;
            padding: 0 12px !important;
        }
        
        /* Cor mais suave para tabs não selecionadas */
        .bg-gray-50 .q-tab:not(.q-tab--active) {
            opacity: 0.7;
        }
        
        /* Hover suave nas tabs */
        .bg-gray-50 .q-tab:hover {
            background-color: rgba(0, 0, 0, 0.03);
            border-radius: 6px;
        }
        
        /* Tab ativa com destaque suave - usa a cor primária do sistema */
        .bg-gray-50 .q-tab--active {
            font-weight: 500;
            color: ''' + PRIMARY_COLOR + ''' !important;
        }
        
        /* Indicador com a cor primária do sistema */
        .q-tabs__indicator {
            background-color: ''' + PRIMARY_COLOR + ''' !important;
        }
    </style>
'''

# Importa os submódulos
from .visao_geral import render_visao_geral
from .criminal import (
    render_cenario_criminal,
    render_beneficios_penais,
    render_condenacoes_criminais,
    render_cumprimento_penas,
)
from .administrativa import render_administrativa
from .civil import render_civil
from .tributaria import render_tributaria


@ui.page('/governanca')
def governanca():
    """Página principal do módulo de Governança"""
    
    with layout('', breadcrumbs=[('Governança', None)]):
        # Adiciona estilos customizados para as sub-tabs
        ui.add_head_html(SUBTABS_STYLE)
        
        # Título + Sobre este módulo na mesma linha
        with ui.row().classes('w-full items-center gap-2 mb-6 flex-nowrap'):
            ui.label('Governança').classes('text-2xl font-bold text-gray-800 shrink-0')
            with ui.expansion('ℹ️ Sobre este módulo').classes('text-sm text-gray-500 shrink').props('dense header-class="text-gray-500 py-0"'):
                ui.markdown('''
A **governança de riscos** transforma a gestão jurídica em controle executivo, focando na proteção da continuidade do negócio e blindagem dos tomadores de decisão.

Consolidamos a **Matriz de Responsabilidade** (CPFs/CNPJs × obrigações criminais, administrativas e financeiras) para monitorar exposição real, garantir elegibilidade a benefícios e antecipar impactos na operação ou crédito.
''').classes('text-gray-600 text-sm')

        # Abas principais do módulo de Governança
        with ui.tabs().classes('w-full').props('align=left no-caps') as main_tabs:
            visao_geral_tab = ui.tab('Visão Geral', icon='dashboard')
            criminal_tab = ui.tab('Criminal', icon='gavel')
            administrativa_tab = ui.tab('Administrativa', icon='description')
            civil_tab = ui.tab('Cível', icon='balance')
            tributaria_tab = ui.tab('Tributária', icon='receipt')
        
        with ui.tab_panels(main_tabs, value=visao_geral_tab).classes('w-full bg-white p-4 rounded shadow-sm'):
            
            # ============================================
            # VISÃO GERAL
            # ============================================
            with ui.tab_panel(visao_geral_tab):
                render_visao_geral()
            
            # ============================================
            # CRIMINAL
            # ============================================
            with ui.tab_panel(criminal_tab):
                _render_criminal_tab()
            
            # ============================================
            # ADMINISTRATIVA
            # ============================================
            with ui.tab_panel(administrativa_tab):
                render_administrativa()
            
            # ============================================
            # CÍVEL
            # ============================================
            with ui.tab_panel(civil_tab):
                render_civil()
            
            # ============================================
            # TRIBUTÁRIA
            # ============================================
            with ui.tab_panel(tributaria_tab):
                render_tributaria()


def _render_criminal_tab():
    """Renderiza a aba criminal com suas sub-abas"""
    
    # Sub-abas Criminal - estilo mais discreto e hierárquico
    with ui.tabs().classes('w-full bg-gray-50 rounded-lg p-1').props('dense inline-label no-caps align=left indicator-color="' + PRIMARY_COLOR + '"') as criminal_tabs:
        cenario_crim_tab = ui.tab('Cenário Criminal', icon='insights').classes('text-sm text-gray-600')
        ben_penais_tab = ui.tab('Benefícios Penais', icon='verified').classes('text-sm text-gray-600')
        condenacoes_crim_tab = ui.tab('Condenações', icon='gavel').classes('text-sm text-gray-600')
        cumprimento_penas_tab = ui.tab('Cumprimento de Penas', icon='traffic').classes('text-sm text-gray-600')
    
    with ui.tab_panels(criminal_tabs, value=cenario_crim_tab).classes('w-full mt-3 bg-white rounded-lg border border-gray-100 p-4'):
        
        # --- CENÁRIO CRIMINAL ---
        with ui.tab_panel(cenario_crim_tab):
            render_cenario_criminal()
        
        # --- BENEFÍCIOS PENAIS ---
        with ui.tab_panel(ben_penais_tab):
            render_beneficios_penais()
        
        # --- CONDENAÇÕES CRIMINAIS ---
        with ui.tab_panel(condenacoes_crim_tab):
            render_condenacoes_criminais()
        
        # --- CUMPRIMENTO DE PENAS ---
        with ui.tab_panel(cumprimento_penas_tab):
            render_cumprimento_penas()

