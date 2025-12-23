"""Painel de Desenvolvedor - Interface administrativa com abas."""
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated, get_current_user
from ..dev.dev_database import obter_todos_workspaces, obter_todos_usuarios
from ..dev.dev_components import card_workspaces, card_usuarios


def _is_developer(uid: str) -> bool:
    """Verifica se o usuário é desenvolvedor/administrador."""
    if not uid:
        return False
    
    try:
        from ...firebase_config import get_db
        db = get_db()
        query = db.collection('usuarios_sistema').where('firebase_uid', '==', uid).limit(1)
        docs = list(query.stream())
        
        if docs:
            usuario = docs[0].to_dict()
            workspaces_colecao = usuario.get('workspaces', [])
            if 'visao_geral' in workspaces_colecao:
                return True
    except Exception:
        pass
    
    return False


@ui.page('/developer')
def developer_page():
    """Painel do Desenvolvedor com abas."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    user = get_current_user()
    if not user:
        ui.navigate.to('/login')
        return
    
    uid = user.get('uid')
    if not uid:
        ui.navigate.to('/login')
        return
    
    if not _is_developer(uid):
        ui.notify('Acesso negado. Apenas desenvolvedores podem acessar esta página.', type='negative')
        ui.navigate.to('/')
        return
    
    with layout('Painel do Desenvolvedor', breadcrumbs=[('Dev', None)]):
        ui.label('🛠️ Painel do Desenvolvedor').classes('text-3xl font-bold mb-6')
        
        # Sistema de abas minimalista
        with ui.tabs().classes('w-full border-b') as tabs:
            tab_workspaces = ui.tab('📦 Workspaces')
            tab_usuarios = ui.tab('👥 Usuários')
            tab_migracao = ui.tab('🔄 Migração')
        
        # Painéis das abas
        with ui.tab_panels(tabs, value=tab_workspaces).classes('w-full bg-transparent'):
            
            # ========== ABA WORKSPACES ==========
            with ui.tab_panel(tab_workspaces):
                render_aba_workspaces()
            
            # ========== ABA USUÁRIOS ==========
            with ui.tab_panel(tab_usuarios):
                render_aba_usuarios()
            
            # ========== ABA MIGRAÇÃO ==========
            with ui.tab_panel(tab_migracao):
                render_aba_migracao()


def render_aba_workspaces():
    """Renderiza aba de workspaces."""
    try:
        workspaces = obter_todos_workspaces()
        card_workspaces(workspaces)
    except Exception as e:
        ui.label(f'Erro ao carregar workspaces: {str(e)}').classes('text-red-500')


def render_aba_usuarios():
    """Renderiza aba de usuários."""
    try:
        # Usa a função segura que criamos para evitar crash do gRPC
        usuarios = obter_todos_usuarios()
        card_usuarios(usuarios)
    except Exception as e:
        ui.label(f'Erro ao carregar usuários: {str(e)}').classes('text-red-500')


def render_aba_migracao():
    """Renderiza aba de migração de processos."""
    # Importar interface de migração do arquivo administrativo
    from ..admin.admin_migracao_processos import render_migracao_interface
    render_migracao_interface()

