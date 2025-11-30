"""
acordos_page.py - Página principal do módulo de Acordos.

Visualização de tabela de acordos seguindo padrão visual do módulo Processos.
"""

from nicegui import ui
from ...core import layout, invalidate_cache
from ...auth import is_authenticated
from .database import listar_acordos, buscar_acordos, buscar_acordo_por_id
from .ui_components import header_acordos, filtros_acordos, tabela_acordos
from .acordo_dialog import render_acordo_dialog
from .acordo_edit_dialog import render_acordo_edit_dialog


@ui.page('/acordos')
def acordos():
    """Página principal de Acordos."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        _render_acordos_content()
    except Exception as e:
        print(f"Erro na página Acordos: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f'Erro ao carregar página: {str(e)}', type='negative')


def _render_acordos_content():
    """Conteúdo principal da página Acordos."""
    with layout('Acordos', breadcrumbs=[('Acordos', None)]):
        # Estado dos filtros e busca
        search_term = {'value': ''}
        filter_status = {'value': ''}
        
        # Referência para render_table (será definida depois)
        render_table_ref = {'func': None}
        
        # Função para atualizar tabela
        def refresh_table():
            if render_table_ref['func']:
                render_table_ref['func'].refresh()
        
        # Função para extrair opções únicas dos dados
        def get_filter_options():
            all_rows = listar_acordos()
            return {
                'status': [''] + sorted(set([r.get('status', '') for r in all_rows if r.get('status')]))
            }
        
        # Criar dialog de novo acordo
        def on_success_callback():
            """Callback executado após salvar acordo com sucesso."""
            invalidate_cache('agreements')
            refresh_table()
        
        acordo_dialog, open_acordo_dialog = render_acordo_dialog(on_success=on_success_callback)
        acordo_edit_dialog, open_acordo_edit_dialog = render_acordo_edit_dialog(on_success=on_success_callback)
        
        # Função de callback para novo acordo
        def on_novo_acordo():
            """Callback para criar novo acordo - abre o dialog."""
            open_acordo_dialog()
        
        # Função para abrir modal de edição
        def open_edit_dialog(acordo_id: str):
            """Abre modal de edição com dados do acordo."""
            acordo = buscar_acordo_por_id(acordo_id)
            if acordo:
                open_acordo_edit_dialog(acordo)
            else:
                ui.notify('Acordo não encontrado!', type='negative')
        
        # Barra superior: pesquisa + botão novo acordo
        search_input = header_acordos(on_novo_acordo=on_novo_acordo)
        
        # Callback para atualizar pesquisa quando valor mudar
        def on_search_change():
            search_term['value'] = search_input.value if search_input.value else ''
            refresh_table()
        
        search_input.on('update:model-value', on_search_change)
        
        # Seção de filtros
        filter_options = get_filter_options()
        filter_selects = filtros_acordos(
            filter_status=filter_status,
            filter_options=filter_options,
            on_filter_change=refresh_table,
            on_clear=lambda: clear_filters()
        )
        
        # Função para limpar filtros
        def clear_filters():
            """Limpa filtros com validação de DOM."""
            try:
                filter_status['value'] = ''
                search_term['value'] = ''
                # Limpar valores dos selects (com validação)
                if 'status' in filter_selects and filter_selects['status']:
                    try:
                        filter_selects['status'].value = ''
                    except:
                        pass
                if search_input:
                    try:
                        search_input.value = ''
                    except:
                        pass
                refresh_table()
            except Exception:
                # Ignora erros de DOM deferido
                pass
        
        # Função de filtragem
        def filter_rows(rows):
            """Aplica filtros aos acordos."""
            filtered = rows
            
            # Filtro de pesquisa (título e cliente)
            if search_term['value']:
                term = search_term['value'].lower()
                filtered = [
                    r for r in filtered 
                    if term in (r.get('titulo') or '').lower() 
                    or term in (r.get('cliente') or '').lower()
                ]
            
            # Filtro de status
            if filter_status['value'] and filter_status['value'].strip():
                status_filter = filter_status['value'].strip()
                filtered = [r for r in filtered if (r.get('status') or '').strip() == status_filter]
            
            return filtered
        
        @ui.refreshable
        def render_table():
            """Renderiza tabela de acordos."""
            # Busca acordos
            if search_term['value']:
                rows = buscar_acordos(search_term['value'])
            else:
                rows = listar_acordos()
            
            # Aplica filtros
            rows = filter_rows(rows)
            
            # Callback para editar acordo (ao clicar no título)
            def on_edit(acordo_id):
                """Callback para editar acordo - abre modal de edição."""
                if acordo_id:
                    open_edit_dialog(acordo_id)
            
            # Renderiza tabela (sem coluna de ações)
            table = tabela_acordos(
                acordos=rows,
                on_edit=on_edit
            )
        
        render_table_ref['func'] = render_table
        render_table()
