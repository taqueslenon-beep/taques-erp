"""
Página do módulo "Central de Comando" do workspace "Visão Geral do Escritório".
Estrutura de abas para organizar diferentes funcionalidades administrativas.
"""
from nicegui import ui
from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace


@ui.page('/visao-geral/central-comando')
def central_comando():
    """
    Página da Central de Comando do workspace "Visão Geral do Escritório".
    Estrutura de abas para organizar funcionalidades administrativas.
    """
    # Verifica autenticação
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Define workspace como "Visão Geral do Escritório"
    definir_workspace('visao_geral_escritorio')
    
    # Renderiza página com layout padrão
    with layout('Central de Comando', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Central de Comando', None)]):
        # Container principal
        with ui.column().classes('w-full gap-4'):
            # Abas principais do módulo
            with ui.tabs().classes('w-full').props('align=left no-caps') as main_tabs:
                processos_internos_tab = ui.tab('Processos Internos', icon='work')
                # TODO: Adicionar mais abas aqui no futuro
                # Exemplo: outras_abas_tab = ui.tab('Outras Funcionalidades', icon='settings')
            
            # Painéis das abas
            with ui.tab_panels(main_tabs, value=processos_internos_tab).classes('w-full bg-white p-4 rounded shadow-sm'):
                
                # ============================================
                # ABA: PROCESSOS INTERNOS
                # ============================================
                with ui.tab_panel(processos_internos_tab):
                    _render_aba_processos_internos()


def _render_aba_processos_internos():
    """
    Renderiza o conteúdo da aba "Processos Internos".
    Inclui cabeçalho, botão de cadastro e área para listagem futura.
    """
    # Container principal da aba
    with ui.column().classes('w-full gap-4'):
        # Cabeçalho da seção com botão de cadastro
        with ui.row().classes('w-full items-center justify-between'):
            # Título da seção
            ui.label('Processos Internos').classes('text-xl font-bold text-gray-800')
            
            # Botão de cadastro - destacado no canto superior direito
            ui.button(
                'Cadastrar Processo Interno',
                icon='add',
                on_click=_on_click_cadastrar_processo_interno
            ).props('unelevated').style(f'background-color: {PRIMARY_COLOR}; color: white;') \
             .classes('font-medium')
        
        # Separador visual
        ui.separator()
        
        # Área para futura listagem de processos internos
        with ui.column().classes('w-full mt-4'):
            # Placeholder - será substituído pela listagem futura
            with ui.card().classes('w-full p-8 text-center bg-gray-50'):
                ui.icon('inbox', size='xl').classes('text-gray-400 mb-4')
                ui.label('Nenhum processo interno cadastrado').classes('text-gray-500 text-sm')
                ui.label('Use o botão "Cadastrar Processo Interno" para adicionar novos processos.').classes('text-gray-400 text-xs mt-2')
            
            # TODO: Implementar listagem de processos internos aqui
            # Exemplo de estrutura futura:
            # - Tabela ou cards com processos internos
            # - Filtros e busca
            # - Ações (editar, excluir, visualizar)


def _on_click_cadastrar_processo_interno():
    """
    Handler para o clique no botão "Cadastrar Processo Interno".
    Por enquanto apenas exibe notificação de funcionalidade em desenvolvimento.
    """
    ui.notify('Funcionalidade em desenvolvimento', type='info')

