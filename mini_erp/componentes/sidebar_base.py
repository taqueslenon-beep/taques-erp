"""
Componente base de sidebar reutilizável.
Permite criar sidebars para diferentes workspaces com visual consistente.

Uso:
    from mini_erp.componentes.sidebar_base import render_sidebar

    # Define itens do menu do workspace
    MENU_ITEMS = [
        {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/'},
        {'icone': 'folder', 'titulo': 'Casos', 'rota': '/casos'},
    ]

    # Na página, renderiza a sidebar
    render_sidebar(MENU_ITEMS)
"""
from typing import List, Dict, Optional
from nicegui import ui

# Cor primária do sistema (importada do core para consistência)
PRIMARY_COLOR = '#223631'


def _criar_item_menu(titulo: str, icone: str, rota: str, rota_atual: str = None):
    """
    Cria um item individual do menu de navegação.

    Args:
        titulo: Texto exibido no item
        icone: Nome do ícone Material Design (ex: 'dashboard', 'folder')
        rota: URL de destino ao clicar
        rota_atual: Rota atual da página para destacar item ativo
    """
    # Verifica se este item está ativo (rota atual corresponde)
    is_active = False
    if rota_atual:
        # Normaliza rotas para comparação
        rota_normalizada = rota.rstrip('/')
        rota_atual_normalizada = rota_atual.rstrip('/')

        # Verifica correspondência exata ou se é subpágina
        if rota_normalizada == rota_atual_normalizada:
            is_active = True
        elif rota_normalizada != '' and rota_atual_normalizada.startswith(rota_normalizada + '/'):
            is_active = True

    # Classes base do item
    classes_base = 'w-full flex flex-row flex-nowrap items-center gap-3 rounded transition-colors no-underline cursor-pointer'

    # Adiciona classes de destaque se ativo
    if is_active:
        classes_item = f'{classes_base} bg-white/20'
    else:
        classes_item = f'{classes_base} hover:bg-white/10'

    with ui.link(target=rota).classes(classes_item).style('padding: 8px 8px 8px 12px; margin-left: 0;'):
        ui.icon(icone, size='sm').classes('text-white/80 flex-shrink-0')
        ui.label(titulo).classes('text-sm font-medium text-white/90 whitespace-nowrap')


def render_sidebar(
    itens_menu: List[Dict[str, str]],
    rota_atual: str = None,
    largura: int = 190,
    cor_fundo: str = None
):
    """
    Renderiza a sidebar completa com os itens de menu fornecidos.

    Args:
        itens_menu: Lista de dicionários com configuração de cada item
                   Formato: [{'icone': str, 'titulo': str, 'rota': str}, ...]
        rota_atual: Rota atual da página (para destacar item ativo)
        largura: Largura da sidebar em pixels (padrão: 190)
        cor_fundo: Cor de fundo da sidebar (padrão: PRIMARY_COLOR)

    Exemplo de itens_menu:
        [
            {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/visao-geral/painel'},
            {'icone': 'folder', 'titulo': 'Casos', 'rota': '/visao-geral/casos'},
            {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/visao-geral/processos'},
        ]
    """
    cor = cor_fundo or PRIMARY_COLOR

    with ui.left_drawer(value=True).props(f'width={largura} bordered persistent').classes('border-r border-gray-200').style(f'background-color: {cor}'):
        with ui.column().classes('w-full px-2 pt-4 gap-1'):
            for item in itens_menu:
                _criar_item_menu(
                    titulo=item.get('titulo', ''),
                    icone=item.get('icone', 'circle'),
                    rota=item.get('rota', '/'),
                    rota_atual=rota_atual
                )


def obter_itens_menu_por_workspace(workspace_id: str) -> List[Dict[str, str]]:
    """
    Retorna os itens de menu para um workspace específico.

    Args:
        workspace_id: ID do workspace ('area_cliente_schmidmeier' ou 'visao_geral_escritorio')

    Returns:
        Lista de itens de menu configurados para o workspace
    """
    # Menu do workspace "Área do cliente: Schmidmeier"
    MENU_AREA_CLIENTE = [
        {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/'},
        {'icone': 'psychology', 'titulo': 'Inteligência', 'rota': '/inteligencia'},
        {'icone': 'folder', 'titulo': 'Casos', 'rota': '/casos'},
        {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/processos'},
        {'icone': 'handshake', 'titulo': 'Acordos', 'rota': '/acordos'},
        {'icone': 'groups', 'titulo': 'Pessoas', 'rota': '/pessoas'},
        {'icone': 'settings', 'titulo': 'Configurações', 'rota': '/configuracoes'},
    ]

    # Menu do workspace "Visão geral do escritório"
    MENU_VISAO_GERAL = [
        {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/visao-geral/painel'},
        {'icone': 'folder', 'titulo': 'Casos', 'rota': '/visao-geral/casos'},
        {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/visao-geral/processos'},
        {'icone': 'handshake', 'titulo': 'Acordos', 'rota': '/visao-geral/acordos'},
        {'icone': 'groups', 'titulo': 'Pessoas', 'rota': '/visao-geral/pessoas'},
        {'icone': 'settings', 'titulo': 'Configurações', 'rota': '/visao-geral/configuracoes'},
    ]

    # Mapeamento de workspace para menu
    MENUS_POR_WORKSPACE = {
        'area_cliente_schmidmeier': MENU_AREA_CLIENTE,
        'visao_geral_escritorio': MENU_VISAO_GERAL,
    }

    return MENUS_POR_WORKSPACE.get(workspace_id, MENU_AREA_CLIENTE)
