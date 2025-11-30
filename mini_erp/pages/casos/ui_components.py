"""
Módulo de componentes de UI para o módulo de Casos.

Contém componentes NiceGUI reutilizáveis, incluindo
editores de texto, listas de cards e toggles de visualização.
"""

from nicegui import ui

from ...core import (
    PRIMARY_COLOR,
    get_cases_list,
    get_clients_list
)

from .models import filter_state
from .business_logic import get_filtered_cases, deduplicate_cases_by_title
from .database import remove_case, renumber_cases_of_type
from .utils import get_short_name_helper, get_state_flag_html


# =============================================================================
# CSS CUSTOMIZADO
# =============================================================================

CASE_CARD_CSS = '''
<style>
.case-card {
    transition: all 0.2s ease-in-out;
    border-radius: 12px;
    overflow: hidden;
}
.case-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
.case-card .q-card {
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
}
.case-title {
    line-height: 1.3;
    margin-bottom: 4px;
}
.case-clients {
    line-height: 1.4;
    min-height: 20px;
}
.case-chips {
    gap: 6px;
}
/* Chips de categoria (Contencioso / Consultivo) com alta legibilidade
   Mantém exatamente os tons já usados, apenas adicionando borda e leve elevação. */
.case-category-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 28px;
    padding: 2px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    line-height: 1.3;
    text-transform: none;
}
.case-category-chip--contencioso {
    /* Tons equivalentes a bg-red-100 / text-red-800 */
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #991b1b; /* borda 1px em tom mais escuro para máximo contraste */
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.10); /* leve elevação para evitar efeito "lavado" */
}
.case-category-chip--consultivo {
    /* Tons equivalentes a bg-green-100 / text-green-800 */
    background-color: #dcfce7;
    color: #166534;
    border: 1px solid #166534; /* borda 1px em tom mais escuro para máximo contraste */
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.10); /* leve elevação para evitar efeito "lavado" */
}
.case-footer {
    background: rgba(249, 250, 251, 0.8);
    backdrop-filter: blur(8px);
}
.case-action-buttons .q-btn {
    transition: all 0.15s ease;
}
.case-action-buttons .q-btn:hover {
    transform: scale(1.1);
}
</style>
'''


# =============================================================================
# COMPONENTES DE UI
# =============================================================================

def create_rich_text_editor(value: str = '', placeholder: str = '', on_change=None):
    """
    Cria um editor de texto rico com funcionalidades similares ao Slack.
    Toolbar inclui: Bold, Italic, Underline, Strikethrough, Link, Lists, Code Block, Quote
    
    O NiceGUI usa Quill editor. O editor padrão já inclui muitas dessas funcionalidades.
    Adicionamos CSS e configuração para garantir todas as opções do Slack estejam visíveis.
    
    Args:
        value: Valor inicial do editor
        placeholder: Texto placeholder
        on_change: Callback para mudanças
        
    Returns:
        Elemento ui.editor configurado
    """
    editor = ui.editor(
        value=value,
        placeholder=placeholder,
        on_change=on_change
    ).props('''
toolbar="bold italic underline strike | bullist numlist | outdent indent | removeformat"
content-style="font-family: sans-serif; font-size: 14px;"
''').classes('w-full min-h-[150px]')
    
    # Adicionar CSS global uma vez para melhorar a aparência da toolbar estilo Slack
    if not hasattr(create_rich_text_editor, '_css_added'):
        ui.add_head_html('''
        <style>
        /* Melhorias na toolbar do editor estilo Slack */
        .q-editor__toolbar {
            border-bottom: 1px solid #e0e0e0 !important;
            padding: 6px 8px !important;
            background: #fafafa !important;
        }
        .q-editor__toolbar .q-btn {
            margin: 0 1px !important;
            padding: 4px 6px !important;
            min-width: 32px !important;
        }
        .q-editor__toolbar .q-btn:hover {
            background-color: #e8e8e8 !important;
        }
        </style>
        ''')
        create_rich_text_editor._css_added = True
    
    return editor


@ui.refreshable
def render_cases_list():
    """
    Renderiza a lista de casos em formato de grid de cards.
    
    Usa o decorador @ui.refreshable para permitir atualização dinâmica.
    """
    if filter_state.get('case_type') == 'new':
        # Evita duplicação de números ao entrar na aba de casos novos
        renumber_cases_of_type('Novo')
    
    filtered_cases = get_filtered_cases()
    
    if not get_cases_list():
        with ui.card().classes('w-full p-8 flex justify-center items-center bg-white'):
            ui.label('Nenhum caso cadastrado.').classes('text-gray-400 italic')
        return
    
    if not filtered_cases:
        with ui.card().classes('w-full p-8 flex justify-center items-center bg-white'):
            ui.label('Nenhum caso encontrado com os filtros aplicados.').classes('text-gray-400 italic')
        return

    # Adicionar CSS customizado para melhorar a aparência dos cards
    ui.add_head_html(CASE_CARD_CSS)
    
    with ui.grid(columns=4).classes('w-full gap-4'):
        for case in filtered_cases:
            with ui.card().classes('w-full p-4 shadow-md hover:shadow-xl transition-all duration-200 border case-card').style(f'border-color: {PRIMARY_COLOR}; border-width: 1px;'):
                with ui.dialog() as delete_dialog, ui.card().classes('w-full max-w-sm p-6'):
                    ui.label('Excluir caso').classes('text-lg font-bold mb-2 text-primary')
                    ui.label(f'Tem certeza que deseja excluir "{case["title"]}"?').classes('text-sm text-gray-600 mb-4')
                    ui.label('Esta ação não pode ser desfeita.').classes('text-xs text-red-500 mb-4')

                    def confirm_delete_case(case_ref=case):
                        if remove_case(case_ref):
                            ui.notify('Caso removido!')
                            delete_dialog.close()
                            render_cases_list.refresh()

                    with ui.row().classes('w-full justify-end gap-2'):
                        ui.button('Cancelar', on_click=delete_dialog.close).props('flat color=grey')
                        ui.button('Excluir', on_click=confirm_delete_case).classes('bg-red-600 text-white')

                # Estrutura organizada do card com seções bem definidas
                with ui.column().classes('w-full gap-3'):
                    # Seção principal: título e clientes (sempre clicável)
                    with ui.column().classes('w-full gap-2 cursor-pointer').on('click', lambda c=case: ui.navigate.to(f'/casos/{c["slug"]}')):
                        # Título do caso
                        ui.label(case['title']).classes('text-lg font-bold text-gray-800 leading-tight case-title')

                        # Clientes usando regra centralizada de nome de exibição
                        from ...core import get_display_name, get_display_name_by_id
                        
                        clients_list = get_clients_list()
                        all_client_names = [c.get('name') or c.get('full_name', '') for c in clients_list if c.get('name') or c.get('full_name', '')]
                        
                        if 'clients' in case and case['clients']:
                            # Verifica se todos os clientes estão vinculados
                            if set(case['clients']) == set(all_client_names) and len(case['clients']) > 0:
                                # Exibe mensagem simplificada para "Todos os Clientes"
                                clients_text = f'✓ Todos os Clientes ({len(case["clients"])})'
                                full_names = clients_text
                            else:
                                # Usa função centralizada para obter nome de exibição
                                display_names = []
                                full_names_list = []
                                
                                for client_name in case['clients']:
                                    # Busca cliente na lista para obter ID e usar função centralizada
                                    client_found = False
                                    for client in clients_list:
                                        client_full_name = client.get('name') or client.get('full_name', '')
                                        if client_full_name == client_name:
                                            # Usa função centralizada
                                            display_name = get_display_name(client)
                                            display_names.append(display_name)
                                            full_names_list.append(client_full_name)
                                            client_found = True
                                            break
                                    
                                    if not client_found:
                                        # Fallback para nome original se não encontrar
                                        display_names.append(client_name.split()[0] if client_name else client_name)
                                        full_names_list.append(client_name)
                                
                                clients_text = ', '.join(display_names)
                                full_names = ', '.join(full_names_list)
                        elif 'client' in case:
                            # Busca cliente único
                            client_found = False
                            for client in clients_list:
                                client_full_name = client.get('name') or client.get('full_name', '')
                                if client_full_name == case['client']:
                                    clients_text = get_display_name(client)
                                    full_names = client_full_name
                                    client_found = True
                                    break
                            
                            if not client_found:
                                clients_text = case['client'].split()[0] if case['client'] else case['client']
                                full_names = case['client']
                        else:
                            clients_text = 'Sem cliente'
                            full_names = 'Sem cliente'

                        # Limitar texto de clientes se for muito longo
                        display_clients = clients_text if len(clients_text) <= 60 else clients_text[:57] + '...'
                        
                        ui.label(display_clients).classes('text-sm text-gray-600 leading-relaxed case-clients').tooltip(full_names)

                    # Seção de status e categoria (chips organizados)
                    with ui.row().classes('gap-2 flex-wrap items-center case-chips'):
                        # Cores dos status com boa legibilidade
                        status_color = {
                            'Em andamento': 'text-gray-900',
                            'Concluído': 'text-white',
                            'Concluído com pendências': 'text-white',
                            'Em monitoramento': 'text-white'
                        }.get(case['status'], 'bg-gray-200 text-gray-800')
                        
                        status_bg = {
                            'Em andamento': '#eab308',           # amarelo claro
                            'Concluído': '#166534',              # verde escuro
                            'Concluído com pendências': '#4d7c0f', # verde militar
                            'Em monitoramento': '#ea580c'         # laranja
                        }.get(case['status'], '#9ca3af')

                        # Chip de status
                        ui.label(case['status']).classes(
                            f'text-xs px-3 py-1 rounded-full font-medium {status_color}'
                        ).style(f'background-color: {status_bg}; border: 1px solid rgba(0,0,0,0.1);')
                        
                        # Chip de categoria (Contencioso / Consultivo) com estilos otimizados
                        category = case.get('category', 'Contencioso')
                        if category == 'Consultivo':
                            chip_classes = 'case-category-chip case-category-chip--consultivo'
                        else:
                            # Default visual: Contencioso
                            chip_classes = 'case-category-chip case-category-chip--contencioso'
                        ui.label(category).classes(chip_classes)

                    # Rodapé do card: informações adicionais e botões de ação
                    with ui.row().classes('w-full justify-between items-center mt-3 pt-3 border-t border-gray-100 case-footer'):
                        # Lado esquerdo: estado (sempre presente para manter alinhamento)
                        with ui.row().classes('items-center gap-2 min-w-[80px]'):
                            if case.get('state'):
                                ui.html(get_state_flag_html(case['state'], 16), sanitize=False)
                                ui.label(case['state']).classes('text-xs text-gray-600 font-medium')
                            else:
                                ui.label('---').classes('text-xs text-gray-400 font-medium')
                        
                        # Botões de ação no lado direito (sempre alinhados)
                        with ui.row().classes('items-center gap-1 case-action-buttons'):
                            ui.button(
                                icon='open_in_new',
                                on_click=lambda c=case: ui.navigate.to(f'/casos/{c["slug"]}')
                            ).props('flat round dense color=primary size=sm').tooltip('Abrir caso')
                            ui.button(
                                icon='delete',
                                on_click=delete_dialog.open
                            ).props('flat round dense color=red size=sm').tooltip('Excluir caso')


@ui.refreshable
def case_view_toggle():
    """
    Botões de alternância entre visualização de casos antigos, novos e futuros.
    
    Usa o decorador @ui.refreshable para permitir atualização dinâmica.
    """
    current_type = filter_state.get('case_type', 'old')

    def change_type(new_type: str):
        filter_state['case_type'] = new_type
        case_view_toggle.refresh()
        render_cases_list.refresh()

    with ui.row().classes('w-full items-center gap-3 mb-4'):
        ui.label('Visualização:').classes('text-sm text-gray-600')
        ui.button(
            '🔴 Casos antigos',
            on_click=lambda: change_type('old')
        ).props('flat color=primary' if current_type == 'old' else 'flat color=grey-7')
        ui.button(
            '🔥 Casos novos',
            on_click=lambda: change_type('new')
        ).props('flat color=primary' if current_type == 'new' else 'flat color=grey-7')
        ui.button(
            '🔮 Casos futuros',
            on_click=lambda: change_type('future')
        ).props('flat color=primary' if current_type == 'future' else 'flat color=grey-7')

