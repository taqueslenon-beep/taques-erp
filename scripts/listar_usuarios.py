#!/usr/bin/env python3
"""Script para listar todos os usuários do Firebase Authentication."""

import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_admin import auth
from mini_erp.firebase_config import get_db, init_firebase
from datetime import datetime

def format_timestamp(ts):
    """Formata timestamp em data legível."""
    if not ts:
        return '-'
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts / 1000)
            return dt.strftime('%d/%m/%Y %H:%M')
        return str(ts)
    except:
        return '-'

def listar_usuarios():
    """Lista todos os usuários do Firebase Auth."""
    print("\n" + "="*80)
    print("RELATÓRIO DE USUÁRIOS - TAQUES ERP")
    print("="*80 + "\n")
    
    # Inicializa Firebase
    try:
        init_firebase()
    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")
        return []
    
    usuarios = []
    
    try:
        # Itera sobre todos os usuários
        page = auth.list_users()
        
        while page:
            for user in page.users:
                custom_claims = user.custom_claims or {}
                
                # Determina função/perfil
                role = 'Usuário'
                if custom_claims.get('admin') or custom_claims.get('role') == 'admin':
                    role = 'Administrador'
                elif custom_claims.get('role'):
                    role = custom_claims.get('role')
                
                # Determina acesso a workspaces
                perfil_workspace = custom_claims.get('perfil', 'indefinido')
                
                # Normaliza perfil para determinar acesso
                perfil_normalizado = None
                if perfil_workspace and perfil_workspace != 'indefinido':
                    perfil_lower = perfil_workspace.lower()
                    if perfil_lower in ['cliente', 'client']:
                        perfil_normalizado = 'cliente'
                    elif perfil_lower in ['interno', 'internal', 'admin']:
                        perfil_normalizado = 'interno'
                    elif perfil_lower in ['df_projetos', 'df-projetos', 'projetos']:
                        perfil_normalizado = 'df_projetos'
                
                # Determina workspaces disponíveis baseado no perfil
                workspaces_acesso = []
                if perfil_normalizado == 'cliente':
                    workspaces_acesso = ['area_cliente_schmidmeier']
                elif perfil_normalizado in ['interno', 'df_projetos']:
                    workspaces_acesso = ['area_cliente_schmidmeier', 'visao_geral_escritorio']
                else:
                    # Se não tem perfil definido, verifica se é admin
                    if custom_claims.get('admin') or role == 'Administrador':
                        workspaces_acesso = ['area_cliente_schmidmeier', 'visao_geral_escritorio']
                    else:
                        workspaces_acesso = ['area_cliente_schmidmeier']  # Padrão seguro
                
                usuarios.append({
                    'email': user.email,
                    'uid': user.uid,
                    'role': role,
                    'perfil_workspace': perfil_workspace,
                    'perfil_normalizado': perfil_normalizado or 'sem perfil definido',
                    'workspaces_acesso': workspaces_acesso,
                    'custom_claims': custom_claims,
                    'criacao': format_timestamp(user.user_metadata.creation_timestamp),
                    'ultimo_login': format_timestamp(user.user_metadata.last_sign_in_timestamp),
                    'status': 'Inativo' if user.disabled else 'Ativo',
                })
            
            page = page.get_next_page()
        
        # Exibe relatório
        print(f"Total de usuários: {len(usuarios)}\n")
        print("-"*80)
        
        for i, u in enumerate(usuarios, 1):
            print(f"\n[{i}] {u['email']}")
            print(f"    UID: {u['uid']}")
            print(f"    Função: {u['role']}")
            print(f"    Perfil Workspace (raw): {u['perfil_workspace']}")
            print(f"    Perfil Normalizado: {u['perfil_normalizado']}")
            print(f"    Workspaces com Acesso: {', '.join(u['workspaces_acesso'])}")
            print(f"    Custom Claims: {u['custom_claims']}")
            print(f"    Criação: {u['criacao']}")
            print(f"    Último Login: {u['ultimo_login']}")
            print(f"    Status: {u['status']}")
        
        # Resumo por perfil
        print("\n" + "="*80)
        print("RESUMO POR PERFIL DE WORKSPACE")
        print("="*80 + "\n")
        
        perfis_count = {}
        for u in usuarios:
            perfil = u['perfil_normalizado']
            perfis_count[perfil] = perfis_count.get(perfil, 0) + 1
        
        for perfil, count in sorted(perfis_count.items()):
            print(f"  {perfil}: {count} usuário(s)")
        
        # Lista de emails
        print("\n" + "="*80)
        print("LISTA DE EMAILS")
        print("="*80 + "\n")
        for u in usuarios:
            print(f"  - {u['email']} ({u['perfil_normalizado']})")
        
        print("\n" + "="*80)
        print("FIM DO RELATÓRIO")
        print("="*80 + "\n")
        
        return usuarios
        
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    listar_usuarios()




