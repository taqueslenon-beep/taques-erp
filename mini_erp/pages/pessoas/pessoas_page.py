"""
Página principal do módulo Pessoas.
Orquestra todos os componentes e gerencia a estrutura de tabs e dialogs.
"""
from nicegui import ui
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
    # Invalida cache na entrada para garantir dados frescos do Firebase
    invalidate_cache('clients')
    invalidate_cache('opposing_parties')
    
    with layout('Pessoas', breadcrumbs=[('Pessoas', None)]):
            # Tabs principais
            with ui.tabs().classes('w-full').props('no-caps') as tabs:
                clientes_tab = ui.tab('Clientes')
                partes_contrarias_tab = ui.tab('Outros Envolvidos')

            with ui.tab_panels(tabs, value=clientes_tab).classes('w-full bg-white p-4 rounded shadow-sm'):
                # ========== TAB: CLIENTES ==========
                with ui.tab_panel(clientes_tab):
                    # Sub-tabs para Clientes
                    with ui.tabs().classes('w-full').props('dense inline-label no-caps') as client_sub_tabs:
                        all_clients_tab = ui.tab('Todos os Clientes', icon='people')
                        bonds_map_tab = ui.tab('Mapeamento de Vínculos', icon='account_tree')

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
