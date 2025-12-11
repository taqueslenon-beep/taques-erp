"""
Página principal do Painel - Orquestrador.
Gerencia o layout, navegação entre abas e carregamento de dados.
"""
from nicegui import ui

from ...core import layout, get_cases_list, get_processes_list, get_clients_list, get_opposing_parties_list, PRIMARY_COLOR
from ...auth import is_authenticated

from .models import TAB_CONFIG, TAB_STYLES
from .data_service import create_data_service
from .tab_visualizations import (
    render_tab_totais,
    render_tab_comparativo,
    render_tab_categoria,
    render_tab_temporal,
    render_tab_status,
    render_tab_resultado,
    render_tab_cliente,
    render_tab_parte,
    render_tab_area,
    render_tab_area_ha,
    render_tab_estado,
    render_tab_heatmap,
    render_tab_probabilidade,
    render_tab_financeiro,
)


@ui.page('/')
def painel():
    """Página principal do Painel de Visualizações."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        # Define workspace atual na sessão (workspace padrão)
        from ...gerenciadores.gerenciador_workspace import definir_workspace
        definir_workspace('area_cliente_schmidmeier')
        
        # ==========================================================================
        # OTIMIZAÇÃO: Carrega todos os dados UMA ÚNICA VEZ no início
        # ==========================================================================
        ds = create_data_service(
            get_cases_list,
            get_processes_list,
            get_clients_list,
            get_opposing_parties_list,
        )
        
        with layout('Painel', breadcrumbs=[('Painel', None)]):
            ui.label('Visão consolidada dos dados do sistema. Informações atualizadas em tempo real.').classes('text-gray-500 text-sm mb-4 -mt-4')
            
            # Estilo para abas minimalistas
            ui.add_head_html(TAB_STYLES)
            
            # Estado para controlar a aba ativa
            active_tab = {'value': 'totais'}
            
            # Layout vertical: menu lateral esquerdo + conteúdo à direita
            with ui.row().classes('w-full gap-4 items-start'):
                # Menu vertical à esquerda
                with ui.column().classes('w-64 min-w-64 bg-white rounded shadow-sm p-2 sticky top-4'):
                    ui.label('Visualizações').classes('text-sm font-semibold text-gray-700 mb-2 px-2')
                    
                    def set_active_tab(tab_name: str):
                        active_tab['value'] = tab_name
                        menu_buttons.refresh()
                        content_area.refresh()
                    
                    @ui.refreshable
                    def menu_buttons():
                        for tab_id, tab_label, tab_icon in TAB_CONFIG:
                            is_active = active_tab['value'] == tab_id
                            
                            def make_click_handler(tid):
                                return lambda: set_active_tab(tid)
                            
                            btn = ui.button(tab_label, icon=tab_icon, on_click=make_click_handler(tab_id))
                            props_str = ('unelevated' if is_active else 'flat') + ' ' + ('color=primary' if is_active else 'color=grey-7') + ' align=left'
                            btn.props(props_str)
                            btn.classes('w-full justify-start text-left px-3 py-2 mb-1')
                            if is_active:
                                btn.style('background-color: #e3f2fd; font-weight: 600;')
                    
                    menu_buttons()
                
                # Área de conteúdo à direita
                with ui.column().classes('flex-1 min-w-0'):
                    @ui.refreshable
                    def content_area():
                        current_tab = active_tab['value']
                        
                        # Callback para refresh quando resultado muda
                        def on_result_change():
                            # Recarrega dados e atualiza a view
                            nonlocal ds
                            ds = create_data_service(
                                get_cases_list,
                                get_processes_list,
                                get_clients_list,
                                get_opposing_parties_list,
                            )
                            content_area.refresh()
                        
                        # Mapeia cada aba para sua função de renderização
                        tab_renderers = {
                            'totais': lambda: render_tab_totais(ds, PRIMARY_COLOR),
                            'comparativo': lambda: render_tab_comparativo(ds),
                            'categoria': lambda: render_tab_categoria(ds),
                            'temporal': lambda: render_tab_temporal(ds),
                            'status': lambda: render_tab_status(ds),
                            'resultado': lambda: render_tab_resultado(ds, on_result_change),
                            'cliente': lambda: render_tab_cliente(ds, PRIMARY_COLOR),
                            'parte': lambda: render_tab_parte(ds),
                            'area': lambda: render_tab_area(ds),
                            'area_ha': lambda: render_tab_area_ha(),
                            'estado': lambda: render_tab_estado(ds),
                            'heatmap': lambda: render_tab_heatmap(ds),
                            'probabilidade': lambda: render_tab_probabilidade(ds),
                            'financeiro': lambda: render_tab_financeiro(ds),
                        }
                        
                        # Executa o renderer da aba atual
                        renderer = tab_renderers.get(current_tab)
                        if renderer:
                            renderer()
                    
                    content_area()
    except Exception as e:
        print(f"Erro na página Painel: {e}")
        import traceback
        traceback.print_exc()
        # Não redireciona para login automaticamente - apenas loga o erro
        ui.notify(f'Erro ao carregar página: {str(e)}', type='negative')


