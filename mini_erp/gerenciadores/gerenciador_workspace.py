"""
Gerenciador de estado dos workspaces.
Gerencia alternância, permissões e persistência de workspace ativo.
"""
from typing import Optional, List, Dict
from nicegui import app
from ..auth import get_current_user


# =============================================================================
# DEFINIÇÕES DOS WORKSPACES
# =============================================================================

WORKSPACES = {
    'area_cliente_schmidmeier': {
        'id': 'area_cliente_schmidmeier',
        'nome': 'Área do cliente: Schmidmeier 🇩🇪',
        'prefixo_colecoes': 'schmidmeier_',
        'rota_inicial': '/visao-geral/painel',  # ALTERADO: Agora redireciona para Painel ao invés de '/'
        'icon': 'folder_open'
    },
    'visao_geral_escritorio': {
        'id': 'visao_geral_escritorio',
        'nome': 'Visão geral do escritório',
        'prefixo_colecoes': 'visao_geral_',
        'rota_inicial': '/visao-geral/painel',
        'icon': 'business'
    }
}

# Workspace padrão (fallback)
# ALTERADO: Agora usa 'visao_geral_escritorio' como padrão ao invés de 'area_cliente_schmidmeier'
WORKSPACE_PADRAO = 'visao_geral_escritorio'


# =============================================================================
# FUNÇÕES DE GERENCIAMENTO DE ESTADO
# =============================================================================

def obter_workspace_atual() -> str:
    """
    Retorna o identificador do workspace ativo na sessão atual.
    
    Returns:
        ID do workspace ativo ou workspace padrão se não definido
    """
    workspace = app.storage.user.get('workspace', None)
    
    # Valida se o workspace é válido
    if workspace and workspace in WORKSPACES:
        return workspace
    
    # Retorna workspace padrão
    return WORKSPACE_PADRAO


def definir_workspace(workspace_id: str) -> bool:
    """
    Define o workspace ativo na sessão do usuário.
    
    Args:
        workspace_id: ID do workspace a ser ativado
    
    Returns:
        True se definido com sucesso, False se workspace inválido
    """
    if workspace_id not in WORKSPACES:
        print(f"Erro: Workspace '{workspace_id}' não existe")
        return False
    
    app.storage.user['workspace'] = workspace_id
    
    # Persiste também no localStorage do navegador (via JavaScript)
    from nicegui import ui
    ui.run_javascript(f"""
        try {{
            localStorage.setItem('taques_erp_workspace', '{workspace_id}');
        }} catch(e) {{
            console.log('Erro ao salvar workspace no localStorage:', e);
        }}
    """)
    
    return True


def obter_workspaces_usuario(usuario_id: Optional[str] = None) -> List[str]:
    """
    Retorna lista de workspaces que o usuário tem acesso baseado no perfil.
    
    Primeiro tenta buscar na coleção usuarios_sistema pelo firebase_uid.
    Se não encontrar, usa o sistema antigo de custom_claims.
    
    Args:
        usuario_id: UID do Firebase Auth (opcional, usa usuário atual se None)
    
    Returns:
        Lista de IDs de workspaces disponíveis
    """
    # Se não fornecido, usa usuário atual
    if usuario_id is None:
        user = get_current_user()
        if not user:
            return [WORKSPACE_PADRAO]
        usuario_id = user.get('uid')
    
    if not usuario_id:
        return [WORKSPACE_PADRAO]
    
    # Mapeamento de IDs de workspace da coleção para IDs do sistema
    MAPEAMENTO_WORKSPACES = {
        'schmidmeier': 'area_cliente_schmidmeier',
        'visao_geral': 'visao_geral_escritorio',
    }
    
    # Tenta buscar na coleção usuarios_sistema primeiro
    try:
        from ..firebase_config import get_db
        db = get_db()
        
        # Busca usuário pelo firebase_uid
        query = db.collection('usuarios_sistema').where('firebase_uid', '==', usuario_id).limit(1)
        docs = list(query.stream())
        
        if docs:
            usuario = docs[0].to_dict()
            workspaces_colecao = usuario.get('workspaces', [])
            
            # Converte IDs da coleção para IDs do sistema
            workspaces_sistema = []
            for ws_id in workspaces_colecao:
                ws_sistema = MAPEAMENTO_WORKSPACES.get(ws_id)
                if ws_sistema and ws_sistema in WORKSPACES:
                    workspaces_sistema.append(ws_sistema)
            
            if workspaces_sistema:
                return workspaces_sistema
    except Exception as e:
        print(f"Erro ao buscar usuário na coleção usuarios_sistema: {e}")
    
    # Fallback: usa sistema antigo de custom_claims
    from ..auth import get_user_profile
    profile = get_user_profile()
    
    # Perfil "cliente" → apenas workspace do cliente
    if profile == 'cliente':
        return ['area_cliente_schmidmeier']
    
    # Perfil "interno" ou "df_projetos" → ambos workspaces
    if profile in ['interno', 'df_projetos']:
        return ['area_cliente_schmidmeier', 'visao_geral_escritorio']
    
    # Se é admin (custom_claims), retorna todos
    user = get_current_user()
    if user:
        from firebase_admin import auth
        try:
            firebase_user = auth.get_user(usuario_id)
            custom_claims = firebase_user.custom_claims or {}
            if custom_claims.get('admin') or custom_claims.get('role') == 'admin':
                return ['area_cliente_schmidmeier', 'visao_geral_escritorio']
        except:
            pass
    
    # Default: apenas workspace do cliente (segurança)
    return [WORKSPACE_PADRAO]


def verificar_acesso_workspace(usuario_id: Optional[str] = None, workspace_id: str = None) -> bool:
    """
    Verifica se o usuário tem permissão para acessar um workspace específico.
    
    Args:
        usuario_id: ID do usuário (opcional, usa usuário atual se None)
        workspace_id: ID do workspace a verificar (opcional, usa workspace atual se None)
    
    Returns:
        True se tem acesso, False caso contrário
    """
    # Se não fornecido, usa workspace atual
    if workspace_id is None:
        workspace_id = obter_workspace_atual()
    
    # Valida se workspace existe
    if workspace_id not in WORKSPACES:
        return False
    
    # Obtém workspaces disponíveis para o usuário
    workspaces_disponiveis = obter_workspaces_usuario(usuario_id)
    
    # Verifica se workspace está na lista de disponíveis
    return workspace_id in workspaces_disponiveis


def obter_info_workspace(workspace_id: Optional[str] = None) -> Optional[Dict]:
    """
    Retorna informações completas de um workspace.
    
    Args:
        workspace_id: ID do workspace (opcional, usa workspace atual se None)
    
    Returns:
        Dicionário com informações do workspace ou None se inválido
    """
    if workspace_id is None:
        workspace_id = obter_workspace_atual()
    
    return WORKSPACES.get(workspace_id)


def carregar_workspace_persistido() -> str:
    """
    Carrega workspace salvo no localStorage ou retorna padrão.
    Usado ao fazer login ou refresh da página.
    
    Returns:
        ID do workspace a ser usado
    """
    # Tenta carregar da sessão NiceGUI primeiro
    workspace = app.storage.user.get('workspace', None)
    if workspace and workspace in WORKSPACES:
        # Valida se usuário ainda tem acesso
        if verificar_acesso_workspace(workspace_id=workspace):
            return workspace
    
    # Se não encontrado na sessão ou sem acesso, tenta carregar do localStorage
    # Nota: localStorage é acessado via JavaScript no cliente, então aqui
    # apenas retornamos o padrão. O JavaScript pode sincronizar depois.
    # Em produção, você pode fazer uma chamada AJAX para sincronizar.
    
    # Verifica se usuário tem acesso ao workspace padrão
    if verificar_acesso_workspace(workspace_id=WORKSPACE_PADRAO):
        return WORKSPACE_PADRAO
    
    # Se não tem acesso ao padrão, retorna primeiro workspace disponível
    workspaces_disponiveis = obter_workspaces_usuario()
    if workspaces_disponiveis:
        return workspaces_disponiveis[0]
    
    return WORKSPACE_PADRAO


def alternar_workspace(workspace_id: str, verificar_permissao: bool = True) -> bool:
    """
    Alterna para um workspace específico, verificando permissões.
    
    Args:
        workspace_id: ID do workspace desejado
        verificar_permissao: Se True, verifica permissão antes de alternar
    
    Returns:
        True se alternou com sucesso, False caso contrário
    """
    # Verifica permissão se solicitado
    if verificar_permissao:
        if not verificar_acesso_workspace(workspace_id=workspace_id):
            print(f"Erro: Usuário não tem permissão para acessar workspace '{workspace_id}'")
            return False
    
    # Define novo workspace
    return definir_workspace(workspace_id)

