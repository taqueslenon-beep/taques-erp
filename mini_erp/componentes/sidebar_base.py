"""
Componente base de sidebar reutilizável.
Permite criar sidebars para diferentes workspaces com visual consistente.
Inclui funcionalidade de expandir/recolher com persistência.

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

# Constantes para estados da sidebar
LARGURA_EXPANDIDA = 190
LARGURA_RECOLHIDA = 70
LARGURA_MINIMA = 60  # Largura mínima absoluta - NUNCA menor que isso
DURACAO_TRANSICAO = 300  # ms


def _obter_estado_sidebar() -> bool:
    """
    Obtém o estado da sidebar do localStorage.
    Usa JavaScript para ler o valor e define em variável global.
    
    Returns:
        True se expandida, False se recolhida (padrão: True)
    """
    try:
        # Tenta obter do localStorage via JavaScript
        # Como é assíncrono, usa valor padrão e atualiza depois
        ui.run_javascript('''
            (function() {
                try {
                    var estado = localStorage.getItem("taques_sidebar_expandida");
                    if (estado === null) {
                        localStorage.setItem("taques_sidebar_expandida", "true");
                    }
                } catch(e) {
                    console.log("Erro ao ler estado da sidebar:", e);
                }
            })();
        ''')
        # Retorna padrão (expandida) - será atualizado pelo JavaScript se necessário
        return True
    except:
        return True


def _salvar_estado_sidebar(expandida: bool):
    """
    Salva o estado da sidebar no localStorage.
    
    Args:
        expandida: True para expandida, False para recolhida
    """
    try:
        valor = "true" if expandida else "false"
        ui.run_javascript(f'localStorage.setItem("taques_sidebar_expandida", "{valor}");')
    except Exception as e:
        print(f"Erro ao salvar estado da sidebar: {e}")


def _criar_item_menu(
    titulo: str, 
    icone: str, 
    rota: str, 
    rota_atual: str = None,
    expandida: bool = True
):
    """
    Cria um item individual do menu de navegação.

    Args:
        titulo: Texto exibido no item
        icone: Nome do ícone Material Design (ex: 'dashboard', 'folder')
        rota: URL de destino ao clicar
        rota_atual: Rota atual da página para destacar item ativo
        expandida: Se sidebar está expandida (mostra texto) ou recolhida (apenas ícone)
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
    classes_base = 'w-full flex flex-row flex-nowrap items-center rounded transition-colors no-underline cursor-pointer'
    
    # Ajusta gap e padding baseado no estado
    if expandida:
        classes_base += ' gap-3'
        padding = 'padding: 8px 8px 8px 12px;'
    else:
        classes_base += ' gap-0 justify-center'
        padding = 'padding: 12px;'

    # Adiciona classes de destaque se ativo
    if is_active:
        classes_item = f'{classes_base} bg-white/20'
    else:
        classes_item = f'{classes_base} hover:bg-white/10'

    # Cria link
    link = ui.link(target=rota).classes(classes_item).style(f'{padding} margin-left: 0;')
    
    with link:
        icon_elem = ui.icon(icone, size='sm').classes('text-white/80 flex-shrink-0')
        
        # Adiciona tooltip no ícone quando recolhido
        if not expandida:
            icon_elem.tooltip(titulo).props('delay=300')
        
        if expandida:
            ui.label(titulo).classes('text-sm font-medium text-white/90 whitespace-nowrap')


def render_sidebar(
    itens_menu: List[Dict[str, str]],
    rota_atual: str = None,
    largura: int = None,
    cor_fundo: str = None
):
    """
    Renderiza a sidebar completa com os itens de menu fornecidos.
    Inclui funcionalidade de expandir/recolher com botão toggle.
    
    REGRAS CRÍTICAS DE VISIBILIDADE:
    - Sidebar NUNCA desaparece (sempre visível)
    - Largura mínima: 60px (NUNCA menor)
    - Estado padrão: RECOLHIDA (apenas ícones)
    - Todos os ícones sempre clicáveis
    - Botão toggle sempre acessível no topo

    Args:
        itens_menu: Lista de dicionários com configuração de cada item
                   Formato: [{'icone': str, 'titulo': str, 'rota': str}, ...]
        rota_atual: Rota atual da página (para destacar item ativo)
        largura: Largura da sidebar em pixels (ignorado, usa estado expandido/recolhido)
        cor_fundo: Cor de fundo da sidebar (padrão: PRIMARY_COLOR)

    Exemplo de itens_menu:
        [
            {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/visao-geral/painel'},
            {'icone': 'folder', 'titulo': 'Casos', 'rota': '/visao-geral/casos'},
            {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/visao-geral/processos'},
        ]
    """
    cor = cor_fundo or PRIMARY_COLOR
    
    # Estado inicial: padrão RECOLHIDA (conforme imagem de referência)
    estado_inicial = False
    
    # Script para carregar estado do localStorage
    ui.run_javascript('''
        (function() {
            try {
                var estado = localStorage.getItem("taques_sidebar_expandida");
                
                // Se não tem estado salvo, usa padrão RECOLHIDA
                if (estado === null) {
                    estado = "false";
                    localStorage.setItem("taques_sidebar_expandida", "false");
                }
                
                // Define variável global para Python acessar
                window._taques_sidebar_state = estado === "true";
            } catch(e) {
                console.log("Erro ao carregar estado da sidebar:", e);
                window._taques_sidebar_state = false;
            }
        })();
    ''')
    
    # Estado reativo usando dicionário (compatível com NiceGUI)
    estado_sidebar = {'expandida': estado_inicial}
    
    # Calcula largura baseada no estado
    # GARANTE que nunca seja menor que LARGURA_MINIMA
    largura_atual = LARGURA_EXPANDIDA if estado_sidebar['expandida'] else LARGURA_RECOLHIDA
    if largura_atual < LARGURA_MINIMA:
        largura_atual = LARGURA_MINIMA
    
    # Adiciona CSS para transição suave e garantia de visibilidade
    ui.add_head_html(f'''
        <style>
            /* Sidebar SEMPRE visível - REGRAS CRÍTICAS */
            .sidebar-transition {{
                transition: width {DURACAO_TRANSICAO}ms ease-in-out !important;
                min-width: {LARGURA_MINIMA}px !important;
                width: auto !important;
                display: flex !important;
                visibility: visible !important;
                overflow: visible !important;
            }}
            
            /* Garantir que drawer nunca some */
            .q-drawer.sidebar-transition {{
                min-width: {LARGURA_MINIMA}px !important;
                display: flex !important;
                visibility: visible !important;
                overflow: visible !important;
            }}
            
            /* Botão toggle */
            .sidebar-toggle-btn {{
                transition: opacity 0.2s ease-in-out, background-color 0.2s ease-in-out;
                cursor: pointer;
            }}
            .sidebar-toggle-btn:hover {{
                opacity: 0.8;
                background-color: rgba(255, 255, 255, 0.15) !important;
            }}
        </style>
    ''')
    
    # Cria drawer com largura dinâmica
    # IMPORTANTE: value=True garante que drawer está sempre visível
    # persistent garante que não fecha automaticamente
    # min-width garantido via CSS inline
    with ui.left_drawer(value=True).props(f'width={largura_atual} bordered persistent').classes('border-r border-gray-200 sidebar-transition').style(f'background-color: {cor}; min-width: {LARGURA_MINIMA}px !important; display: flex !important; visibility: visible !important;') as drawer:
        # Timer para garantir que drawer nunca seja ocultado
        def garantir_visibilidade_drawer():
            """Garante que drawer sempre esteja visível"""
            try:
                if not drawer.value:
                    drawer.value = True
                # Força largura mínima via JavaScript se necessário
                ui.run_javascript(f'''
                    (function() {{
                        var drawer = document.querySelector('.q-drawer.sidebar-transition');
                        if (drawer) {{
                            drawer.style.minWidth = '{LARGURA_MINIMA}px';
                            drawer.style.display = 'flex';
                            drawer.style.visibility = 'visible';
                        }}
                    }})();
                ''')
            except Exception as e:
                print(f"Erro ao garantir visibilidade do drawer: {e}")
        
        # Verifica a cada 2 segundos que drawer está visível
        ui.timer(2.0, garantir_visibilidade_drawer)
        
        with ui.column().classes('w-full px-2 pt-2 gap-1'):
            # Container para botão toggle e itens do menu (refreshable)
            @ui.refreshable
            def render_menu_completo():
                is_expandida = estado_sidebar['expandida']
                
                # BOTÃO TOGGLE - PRIMEIRO ITEM DA SIDEBAR (fixo no topo)
                # Usa mesmo estilo dos outros itens do menu
                icon_toggle = 'chevron_left' if is_expandida else 'chevron_right'
                classes_toggle = 'w-full flex flex-row flex-nowrap items-center rounded transition-colors cursor-pointer'
                
                if is_expandida:
                    classes_toggle += ' gap-3'
                    padding_toggle = 'padding: 8px 8px 8px 12px;'
                else:
                    classes_toggle += ' gap-0 justify-center'
                    padding_toggle = 'padding: 12px;'
                
                classes_toggle += ' hover:bg-white/10'
                
                with ui.button().props('flat').classes(classes_toggle).style(f'{padding_toggle} margin-left: 0;') as toggle_btn:
                    icon_toggle_elem = ui.icon(icon_toggle, size='sm').classes('text-white/80 flex-shrink-0')
                    
                    # Tooltip quando recolhido
                    if not is_expandida:
                        icon_toggle_elem.tooltip('Expandir menu').props('delay=300')
                    
                    if is_expandida:
                        ui.label('Recolher menu').classes('text-sm font-medium text-white/90 whitespace-nowrap')
                    
                    def toggle_sidebar():
                        """Alterna estado da sidebar mantendo sempre visível"""
                        estado_sidebar['expandida'] = not estado_sidebar['expandida']
                        _salvar_estado_sidebar(estado_sidebar['expandida'])
                        
                        # Atualiza largura do drawer
                        # GARANTE que nunca seja menor que LARGURA_MINIMA
                        nova_largura = LARGURA_EXPANDIDA if estado_sidebar['expandida'] else LARGURA_RECOLHIDA
                        if nova_largura < LARGURA_MINIMA:
                            nova_largura = LARGURA_MINIMA
                        
                        # CRÍTICO: Garante que drawer está sempre visível antes de atualizar
                        drawer.value = True
                        
                        # Atualiza props do drawer mantendo visibilidade
                        drawer.props(f'width={nova_largura} bordered persistent')
                        drawer.style(f'background-color: {cor}; min-width: {LARGURA_MINIMA}px !important; display: flex !important; visibility: visible !important;')
                        
                        # Força visibilidade via JavaScript também
                        ui.run_javascript(f'''
                            (function() {{
                                var drawer = document.querySelector('.q-drawer.sidebar-transition');
                                if (drawer) {{
                                    drawer.style.minWidth = '{LARGURA_MINIMA}px';
                                    drawer.style.display = 'flex';
                                    drawer.style.visibility = 'visible';
                                    drawer.style.width = '{nova_largura}px';
                                }}
                            }})();
                        ''')
                        
                        # Atualiza menu completo
                        render_menu_completo.refresh()
                    
                    toggle_btn.on('click', toggle_sidebar)
                
                # Itens do menu (após o botão toggle)
                for item in itens_menu:
                    _criar_item_menu(
                        titulo=item.get('titulo', ''),
                        icone=item.get('icone', 'circle'),
                        rota=item.get('rota', '/'),
                        rota_atual=rota_atual,
                        expandida=is_expandida
                    )
            
            render_menu_completo()


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
        {'icone': 'dashboard', 'titulo': 'Painel', 'rota': '/visao-geral/painel'},
        {'icone': 'calendar_month', 'titulo': 'Prazos', 'rota': '/prazos'},
        {'icone': 'folder', 'titulo': 'Casos', 'rota': '/visao-geral/casos'},
        {'icone': 'gavel', 'titulo': 'Processos', 'rota': '/visao-geral/processos'},
        {'icone': 'assignment', 'titulo': 'Entregáveis', 'rota': '/visao-geral/entregaveis'},
        {'icone': 'handshake', 'titulo': 'Acordos/parcelamentos', 'rota': '/visao-geral/acordos'},
        {'icone': 'groups', 'titulo': 'Pessoas', 'rota': '/visao-geral/pessoas'},
        {'icone': 'settings', 'titulo': 'Configurações', 'rota': '/visao-geral/configuracoes'},
    ]

    # Mapeamento de workspace para menu
    MENUS_POR_WORKSPACE = {
        'area_cliente_schmidmeier': MENU_AREA_CLIENTE,
        'visao_geral_escritorio': MENU_VISAO_GERAL,
    }

    return MENUS_POR_WORKSPACE.get(workspace_id, MENU_AREA_CLIENTE)
