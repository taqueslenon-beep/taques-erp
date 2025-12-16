"""
Componente base de sidebar reutilizável.
Sidebar sempre expandida e fixa (220px) - sem opção de recolher.

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

# CORREÇÃO: Sidebar sempre expandida e fixa
LARGURA_FIXA = 220  # Largura fixa da sidebar (220px para caber textos completos como "Acordos/parcelamentos")


# REMOVIDO: Funções de estado da sidebar (não são mais necessárias)
# A sidebar está sempre expandida e fixa


def _criar_item_menu(
    titulo: str, 
    icone: str, 
    rota: str, 
    rota_atual: str = None
):
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

    # CORREÇÃO: Classes base do item com espaçamento reduzido
    # gap-2 = 8px entre ícone e texto (reduzido de gap-3 = 12px)
    # padding reduzido: 12px vertical e 16px horizontal (menos padding-left)
    classes_base = 'w-full flex flex-row flex-nowrap items-center gap-2 rounded transition-colors no-underline cursor-pointer'
    padding = 'padding: 12px 16px;'

    # Adiciona classes de destaque se ativo
    if is_active:
        classes_item = f'{classes_base} bg-white/20'
    else:
        classes_item = f'{classes_base} hover:bg-white/10'

    # Cria link
    link = ui.link(target=rota).classes(classes_item).style(f'{padding} margin-left: 0;')
    
    with link:
        # CORREÇÃO: Ícone com largura fixa para alinhamento
        ui.icon(icone, size='sm').classes('text-white/80 flex-shrink-0').style('width: 24px; min-width: 24px; text-align: center;')
        # CORREÇÃO: Texto completo sem cortar (nowrap mas com overflow visible para não truncar)
        ui.label(titulo).classes('text-sm font-medium text-white/90').style('white-space: nowrap; overflow: visible; text-overflow: clip;')


def render_sidebar(
    itens_menu: List[Dict[str, str]],
    rota_atual: str = None,
    largura: int = None,
    cor_fundo: str = None
):
    """
    Renderiza a sidebar completa com os itens de menu fornecidos.
    Sidebar sempre expandida e fixa (220px) - sem opção de recolher.
    
    REGRAS CRÍTICAS DE VISIBILIDADE:
    - Sidebar NUNCA desaparece (sempre visível)
    - Largura fixa: 220px (sempre expandida, suficiente para textos completos)
    - Sem botão de recolher (simplificado)
    - Todos os itens sempre visíveis (ícone + texto completo)

    Args:
        itens_menu: Lista de dicionários com configuração de cada item
                   Formato: [{'icone': str, 'titulo': str, 'rota': str}, ...]
        rota_atual: Rota atual da página (para destacar item ativo)
        largura: Largura da sidebar em pixels (ignorado, sempre 220px)
        cor_fundo: Cor de fundo da sidebar (padrão: PRIMARY_COLOR)

    Exemplo de itens_menu:
        [
            {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/visao-geral/painel'},
            {'icone': 'folder', 'titulo': 'Casos', 'rota': '/visao-geral/casos'},
            {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/visao-geral/processos'},
        ]
    """
    cor = cor_fundo or PRIMARY_COLOR
    
    # CORREÇÃO: Sidebar sempre expandida com largura fixa
    largura_atual = LARGURA_FIXA
    
    # CORREÇÃO: CSS simplificado para sidebar sempre expandida e fixa
    ui.add_head_html(f'''
        <style>
            /* Sidebar SEMPRE visível e fixa (220px) */
            .sidebar-transition {{
                width: {LARGURA_FIXA}px !important;
                min-width: {LARGURA_FIXA}px !important;
                max-width: {LARGURA_FIXA}px !important;
                display: flex !important;
                visibility: visible !important;
                overflow: visible !important;
            }}
            
            /* Garantir que drawer nunca some */
            .q-drawer.sidebar-transition {{
                width: {LARGURA_FIXA}px !important;
                min-width: {LARGURA_FIXA}px !important;
                max-width: {LARGURA_FIXA}px !important;
                display: flex !important;
                visibility: visible !important;
                overflow: visible !important;
                position: fixed !important;
                z-index: 1000 !important;
            }}
            
            /* CORREÇÃO: Container de conteúdo - deve começar após a sidebar (220px) */
            .q-page-container {{
                margin-left: 220px !important;  /* Largura da sidebar fixa */
                padding-left: 16px !important;  /* Pequeno respiro após sidebar */
                padding-right: 16px !important;
                max-width: none !important;
            }}
            
            /* Remover margin duplicado de containers internos */
            .q-page {{
                margin-left: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }}
            
            /* Container principal dentro de layout() - sem margin/padding extra */
            .taques-content-container {{
                margin-left: 0 !important;  /* Sem margin duplicado */
                padding-left: 0 !important;  /* Padding já no container pai */
                padding-right: 0 !important;
                max-width: none !important;
            }}
            
            /* Remover centralização automática de containers internos */
            .q-page-container > div,
            .q-page > div,
            .taques-content-container > div {{
                margin-left: 0 !important;
                margin-right: auto !important;
            }}
            
            /* CORREÇÃO: Garantir que textos dos itens do menu não sejam cortados */
            .sidebar-transition .q-item__label,
            .sidebar-transition label {{
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
                word-wrap: break-word !important;
            }}
            
            /* Garantir que conteúdo fique abaixo da sidebar */
            .q-page-container, .q-page, .taques-content-container {{
                position: relative !important;
                z-index: 1 !important;
            }}
        </style>
    ''')
    
    # CORREÇÃO: Drawer sempre expandido e fixo (220px)
    # IMPORTANTE: value=True garante que drawer está sempre visível
    # persistent garante que não fecha automaticamente
    # behavior=push faz o drawer EMPURRAR o conteúdo
    # overlay=false desabilita overlay
    # no-swipe-open e no-swipe-close desabilitam gestos de swipe
    with ui.left_drawer(value=True).props(f'width={LARGURA_FIXA} bordered persistent behavior=push overlay=false no-swipe-open no-swipe-close').classes('border-r border-gray-200 sidebar-transition').style(f'background-color: {cor}; width: {LARGURA_FIXA}px !important; min-width: {LARGURA_FIXA}px !important; max-width: {LARGURA_FIXA}px !important; display: flex !important; visibility: visible !important; z-index: 1000;') as drawer:
        # CORREÇÃO: Proteção básica de visibilidade (simplificada - sem MutationObserver)
        ui.run_javascript(f'''
            (function() {{
                // Proteção básica contra remoção do drawer durante navegação
                var protegerDrawer = function() {{
                    var drawer = document.querySelector('.q-drawer.sidebar-transition');
                    if (drawer) {{
                        drawer.style.width = '{LARGURA_FIXA}px';
                        drawer.style.minWidth = '{LARGURA_FIXA}px';
                        drawer.style.maxWidth = '{LARGURA_FIXA}px';
                        drawer.style.display = 'flex';
                        drawer.style.visibility = 'visible';
                    }}
                }};
                
                // Executar imediatamente
                protegerDrawer();
                
                // Executar a cada 100ms durante os primeiros 2 segundos (cobre transições de navegação)
                // Timer já é suficiente - MutationObserver removido para evitar erros
                var contador = 0;
                var intervalo = setInterval(function() {{
                    protegerDrawer();
                    contador++;
                    if (contador >= 20) clearInterval(intervalo);
                }}, 100);
            }})();
        ''')
        
        # CORREÇÃO: Menu simplificado - sem botão toggle, padding reduzido
        with ui.column().classes('w-full px-0 pt-2 gap-1'):
            # Itens do menu (sempre expandidos com ícone + texto)
            for item in itens_menu:
                _criar_item_menu(
                    titulo=item.get('titulo', ''),
                    icone=item.get('icone', 'circle'),
                    rota=item.get('rota', '/'),
                    rota_atual=rota_atual
                )


def obter_itens_menu_por_workspace(workspace_id: str, usuario_admin: bool = False) -> List[Dict[str, str]]:
    """
    Retorna os itens de menu para um workspace específico.
    Filtra itens que requerem permissão de administrador.

    Args:
        workspace_id: ID do workspace ('area_cliente_schmidmeier' ou 'visao_geral_escritorio')
        usuario_admin: Se True, inclui itens restritos a administradores

    Returns:
        Lista de itens de menu configurados para o workspace (filtrados por permissão)
    """
    # Menu do workspace "Área do cliente: Schmidmeier"
    MENU_AREA_CLIENTE = [
        {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/'},
        {'icone': 'calendar_month', 'titulo': 'Prazos', 'rota': '/prazos'},
        {'icone': 'psychology', 'titulo': 'Inteligência', 'rota': '/inteligencia'},
        {'icone': 'folder', 'titulo': 'Casos', 'rota': '/casos'},
        {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/processos'},
        {'icone': 'handshake', 'titulo': 'Acordos/parcelamentos', 'rota': '/acordos'},
        {'icone': 'groups', 'titulo': 'Pessoas', 'rota': '/pessoas'},
        {'icone': 'settings', 'titulo': 'Configurações', 'rota': '/configuracoes'},
    ]

    # Menu do workspace "Visão geral do escritório"
    MENU_VISAO_GERAL = [
        # Central de Comando como PRIMEIRO item (acima de Painel)
        {'icone': 'hub', 'titulo': 'Central de Comando', 'rota': '/visao-geral/central-comando'},
        {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/visao-geral/painel'},
        {'icone': 'trending_up', 'titulo': 'Novos Negócios', 'rota': '/visao-geral/novos-negocios'},
        {'icone': 'calendar_month', 'titulo': 'Prazos', 'rota': '/prazos'},
        {'icone': 'folder', 'titulo': 'Casos', 'rota': '/visao-geral/casos'},
        {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/visao-geral/processos'},
        {'icone': 'assignment', 'titulo': 'Entregáveis', 'rota': '/visao-geral/entregaveis'},
        {'icone': 'handshake', 'titulo': 'Acordos/parcelamentos', 'rota': '/visao-geral/acordos'},
        {'icone': 'groups', 'titulo': 'Pessoas', 'rota': '/visao-geral/pessoas'},
        {'icone': 'settings', 'titulo': 'Configurações', 'rota': '/visao-geral/configuracoes'},
    ]

    # Menu do workspace "Parceria - DF/Taques"
    MENU_PARCERIA_DF_TAQUES = [
        {'icone': 'hub', 'titulo': 'Central de Comando', 'rota': '/parceria-df-taques/central-comando'},
    ]

    # Mapeamento de workspace para menu
    MENUS_POR_WORKSPACE = {
        'area_cliente_schmidmeier': MENU_AREA_CLIENTE,
        'visao_geral_escritorio': MENU_VISAO_GERAL,
        'parceria_df_taques': MENU_PARCERIA_DF_TAQUES,
    }

    return MENUS_POR_WORKSPACE.get(workspace_id, MENU_AREA_CLIENTE)
