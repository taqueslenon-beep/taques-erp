"""
Página principal do módulo Pessoas.
Orquestra todos os componentes e gerencia a estrutura de tabs e dialogs.
"""
from nicegui import ui
from concurrent.futures import ThreadPoolExecutor, as_completed
from ...core import layout
from ...auth import is_authenticated
from .database import delete_client, delete_opposing_party, invalidate_cache, get_clients_list, get_opposing_parties_list
from .ui_dialogs import (
    create_new_client_dialog, create_edit_client_dialog,
    create_new_opposing_dialog, create_edit_opposing_dialog,
    create_add_bond_dialog
)
from .ui_tables import render_clients_table, render_opposing_table, render_bonds_map


@ui.page('/pessoas')
def pessoas():
    """Página principal de Pessoas - gerencia clientes e outros envolvidos."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        _render_pessoas_content()
    except Exception as e:
        print(f"Erro na página Pessoas: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f'Erro ao carregar página: {str(e)}', type='negative')


def _render_pessoas_content():
    """Conteúdo principal da página Pessoas."""
    # Cache de 15 minutos será utilizado se válido
    # Invalidação ocorre apenas após operações de escrita (salvar/deletar)
    # Isso evita recarregamento desnecessário do Firestore a cada navegação
    
    # Gera breadcrumb padronizado com workspace
    from ...componentes.breadcrumb_helper import gerar_breadcrumbs
    breadcrumbs = gerar_breadcrumbs('Pessoas', url_modulo='/pessoas')
    
    with layout('Pessoas', breadcrumbs=breadcrumbs):
        # === Indicador de Loading ===
        loading_row = ui.row().classes('w-full justify-center py-8')
        with loading_row:
            ui.spinner('dots', size='lg', color='primary')
            ui.label('Carregando pessoas...').classes('ml-3 text-gray-500')
        
        # Carregamento PARALELO para reduzir tempo de espera e pré-aquecer cache
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(get_clients_list): 'clients',
                executor.submit(get_opposing_parties_list): 'opposing',
            }
            
            _data = {}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    _data[key] = future.result()
                except Exception as e:
                    print(f"[PESSOAS] Erro ao carregar {key}: {e}")
                    _data[key] = []
        
        # Esconde loading após carregar dados
        loading_row.set_visibility(False)
        # === Fim Loading ===
        # Estilos CSS para hierarquia visual
        ui.add_head_html('''
        <style>
        .main-tabs .q-tab {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #1f2937 !important;
            margin-right: 2rem !important;
        }
        
        .sub-tabs-container {
            margin-left: 30px !important;
            border-left: 3px solid #e5e7eb !important;
            padding-left: 20px !important;
            margin-top: 8px !important;
            margin-bottom: 16px !important;
        }
        
        .sub-tabs .q-tab {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            color: #6b7280 !important;
            background-color: #f9fafb !important;
            border-radius: 6px !important;
            margin-right: 1rem !important;
            padding: 8px 16px !important;
            border: 1px solid #e5e7eb !important;
        }
        
        .sub-tabs .q-tab--active {
            background-color: #3b82f6 !important;
            color: white !important;
            border-color: #3b82f6 !important;
        }
        
        .sub-tabs .q-tab:hover {
            background-color: #e5e7eb !important;
            color: #374151 !important;
        }
        
        .sub-tabs .q-tab--active:hover {
            background-color: #2563eb !important;
            color: white !important;
        }
        
        .hierarchy-transition {
            transition: all 0.3s ease-in-out !important;
        }
        
        /* Responsividade para telas menores */
        @media (max-width: 768px) {
            .sub-tabs-container {
                margin-left: 15px !important;
                padding-left: 10px !important;
            }
            
            .main-tabs .q-tab {
                font-size: 1rem !important;
                margin-right: 1rem !important;
            }
            
            .sub-tabs .q-tab {
                font-size: 0.8rem !important;
                padding: 6px 12px !important;
                margin-right: 0.5rem !important;
            }
        }
        
        @media (max-width: 480px) {
            .sub-tabs-container {
                margin-left: 10px !important;
                padding-left: 8px !important;
            }
            
            .main-tabs .q-tab {
                font-size: 0.9rem !important;
                margin-right: 0.5rem !important;
            }
            
            .sub-tabs .q-tab {
                font-size: 0.75rem !important;
                padding: 4px 8px !important;
                margin-right: 0.25rem !important;
            }
        }
        </style>
        ''')
        
        # Container principal com layout hierárquico
        with ui.column().classes('w-full gap-0'):
            # Abas principais - alinhadas à esquerda
            with ui.tabs().classes('w-full justify-start main-tabs').props('no-caps align=left') as main_tabs:
                clientes_tab = ui.tab('Clientes')
                partes_contrarias_tab = ui.tab('Outros Envolvidos')

            # Container para sub-abas (inicialmente visível para Clientes)
            sub_tabs_container = ui.element('div').classes('w-full sub-tabs-container hierarchy-transition')
            
            with sub_tabs_container:
                # Sub-abas de Clientes - indentadas e subordinadas
                with ui.tabs().classes('w-full justify-start sub-tabs').props('dense inline-label no-caps align=left') as client_sub_tabs:
                    all_clients_tab = ui.tab('Todos os Clientes', icon='people')
                    bonds_map_tab = ui.tab('Mapeamento de Vínculos', icon='account_tree')
            
            # Função para controlar visibilidade das sub-abas com transição suave
            def toggle_subtabs():
                if main_tabs.value == clientes_tab:
                    sub_tabs_container.set_visibility(True)
                    # Adiciona classe de animação de entrada
                    sub_tabs_container.classes('opacity-100 transform translate-y-0')
                else:
                    # Adiciona classe de animação de saída antes de ocultar
                    sub_tabs_container.classes('opacity-0 transform -translate-y-2')
                    ui.timer(0.3, lambda: sub_tabs_container.set_visibility(False), once=True)
            
            # Conecta evento de mudança de aba principal
            main_tabs.on('update:model-value', lambda: toggle_subtabs())
            
            # Inicializa estado correto das sub-abas
            toggle_subtabs()

            # Painel de conteúdo
            with ui.tab_panels(main_tabs, value=clientes_tab).classes('w-full bg-white p-4 rounded shadow-sm'):
                # ========== TAB: CLIENTES ==========
                with ui.tab_panel(clientes_tab):

                    with ui.tab_panels(client_sub_tabs, value=all_clients_tab).classes('w-full mt-2'):
                        # ========== SUB-TAB: TODOS OS CLIENTES ==========
                        with ui.tab_panel(all_clients_tab):
                            # Dialogs de cliente
                            @ui.refreshable
                            def render_clients_table_refreshable():
                                render_clients_table(
                                    on_edit=lambda client: open_edit_client(client),
                                    on_delete=lambda client: remove_client(client)
                                )

                            @ui.refreshable
                            def render_bonds_map_refreshable():
                                render_bonds_map(
                                    on_add_bond=lambda idx: open_add_bond(idx),
                                    on_remove_bond=lambda ci, bi: remove_bond(ci, bi)
                                )

                            new_client_dialog = create_new_client_dialog(
                                render_clients_table_refreshable,
                                render_bonds_map_refreshable
                            )

                            edit_client_dialog, open_edit_client = create_edit_client_dialog(
                                render_clients_table_refreshable,
                                render_bonds_map_refreshable
                            )

                            def remove_client(client):
                                delete_client(client)
                                invalidate_cache('clients')
                                render_clients_table_refreshable.refresh()
                                render_bonds_map_refreshable.refresh()
                                ui.notify('Cliente removido!')

                            with ui.row().classes('w-full justify-end items-center mb-2'):
                                ui.button('Novo Cliente', icon='add', on_click=new_client_dialog.open).props('flat dense color=primary')

                            render_clients_table_refreshable()

                        # ========== SUB-TAB: MAPEAMENTO DE VÍNCULOS ==========
                        with ui.tab_panel(bonds_map_tab):
                            @ui.refreshable
                            def render_bonds_map_refreshable_tab():
                                render_bonds_map(
                                    on_add_bond=lambda idx: open_add_bond(idx),
                                    on_remove_bond=lambda ci, bi: remove_bond(ci, bi)
                                )

                            add_bond_dialog, open_add_bond, remove_bond = create_add_bond_dialog(
                                render_bonds_map_refreshable_tab
                            )

                            render_bonds_map_refreshable_tab()

                # ========== TAB: OUTROS ENVOLVIDOS ==========
                with ui.tab_panel(partes_contrarias_tab):
                    @ui.refreshable
                    def render_opposing_table_refreshable():
                        render_opposing_table(
                            on_edit=lambda opposing: open_edit_opposing(opposing),
                            on_delete=lambda opposing: remove_opposing(opposing)
                        )

                    new_opposing_dialog = create_new_opposing_dialog(
                        render_opposing_table_refreshable
                    )

                    edit_opposing_dialog, open_edit_opposing = create_edit_opposing_dialog(
                        render_opposing_table_refreshable
                    )

                    def remove_opposing(opposing):
                        delete_opposing_party(opposing)
                        invalidate_cache('opposing_parties')
                        render_opposing_table_refreshable.refresh()
                        ui.notify('Outro envolvido removido!')

                    with ui.row().classes('w-full justify-end items-center mb-2'):
                        ui.button('Novo Envolvido', icon='add', on_click=new_opposing_dialog.open).props('flat dense color=primary')

                    render_opposing_table_refreshable()
