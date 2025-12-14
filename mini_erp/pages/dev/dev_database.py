"""
Operações de banco de dados para o módulo Desenvolvedor.
Funções para consultas e manipulação de dados do Firestore.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from ...firebase_config import get_db
from firebase_admin import auth as admin_auth
from ...gerenciadores.gerenciador_workspace import WORKSPACES


def obter_todos_workspaces() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os workspaces configurados no sistema.
    
    Returns:
        Lista de dicionários com: id, nome, prefixo_colecoes, icon
    """
    workspaces = []
    for workspace_id, workspace_info in WORKSPACES.items():
        workspaces.append({
            'id': workspace_info.get('id'),
            'nome': workspace_info.get('nome'),
            'prefixo_colecoes': workspace_info.get('prefixo_colecoes'),
            'icon': workspace_info.get('icon'),
            'rota_inicial': workspace_info.get('rota_inicial')
        })
    return workspaces


def obter_todos_usuarios() -> List[Dict[str, Any]]:
    """
    Busca todos os usuários cadastrados no sistema.
    
    Combina dados da collection 'usuarios_sistema' com dados do Firebase Auth.
    
    Returns:
        Lista de dicionários com informações completas dos usuários:
        - nome_completo
        - email
        - nivel_acesso (Administrador ou Cliente)
        - ultimo_login (formatado ou '-')
        - workspaces (lista de nomes dos workspaces)
    """
    usuarios = []
    
    try:
        db = get_db()
        
        # Busca todos os documentos da collection usuarios_sistema
        docs = db.collection('usuarios_sistema').stream()
        
        # Mapeamento de IDs da coleção para nomes dos workspaces
        MAPEAMENTO_WORKSPACES_NOMES = {
            'schmidmeier': 'Área do cliente: Schmidmeier',
            'visao_geral': 'Visão geral do escritório'
        }
        
        for doc in docs:
            usuario_data = doc.to_dict()
            firebase_uid = usuario_data.get('firebase_uid')
            nome_completo = usuario_data.get('nome_completo', 'Sem nome')
            workspaces_colecao = usuario_data.get('workspaces', [])
            
            # Inicializa dados do usuário
            usuario_info = {
                'nome_completo': nome_completo,
                'email': '-',
                'nivel_acesso': 'Cliente',
                'ultimo_login': '-',
                'workspaces': []
            }
            
            # Busca dados do Firebase Auth se tiver firebase_uid
            if firebase_uid:
                try:
                    firebase_user = admin_auth.get_user(firebase_uid)
                    
                    # Email
                    usuario_info['email'] = firebase_user.email or '-'
                    
                    # Último login
                    if firebase_user.user_metadata and firebase_user.user_metadata.last_sign_in_timestamp:
                        timestamp_ms = firebase_user.user_metadata.last_sign_in_timestamp
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        usuario_info['ultimo_login'] = dt.strftime('%d/%m/%Y %H:%M')
                    
                    # Verifica custom_claims para nível de acesso
                    custom_claims = firebase_user.custom_claims or {}
                    if custom_claims.get('admin') is True or custom_claims.get('role') == 'admin':
                        usuario_info['nivel_acesso'] = 'Administrador'
                    
                except Exception as e:
                    print(f"Erro ao buscar dados do Firebase Auth para UID {firebase_uid}: {e}")
                    # Continua com dados da collection mesmo se Firebase Auth falhar
            
            # Determina nível de acesso baseado nos workspaces
            if 'visao_geral' in workspaces_colecao:
                usuario_info['nivel_acesso'] = 'Administrador'
            
            # Converte IDs de workspaces para nomes
            for ws_id in workspaces_colecao:
                nome_workspace = MAPEAMENTO_WORKSPACES_NOMES.get(ws_id)
                if nome_workspace:
                    usuario_info['workspaces'].append(nome_workspace)
            
            usuarios.append(usuario_info)
        
        # Ordena por nome_completo
        usuarios.sort(key=lambda x: x['nome_completo'].lower())
        
    except Exception as e:
        print(f"Erro ao obter usuários: {e}")
        import traceback
        traceback.print_exc()
    
    return usuarios
