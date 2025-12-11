"""
Sistema de autenticação com Firebase Auth
"""
import requests
from nicegui import app, ui
from functools import wraps
from firebase_admin import auth as admin_auth
from typing import Optional, List

# Configuração do Firebase Auth REST API
FIREBASE_API_KEY = "AIzaSyB5AmzmzdqBJ3WHSV8hiqKxdOf6wCM-Ol4"
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

def login_user(email: str, password: str) -> dict:
    """
    Autentica usuário com email e senha via Firebase Auth.
    Retorna dict com 'success', 'message' e 'user' (se sucesso).
    """
    try:
        response = requests.post(FIREBASE_AUTH_URL, json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        })
        
        data = response.json()
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Login realizado com sucesso!",
                "user": {
                    "email": data.get("email"),
                    "uid": data.get("localId"),
                    "token": data.get("idToken"),
                    "refresh_token": data.get("refreshToken")
                }
            }
        else:
            error_message = data.get("error", {}).get("message", "Erro desconhecido")
            
            # Traduz mensagens de erro comuns
            error_translations = {
                "EMAIL_NOT_FOUND": "Email não encontrado",
                "INVALID_PASSWORD": "Senha incorreta", 
                "INVALID_LOGIN_CREDENTIALS": "Email ou senha incorretos",
                "USER_DISABLED": "Usuário desativado",
                "TOO_MANY_ATTEMPTS_TRY_LATER": "Muitas tentativas. Tente novamente mais tarde."
            }
            
            return {
                "success": False,
                "message": error_translations.get(error_message, f"Erro: {error_message}"),
                "user": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro de conexão: {str(e)}",
            "user": None
        }

def get_current_user():
    """Retorna o usuário logado da sessão atual."""
    return app.storage.user.get('user', None)

def is_authenticated() -> bool:
    """Verifica se há um usuário autenticado na sessão."""
    return get_current_user() is not None

def logout_user():
    """Remove o usuário da sessão (logout)."""
    app.storage.user.pop('user', None)

def logout_e_reiniciar():
    """
    Desloga o usuário e reinicia a aplicação completa
    Limpa cache, sessionStorage, localStorage e volta à tela de login
    """
    try:
        # 1. Limpar dados da sessão
        app.storage.user.pop('user', None)
        
        # 2. Limpar cache do navegador via JavaScript
        ui.run_javascript("""
        // Limpar localStorage
        localStorage.clear();
        
        // Limpar sessionStorage
        sessionStorage.clear();
        
        // Limpar cookies
        document.cookie.split(";").forEach(function(c) {
            document.cookie = c
                .replace(/^ +/, "")
                .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });
        
        // Redirecionar para login
        window.location.href = '/login';
        
        // Força reload após 500ms (sem cache)
        setTimeout(function() {
            window.location.reload(true);
        }, 500);
        """)
        
        return True
    except Exception as e:
        print(f"Erro ao fazer logout e reiniciar: {e}")
        return False

def fazer_logout_com_notificacao():
    """Logout com notificação e delay para garantir execução"""
    try:
        # Mostrar notificação
        ui.notify('🔄 Reiniciando sistema...', type='info')
        
        # Limpar dados da sessão
        app.storage.user.pop('user', None)
        
        # Executar limpeza e reload
        ui.run_javascript("""
        // Limpar tudo
        localStorage.clear();
        sessionStorage.clear();
        
        // Aguardar 300ms e redirecionar
        setTimeout(function() {
            window.location.href = '/login';
        }, 300);
        
        // Força reload após 800ms
        setTimeout(function() {
            window.location.reload(true);
        }, 800);
        """)
        
        return True
    except Exception as e:
        print(f"Erro ao fazer logout: {e}")
        return False

def require_auth(func):
    """
    Decorator para proteger páginas que requerem autenticação.
    Redireciona para /login se não autenticado.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# SISTEMA DE WORKSPACES (DEPRECATED - usar gerenciador_workspace)
# =============================================================================
# Mantido para compatibilidade. Use gerenciadores.gerenciador_workspace para novas implementações.

def get_user_profile() -> Optional[str]:
    """
    Obtém o perfil do usuário atual via Firebase Auth custom_claims.
    
    Returns:
        Perfil do usuário: 'cliente', 'interno', 'df_projetos' ou None
    """
    try:
        user = get_current_user()
        if not user:
            return None
        
        uid = user.get('uid')
        if not uid:
            return None
        
        # Busca custom_claims do Firebase Auth
        firebase_user = admin_auth.get_user(uid)
        custom_claims = firebase_user.custom_claims or {}
        
        # Tenta obter perfil de diferentes campos possíveis
        perfil = custom_claims.get('perfil') or custom_claims.get('role') or custom_claims.get('profile')
        
        # Normaliza valores
        if perfil:
            perfil = perfil.lower()
            # Mapeia variações possíveis
            if perfil in ['cliente', 'client']:
                return 'cliente'
            elif perfil in ['interno', 'internal', 'admin']:
                return 'interno'
            elif perfil in ['df_projetos', 'df-projetos', 'projetos']:
                return 'df_projetos'
        
        return None
    except Exception as e:
        print(f"Erro ao obter perfil do usuário: {e}")
        return None


def get_user_workspaces(profile: Optional[str] = None) -> List[str]:
    """
    DEPRECATED: Use gerenciadores.gerenciador_workspace.obter_workspaces_usuario()
    
    Retorna lista de workspaces que o usuário tem acesso baseado no perfil.
    """
    from .gerenciadores.gerenciador_workspace import obter_workspaces_usuario
    return obter_workspaces_usuario()


def get_current_workspace() -> str:
    """
    DEPRECATED: Use gerenciadores.gerenciador_workspace.obter_workspace_atual()
    
    Retorna o workspace atual da sessão do usuário.
    """
    from .gerenciadores.gerenciador_workspace import obter_workspace_atual
    return obter_workspace_atual()


def set_current_workspace(workspace_id: str):
    """
    DEPRECATED: Use gerenciadores.gerenciador_workspace.definir_workspace()
    
    Define o workspace atual na sessão do usuário.
    """
    from .gerenciadores.gerenciador_workspace import definir_workspace
    definir_workspace(workspace_id)




