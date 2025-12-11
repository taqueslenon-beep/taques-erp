"""
Componente de seleção de workspace com dropdown.
Gerencia exibição e seleção de workspaces baseado em permissões do usuário.
"""
from nicegui import ui
from ..auth import get_current_user
from ..gerenciadores.gerenciador_workspace import (
    obter_workspace_atual,
    obter_workspaces_usuario,
    obter_info_workspace,
    alternar_workspace,
    verificar_acesso_workspace
)

# Cache de permissões para otimização (evita consultas repetidas ao Firebase)
_permissions_cache = {}
_cache_user_id = None


def limpar_cache_permissoes():
    """Limpa o cache de permissões. Útil quando perfil do usuário muda."""
    global _permissions_cache, _cache_user_id
    _permissions_cache = {}
    _cache_user_id = None


def render_workspace_dropdown():
    """
    Renderiza o dropdown de seleção de workspace no header.
    Exibe apenas se o usuário tiver acesso a múltiplos workspaces.
    
    Funcionalidades:
    - Abre menu dropdown ao clicar
    - Lista apenas workspaces permitidos
    - Indica workspace ativo com check
    - Alterna workspace ao selecionar
    - Fecha ao clicar fora (comportamento padrão do ui.menu)
    """
    global _permissions_cache, _cache_user_id
    
    user = get_current_user()
    if not user:
        return
    
    user_id = user.get('uid')
    
    # Limpa cache se usuário mudou
    if _cache_user_id != user_id:
        _permissions_cache = {}
        _cache_user_id = user_id
    
    # Obtém workspaces disponíveis para o usuário (com cache)
    if 'available_workspaces' not in _permissions_cache:
        _permissions_cache['available_workspaces'] = obter_workspaces_usuario()
    
    available_workspaces = _permissions_cache['available_workspaces']
    current_workspace_id = obter_workspace_atual()
    current_workspace_info = obter_info_workspace(current_workspace_id)
    
    if not current_workspace_info:
        return
    
    # Se tiver apenas 1 workspace, mostra texto fixo (sem dropdown)
    if len(available_workspaces) <= 1:
        with ui.element().style('background: rgba(255,255,255,0.1); padding: 8px 12px; border-radius: 6px; display: flex; align-items: center; gap: 8px;'):
            ui.icon(current_workspace_info['icon']).style('font-size: 16px;')
            ui.label(current_workspace_info['nome']).style('font-size: 13px; font-weight: 500; white-space: nowrap;')
        return
    
    # Se tiver múltiplos workspaces, mostra dropdown funcional
    # Estrutura: button com conteúdo customizado + menu dropdown
    # O menu do NiceGUI fecha automaticamente ao clicar fora
    with ui.button().props('flat dense').classes('p-0').style('background: rgba(255,255,255,0.1); padding: 8px 12px; border-radius: 6px;'):
        # Conteúdo visual do botão (ícone + texto + seta)
        with ui.row().classes('items-center gap-2'):
            ui.icon(current_workspace_info['icon']).style('font-size: 16px; color: white;')
            ui.label(current_workspace_info['nome']).style('font-size: 13px; font-weight: 500; white-space: nowrap; color: white;')
            ui.icon('arrow_drop_down').style('font-size: 16px; color: white;')
        
        # Menu dropdown com opções de workspace
        # O menu abre ao clicar no botão e fecha ao clicar fora ou selecionar item
        with ui.menu().props('anchor="bottom right" self="top right"'):
            for workspace_id in available_workspaces:
                workspace_info = obter_info_workspace(workspace_id)
                if not workspace_info:
                    continue
                
                is_current = workspace_id == current_workspace_id
                
                # Cria handler de clique para cada workspace
                def make_click_handler(ws_id):
                    def handler():
                        try:
                            # Verifica permissão antes de alternar (segurança server-side)
                            if not verificar_acesso_workspace(workspace_id=ws_id):
                                ui.notify('Você não tem permissão para acessar este workspace', type='negative')
                                return
                            
                            # Alterna workspace (salva na sessão e localStorage)
                            if alternar_workspace(ws_id, verificar_permissao=False):  # Já verificamos acima
                                # Obtém informações do workspace selecionado
                                target_workspace_info = obter_info_workspace(ws_id)
                                if target_workspace_info:
                                    # Redireciona para página inicial do workspace
                                    ui.notify(f'Alternando para {target_workspace_info["nome"]}...', type='info')
                                    ui.navigate.to(target_workspace_info['rota_inicial'])
                                else:
                                    ui.notify('Erro: Workspace não encontrado', type='negative')
                            else:
                                ui.notify('Erro ao alternar workspace', type='negative')
                        except Exception as e:
                            print(f"Erro ao alternar workspace: {e}")
                            ui.notify('Erro ao alternar workspace. Tente novamente.', type='negative')
                    return handler
                
                # Item do menu para cada workspace
                with ui.menu_item(on_click=make_click_handler(workspace_id)):
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon(workspace_info['icon'], size='xs')
                        ui.label(workspace_info['nome']).classes('flex-grow')
                        # Indicador visual para workspace ativo
                        if is_current:
                            ui.icon('check', size='xs').classes('text-white')

