"""
Operações de banco de dados para o módulo Desenvolvedor.
Funções para consultas e manipulação de dados do Firestore.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from ...firebase_config import get_db
from firebase_admin import auth as admin_auth
from ...gerenciadores.gerenciador_workspace import WORKSPACES


def _determinar_nivel_acesso_fallback(custom_claims: Dict[str, Any]) -> str:
    """
    Determina o nível de acesso baseado em custom_claims quando nivel_display não existe.
    
    Lógica de fallback:
    - Se admin=True e desenvolvedor=True → "Desenvolvedor"
    - Se tipo_usuario='interno' → "Usuário Interno"
    - Se tipo_usuario='externo' → "Usuário Externo"
    - Fallback final → "Usuário"
    
    Args:
        custom_claims: Dicionário com custom claims do Firebase Auth
    
    Returns:
        String com o nível de acesso
    """
    if not custom_claims:
        return 'Usuário'
    
    # Verifica se é desenvolvedor (admin=True e desenvolvedor=True)
    if custom_claims.get('admin') is True and custom_claims.get('desenvolvedor') is True:
        return 'Desenvolvedor'
    
    # Verifica tipo_usuario
    tipo_usuario = custom_claims.get('tipo_usuario', '').lower()
    if tipo_usuario == 'interno':
        return 'Usuário Interno'
    elif tipo_usuario == 'externo':
        return 'Usuário Externo'
    
    # Fallback final
    return 'Usuário'


def obter_todos_workspaces() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os workspaces configurados no sistema, ordenados pelo campo 'ordem'.
    
    Returns:
        Lista de dicionários com: id, nome, prefixo_colecoes, icon, ordem
    """
    from ...gerenciadores.gerenciador_workspace import obter_workspaces_ordenados
    
    # Obtém workspaces ordenados
    workspace_ids_ordenados = obter_workspaces_ordenados()
    
    workspaces = []
    for workspace_id in workspace_ids_ordenados:
        workspace_info = WORKSPACES.get(workspace_id)
        if workspace_info:
            workspaces.append({
                'id': workspace_info.get('id'),
                'nome': workspace_info.get('nome'),
                'prefixo_colecoes': workspace_info.get('prefixo_colecoes'),
                'icon': workspace_info.get('icon'),
                'rota_inicial': workspace_info.get('rota_inicial'),
                'ordem': workspace_info.get('ordem', 999)
            })
    return workspaces


def obter_todos_usuarios() -> List[Dict[str, Any]]:
    """
    Busca todos os usuários cadastrados no sistema.
    
    FONTE PRINCIPAL: Firebase Authentication
    COMPLEMENTO: Collection usuarios_sistema (workspaces, perfil)
    
    Returns:
        Lista de dicionários com informações completas dos usuários:
        - nome_completo: display_name ou custom_claims ou email
        - email: do Firebase Auth (nunca vazio)
        - nivel_acesso: 'Administrador' ou 'Usuário'
        - ultimo_login: formatado (DD/MM/YYYY HH:MM) ou '-'
        - workspaces: lista de nomes dos workspaces ou ['Não vinculado']
        - firebase_uid: UID do Firebase
        - vinculado: True se existe em usuarios_sistema, False se não
        - status: 'Ativo' ou 'Desativado'
        - sem_firebase: True se é usuário órfão (só em usuarios_sistema)
    """
    usuarios = []
    usuarios_por_uid = {}  # Cache para evitar consultas duplicadas
    
    # Mapeamento de IDs da coleção para nomes dos workspaces
    MAPEAMENTO_WORKSPACES_NOMES = {
        'schmidmeier': 'Área do cliente: Schmidmeier',
        'visao_geral': 'Visão geral do escritório',
        'df_taques': 'Parceria - DF/Taques 🤝'
    }
    
    try:
        # ============================================================
        # ETAPA 1: Buscar TODOS os usuários do Firebase Auth
        # ============================================================
        db = get_db()
        
        # Carrega todos os registros de usuarios_sistema em memória (otimização)
        usuarios_sistema_map = {}  # {firebase_uid: usuario_data}
        usuarios_sistema_sem_uid = []  # Usuários sem firebase_uid
        
        try:
            docs_usuarios_sistema = db.collection('usuarios_sistema').stream()
            for doc in docs_usuarios_sistema:
                usuario_data = doc.to_dict()
                firebase_uid = usuario_data.get('firebase_uid')
                
                if firebase_uid:
                    usuarios_sistema_map[firebase_uid] = usuario_data
                else:
                    # Usuário órfão (sem Firebase Auth)
                    usuarios_sistema_sem_uid.append(usuario_data)
        except Exception as e:
            print(f"Erro ao buscar usuarios_sistema: {e}")
        
        # Lista todos os usuários do Firebase Auth
        try:
            page = admin_auth.list_users()
            
            while page:
                for firebase_user in page.users:
                    uid = firebase_user.uid
                    email = firebase_user.email or ''
                    
                    # Inicializa dados do usuário
                    usuario_info = {
                        'firebase_uid': uid,
                        'email': email,
                        'status': 'Desativado' if firebase_user.disabled else 'Ativo',
                        'vinculado': False,
                        'workspaces': [],
                        'nivel_acesso': 'Usuário',
                        'ultimo_login': '-',
                        'sem_firebase': False
                    }
                    
                    # Nome completo: display_name > custom_claims > email
                    if firebase_user.display_name:
                        usuario_info['nome_completo'] = firebase_user.display_name
                    else:
                        custom_claims = firebase_user.custom_claims or {}
                        display_name = custom_claims.get('display_name')
                        if display_name:
                            usuario_info['nome_completo'] = display_name
                        else:
                            # Fallback: parte do email antes do @
                            usuario_info['nome_completo'] = email.split('@')[0] if email else 'Sem nome'
                    
                    # Último login
                    if firebase_user.user_metadata and firebase_user.user_metadata.last_sign_in_timestamp:
                        timestamp_ms = firebase_user.user_metadata.last_sign_in_timestamp
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        usuario_info['ultimo_login'] = dt.strftime('%d/%m/%Y %H:%M')
                    
                    # Busca dados complementares em usuarios_sistema
                    custom_claims = firebase_user.custom_claims or {}
                    
                    if uid in usuarios_sistema_map:
                        usuario_sistema = usuarios_sistema_map[uid]
                        usuario_info['vinculado'] = True
                        
                        # Workspaces
                        workspaces_colecao = usuario_sistema.get('workspaces', [])
                        for ws_id in workspaces_colecao:
                            nome_workspace = MAPEAMENTO_WORKSPACES_NOMES.get(ws_id)
                            if nome_workspace:
                                usuario_info['workspaces'].append(nome_workspace)
                        
                        # Se não tem workspaces, marca como não vinculado
                        if not usuario_info['workspaces']:
                            usuario_info['workspaces'] = ['Não vinculado']
                        
                        # Nível de acesso: usa nivel_display de usuarios_sistema se existir
                        nivel_display = usuario_sistema.get('nivel_display')
                        if nivel_display:
                            usuario_info['nivel_acesso'] = nivel_display
                        else:
                            # Fallback baseado em custom_claims
                            usuario_info['nivel_acesso'] = _determinar_nivel_acesso_fallback(custom_claims)
                    else:
                        # Usuário do Firebase Auth sem registro em usuarios_sistema
                        usuario_info['workspaces'] = ['Não vinculado']
                        # Fallback baseado em custom_claims
                        usuario_info['nivel_acesso'] = _determinar_nivel_acesso_fallback(custom_claims)
                    
                    usuarios.append(usuario_info)
                    usuarios_por_uid[uid] = usuario_info
                
                # Próxima página
                try:
                    page = page.get_next_page()
                except StopIteration:
                    break
                except Exception:
                    break
                    
        except Exception as e:
            print(f"Erro ao listar usuários do Firebase Auth: {e}")
            import traceback
            traceback.print_exc()
        
        # ============================================================
        # ETAPA 2: Adicionar usuários órfãos (só em usuarios_sistema)
        # ============================================================
        for usuario_sistema in usuarios_sistema_sem_uid:
            nome_completo = usuario_sistema.get('nome_completo', 'Sem nome')
            workspaces_colecao = usuario_sistema.get('workspaces', [])
            
            # Converte workspaces para nomes
            workspaces_nomes = []
            for ws_id in workspaces_colecao:
                nome_workspace = MAPEAMENTO_WORKSPACES_NOMES.get(ws_id)
                if nome_workspace:
                    workspaces_nomes.append(nome_workspace)
            
            if not workspaces_nomes:
                workspaces_nomes = ['Não vinculado']
            
            # Nível de acesso: usa nivel_display de usuarios_sistema se existir
            nivel_display = usuario_sistema.get('nivel_display')
            if nivel_display:
                nivel_acesso = nivel_display
            else:
                # Fallback: se tem visao_geral, é Administrador, senão Usuário
                nivel_acesso = 'Administrador' if 'visao_geral' in workspaces_colecao else 'Usuário'
            
            usuario_info = {
                'nome_completo': nome_completo,
                'email': usuario_sistema.get('email', '-'),
                'firebase_uid': '-',
                'status': 'Sem login',
                'vinculado': False,
                'workspaces': workspaces_nomes,
                'nivel_acesso': nivel_acesso,
                'ultimo_login': '-',
                'sem_firebase': True  # Flag para destacar visualmente
            }
            
            usuarios.append(usuario_info)
        
        # Ordena por nome_completo
        usuarios.sort(key=lambda x: x.get('nome_completo', '').lower())
        
    except Exception as e:
        print(f"Erro ao obter usuários: {e}")
        import traceback
        traceback.print_exc()
    
    return usuarios
