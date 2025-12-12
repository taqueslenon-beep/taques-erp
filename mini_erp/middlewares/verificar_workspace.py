"""
Middleware para verificar permissão de acesso a workspaces.
Protege rotas baseadas em workspace e perfil do usuário.
"""
from functools import wraps
from nicegui import ui
from ..auth import is_authenticated, get_current_user
from ..gerenciadores.gerenciador_workspace import (
    verificar_acesso_workspace,
    obter_workspace_atual,
    obter_info_workspace,
    WORKSPACE_PADRAO
)


def require_workspace_access(workspace_id: str = None, redirect_on_deny: bool = True):
    """
    Decorator para proteger rotas baseadas em workspace.
    Verifica se o usuário tem permissão para acessar o workspace da rota.
    
    Args:
        workspace_id: ID do workspace requerido (None para detectar automaticamente da rota)
        redirect_on_deny: Se True, redireciona para workspace permitido em caso de negação
    
    Exemplo:
        @ui.page('/visao-geral-escritorio/casos')
        @require_workspace_access('visao_geral_escritorio')
        def casos():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verifica autenticação primeiro
            if not is_authenticated():
                ui.navigate.to('/login')
                return
            
            # Se workspace_id não fornecido, tenta detectar da rota
            target_workspace = workspace_id
            if target_workspace is None:
                # Detecta workspace baseado na rota atual
                from nicegui import context
                route = context.get_client().request.path

                # Rotas /visao-geral/* pertencem ao workspace visao_geral_escritorio
                if '/visao-geral' in route:
                    target_workspace = 'visao_geral_escritorio'
                else:
                    target_workspace = 'area_cliente_schmidmeier'
            
            # Verifica permissão de acesso
            if not verificar_acesso_workspace(workspace_id=target_workspace):
                if redirect_on_deny:
                    # Redireciona para workspace padrão ou primeiro disponível
                    user = get_current_user()
                    if user:
                        from ..gerenciadores.gerenciador_workspace import obter_workspaces_usuario
                        workspaces_disponiveis = obter_workspaces_usuario()
                        if workspaces_disponiveis:
                            workspace_permitido = workspaces_disponiveis[0]
                            workspace_info = obter_info_workspace(workspace_permitido)
                            if workspace_info:
                                ui.notify('Você não tem permissão para acessar este workspace', type='negative')
                                ui.navigate.to(workspace_info['rota_inicial'])
                                return
                    
                    # Fallback: redireciona para workspace padrão
                    workspace_info = obter_info_workspace(WORKSPACE_PADRAO)
                    if workspace_info:
                        ui.navigate.to(workspace_info['rota_inicial'])
                else:
                    # Apenas mostra erro sem redirecionar
                    ui.notify('Você não tem permissão para acessar este workspace', type='negative')
                return
            
            # Define workspace atual na sessão se tiver permissão
            from ..gerenciadores.gerenciador_workspace import definir_workspace
            definir_workspace(target_workspace)
            
            # Executa função original
            return func(*args, **kwargs)
        return wrapper
    return decorator


def verificar_e_definir_workspace_automatico():
    """
    Verifica e define workspace automaticamente baseado na rota atual.
    Usado em páginas que não usam o decorator.
    """
    if not is_authenticated():
        return False

    from nicegui import context
    try:
        route = context.get_client().request.path

        # Detecta workspace baseado na rota
        # Rotas /visao-geral/* pertencem ao workspace visao_geral_escritorio
        if '/visao-geral' in route:
            target_workspace = 'visao_geral_escritorio'
        else:
            target_workspace = 'area_cliente_schmidmeier'
        
        # Verifica permissão
        if verificar_acesso_workspace(workspace_id=target_workspace):
            from ..gerenciadores.gerenciador_workspace import definir_workspace
            definir_workspace(target_workspace)
            return True
        else:
            # Sem permissão, redireciona
            from ..gerenciadores.gerenciador_workspace import obter_workspaces_usuario, obter_info_workspace, WORKSPACE_PADRAO
            workspaces_disponiveis = obter_workspaces_usuario()
            if workspaces_disponiveis:
                workspace_permitido = workspaces_disponiveis[0]
                workspace_info = obter_info_workspace(workspace_permitido)
                if workspace_info:
                    ui.notify('Você não tem permissão para acessar este workspace', type='negative')
                    ui.navigate.to(workspace_info['rota_inicial'])
            else:
                workspace_info = obter_info_workspace(WORKSPACE_PADRAO)
                if workspace_info:
                    ui.navigate.to(workspace_info['rota_inicial'])
            return False
    except Exception as e:
        print(f"Erro ao verificar workspace automático: {e}")
        return False



