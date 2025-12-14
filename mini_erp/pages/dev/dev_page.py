"""
Página principal do módulo Desenvolvedor.
Painel de ferramentas e informações para desenvolvedores do sistema.
"""
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated, get_current_user
from firebase_admin import auth as admin_auth
from .dev_database import obter_todos_workspaces, obter_todos_usuarios
from .dev_components import card_workspaces, card_usuarios


def _is_developer(uid: str) -> bool:
    """
    Verifica se o usuário é desenvolvedor/administrador.
    
    Verifica:
    1. Se tem 'visao_geral' nos workspaces (collection usuarios_sistema)
    2. Se tem custom_claim 'admin' = true
    
    Args:
        uid: UID do Firebase Auth do usuário
    
    Returns:
        True se for desenvolvedor, False caso contrário
    """
    if not uid:
        return False
    
    # 1. Verifica collection usuarios_sistema
    try:
        from ...firebase_config import get_db
        db = get_db()
        
        # Busca usuário pelo firebase_uid
        query = db.collection('usuarios_sistema').where('firebase_uid', '==', uid).limit(1)
        docs = list(query.stream())
        
        if docs:
            usuario = docs[0].to_dict()
            workspaces_colecao = usuario.get('workspaces', [])
            
            # Se tem acesso a visao_geral, é desenvolvedor
            if 'visao_geral' in workspaces_colecao:
                return True
    except Exception as e:
        print(f"Erro ao buscar usuário na coleção usuarios_sistema: {e}")
    
    # 2. Verifica custom_claims do Firebase Auth
    try:
        firebase_user = admin_auth.get_user(uid)
        custom_claims = firebase_user.custom_claims or {}
        
        # Verifica se é admin
        if custom_claims.get('admin') is True or custom_claims.get('role') == 'admin':
            return True
    except Exception as e:
        print(f"Erro ao obter custom_claims do usuário: {e}")
    
    return False


@ui.page('/dev')
def dev():
    """Página principal do Painel do Desenvolvedor."""
    try:
        # Verifica autenticação
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        # Obtém usuário atual
        user = get_current_user()
        if not user:
            ui.navigate.to('/login')
            return
        
        uid = user.get('uid')
        if not uid:
            ui.navigate.to('/login')
            return
        
        # Verifica se é desenvolvedor
        if not _is_developer(uid):
            ui.notify('Acesso negado. Apenas desenvolvedores podem acessar esta página.', type='negative')
            ui.navigate.to('/')
            return
        
        # Renderiza conteúdo
        _render_dev_content()
        
    except Exception as e:
        print(f"Erro na página Desenvolvedor: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f'Erro ao carregar página: {str(e)}', type='negative')


def _render_dev_content():
    """Conteúdo principal da página Desenvolvedor."""
    with layout('Painel do Desenvolvedor', breadcrumbs=[('Desenvolvedor', None)]):
        
        # Título da página
        ui.label('Painel do Desenvolvedor').classes('text-2xl font-bold mb-6')
        
        # Carrega dados
        workspaces = obter_todos_workspaces()
        usuarios = obter_todos_usuarios()
        
        # Card de Workspaces
        card_workspaces(workspaces)
        
        # Card de Usuários
        card_usuarios(usuarios)

