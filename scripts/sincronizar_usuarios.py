#!/usr/bin/env python3
"""
Script de Sincronização e Limpeza de Usuários
==============================================

Este script sincroniza usuários entre Firebase Authentication e a collection usuarios_sistema,
resolvendo duplicatas e garantindo consistência dos dados.

Funcionalidades:
- Lista todos os usuários do Firebase Auth
- Sincroniza com usuarios_sistema (atualiza ou cria registros)
- Identifica registros órfãos (sem Firebase Auth)
- Define workspaces e perfis por usuário
- Faz backup antes de modificar dados

Uso:
    python scripts/sincronizar_usuarios.py

Requisitos:
    - Variáveis de ambiente do Firebase configuradas
    - Ou arquivo firebase-credentials.json no diretório raiz
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_admin import auth
from mini_erp.firebase_config import get_db, init_firebase


# =============================================================================
# CONFIGURAÇÕES DE USUÁRIOS
# =============================================================================

# Mapeamento de emails para workspaces e perfis
CONFIGURACAO_USUARIOS = {
    'taqueslenon@gmail.com': {
        'workspaces': ['schmidmeier', 'visao_geral', 'df_taques'],
        'perfil': 'interno',
        'nome_completo': 'Lenon Taques'
    },
    'bernataques@gmail.com': {
        'workspaces': ['schmidmeier', 'visao_geral', 'df_taques'],
        'perfil': 'interno',
        'nome_completo': 'Berna Taques'
    },
    'taquesgiba@gmail.com': {
        'workspaces': ['schmidmeier', 'visao_geral', 'df_taques'],
        'perfil': 'interno',
        'nome_completo': 'Gilberto Taques'
    },
    'douglasmarco@gmail.com': {
        'workspaces': ['schmidmeier', 'df_taques'],
        'perfil': 'parceiro',
        'nome_completo': 'Douglas Marco'
    },
    'flaviana.friedrich@gmail.com': {
        'workspaces': ['schmidmeier', 'df_taques'],
        'perfil': 'parceiro',
        'nome_completo': 'Flaviana Friedrich'
    }
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def formatar_timestamp(timestamp_ms: Optional[int]) -> str:
    """Formata timestamp em string legível."""
    if not timestamp_ms:
        return datetime.now().isoformat()
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.isoformat()
    except:
        return datetime.now().isoformat()


def fazer_backup(usuarios_sistema: List[Dict[str, Any]], caminho_backup: str) -> bool:
    """
    Faz backup dos dados atuais de usuarios_sistema.
    
    Args:
        usuarios_sistema: Lista de documentos da collection
        caminho_backup: Caminho do arquivo de backup
    
    Returns:
        True se backup foi criado com sucesso
    """
    try:
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'total_registros': len(usuarios_sistema),
            'registros': usuarios_sistema
        }
        
        with open(caminho_backup, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup criado: {caminho_backup}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False


def obter_usuarios_firebase_auth() -> Dict[str, Any]:
    """
    Lista todos os usuários do Firebase Authentication.
    
    Returns:
        Dicionário {email: firebase_user}
    """
    usuarios_auth = {}
    
    try:
        page = auth.list_users()
        
        while page:
            for user in page.users:
                email = user.email
                if email:
                    usuarios_auth[email.lower()] = user
            
            try:
                page = page.get_next_page()
            except StopIteration:
                break
            except Exception:
                break
        
        print(f"📋 Encontrados {len(usuarios_auth)} usuários no Firebase Auth")
        return usuarios_auth
        
    except Exception as e:
        print(f"❌ Erro ao listar usuários do Firebase Auth: {e}")
        import traceback
        traceback.print_exc()
        return {}


def obter_usuarios_sistema() -> List[Dict[str, Any]]:
    """
    Busca todos os registros da collection usuarios_sistema.
    
    Returns:
        Lista de documentos com seus IDs
    """
    usuarios_sistema = []
    
    try:
        db = get_db()
        docs = db.collection('usuarios_sistema').stream()
        
        for doc in docs:
            data = doc.to_dict()
            data['_doc_id'] = doc.id
            usuarios_sistema.append(data)
        
        print(f"📋 Encontrados {len(usuarios_sistema)} registros em usuarios_sistema")
        return usuarios_sistema
        
    except Exception as e:
        print(f"❌ Erro ao buscar usuarios_sistema: {e}")
        import traceback
        traceback.print_exc()
        return []


def encontrar_registro_por_uid(usuarios_sistema: List[Dict], firebase_uid: str) -> Optional[Dict]:
    """Encontra registro em usuarios_sistema pelo firebase_uid."""
    for usuario in usuarios_sistema:
        if usuario.get('firebase_uid') == firebase_uid:
            return usuario
    return None


def encontrar_registro_por_email(usuarios_sistema: List[Dict], email: str) -> Optional[Dict]:
    """Encontra registro em usuarios_sistema pelo email."""
    email_lower = email.lower()
    for usuario in usuarios_sistema:
        usuario_email = usuario.get('email', '').lower()
        if usuario_email == email_lower:
            return usuario
    return None


def criar_registro_usuario(
    firebase_user: Any,
    config_usuario: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Cria estrutura de registro para usuarios_sistema.
    
    Args:
        firebase_user: Objeto UserRecord do Firebase Auth
        config_usuario: Configuração específica do usuário (workspaces, perfil)
    
    Returns:
        Dicionário com dados do registro
    """
    email = firebase_user.email or ''
    nome_completo = firebase_user.display_name or ''
    
    # Usa configuração específica se disponível
    if config_usuario:
        nome_completo = config_usuario.get('nome_completo', nome_completo)
        workspaces = config_usuario.get('workspaces', [])
        perfil = config_usuario.get('perfil', 'cliente')
    else:
        # Fallback: extrai nome do email ou usa email
        if not nome_completo:
            nome_completo = email.split('@')[0] if email else 'Sem nome'
        workspaces = []
        perfil = 'cliente'
    
    # Se não tem nome completo, tenta custom_claims
    if not nome_completo:
        custom_claims = firebase_user.custom_claims or {}
        nome_completo = custom_claims.get('display_name', nome_completo)
    
    registro = {
        'nome_completo': nome_completo,
        'email': email,
        'firebase_uid': firebase_user.uid,
        'perfil': perfil,
        'workspaces': workspaces,
        'ativo': not firebase_user.disabled,
        'created_at': formatar_timestamp(firebase_user.user_metadata.creation_timestamp),
        'updated_at': datetime.now().isoformat()
    }
    
    return registro


def atualizar_registro_usuario(
    registro_existente: Dict[str, Any],
    firebase_user: Any,
    config_usuario: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Atualiza registro existente com dados do Firebase Auth.
    
    Args:
        registro_existente: Registro atual em usuarios_sistema
        firebase_user: Objeto UserRecord do Firebase Auth
        config_usuario: Configuração específica do usuário
    
    Returns:
        Dicionário atualizado
    """
    registro_atualizado = registro_existente.copy()
    
    # Atualiza firebase_uid se estiver vazio ou diferente
    if not registro_atualizado.get('firebase_uid') or registro_atualizado.get('firebase_uid') != firebase_user.uid:
        registro_atualizado['firebase_uid'] = firebase_user.uid
    
    # Atualiza email se estiver vazio ou diferente
    email_auth = firebase_user.email or ''
    if not registro_atualizado.get('email') or registro_atualizado.get('email').lower() != email_auth.lower():
        registro_atualizado['email'] = email_auth
    
    # Atualiza nome se estiver vazio
    if not registro_atualizado.get('nome_completo'):
        nome_completo = firebase_user.display_name or ''
        if not nome_completo:
            custom_claims = firebase_user.custom_claims or {}
            nome_completo = custom_claims.get('display_name', '')
        if not nome_completo and config_usuario:
            nome_completo = config_usuario.get('nome_completo', '')
        if not nome_completo:
            nome_completo = email_auth.split('@')[0] if email_auth else 'Sem nome'
        registro_atualizado['nome_completo'] = nome_completo
    
    # Atualiza workspaces e perfil se houver configuração específica
    if config_usuario:
        registro_atualizado['workspaces'] = config_usuario.get('workspaces', registro_atualizado.get('workspaces', []))
        registro_atualizado['perfil'] = config_usuario.get('perfil', registro_atualizado.get('perfil', 'cliente'))
    
    # Atualiza status ativo
    registro_atualizado['ativo'] = not firebase_user.disabled
    
    # Atualiza timestamps
    if 'created_at' not in registro_atualizado:
        registro_atualizado['created_at'] = formatar_timestamp(firebase_user.user_metadata.creation_timestamp)
    registro_atualizado['updated_at'] = datetime.now().isoformat()
    
    return registro_atualizado


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def sincronizar_usuarios(dry_run: bool = True) -> Dict[str, Any]:
    """
    Sincroniza usuários entre Firebase Auth e usuarios_sistema.
    
    Args:
        dry_run: Se True, apenas mostra o que seria feito sem modificar
    
    Returns:
        Dicionário com estatísticas da sincronização
    """
    print("\n" + "="*80)
    print("SINCRONIZAÇÃO DE USUÁRIOS - TAQUES ERP")
    print("="*80 + "\n")
    
    if dry_run:
        print("⚠️  MODO DRY RUN: Nenhuma alteração será feita\n")
    
    # Inicializa Firebase
    try:
        init_firebase()
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        return {}
    
    # Busca dados
    usuarios_auth = obter_usuarios_firebase_auth()
    usuarios_sistema = obter_usuarios_sistema()
    
    if not usuarios_auth:
        print("❌ Nenhum usuário encontrado no Firebase Auth. Abortando.")
        return {}
    
    # Faz backup
    if not dry_run:
        timestamp_backup = datetime.now().strftime('%Y%m%d_%H%M%S')
        caminho_backup = f"backup_usuarios_sistema_{timestamp_backup}.json"
        fazer_backup(usuarios_sistema, caminho_backup)
    
    # Estatísticas
    stats = {
        'criados': 0,
        'atualizados': 0,
        'sem_alteracao': 0,
        'orfaos': [],
        'erros': []
    }
    
    db = get_db()
    
    # =========================================================================
    # ETAPA 1: Sincronizar usuários do Firebase Auth
    # =========================================================================
    print("\n" + "-"*80)
    print("ETAPA 1: Sincronizando usuários do Firebase Auth")
    print("-"*80 + "\n")
    
    for email, firebase_user in usuarios_auth.items():
        email_lower = email.lower()
        config_usuario = CONFIGURACAO_USUARIOS.get(email_lower)
        
        # Busca registro existente
        registro_por_uid = encontrar_registro_por_uid(usuarios_sistema, firebase_user.uid)
        registro_por_email = encontrar_registro_por_email(usuarios_sistema, email_lower)
        
        registro_existente = registro_por_uid or registro_por_email
        
        if registro_existente:
            # Atualiza registro existente
            doc_id = registro_existente.get('_doc_id')
            registro_atualizado = atualizar_registro_usuario(
                registro_existente,
                firebase_user,
                config_usuario
            )
            
            # Verifica se houve mudanças
            mudancas = False
            for key in ['firebase_uid', 'email', 'nome_completo', 'workspaces', 'perfil', 'ativo']:
                if registro_existente.get(key) != registro_atualizado.get(key):
                    mudancas = True
                    break
            
            if mudancas:
                print(f"📝 Atualizando: {email}")
                if not dry_run:
                    try:
                        # Remove _doc_id antes de salvar
                        registro_atualizado.pop('_doc_id', None)
                        db.collection('usuarios_sistema').document(doc_id).set(registro_atualizado, merge=True)
                        stats['atualizados'] += 1
                    except Exception as e:
                        print(f"   ❌ Erro: {e}")
                        stats['erros'].append({'email': email, 'erro': str(e)})
                else:
                    stats['atualizados'] += 1
            else:
                print(f"✓ Sem alterações: {email}")
                stats['sem_alteracao'] += 1
        else:
            # Cria novo registro
            novo_registro = criar_registro_usuario(firebase_user, config_usuario)
            print(f"➕ Criando: {email}")
            if not dry_run:
                try:
                    db.collection('usuarios_sistema').add(novo_registro)
                    stats['criados'] += 1
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    stats['erros'].append({'email': email, 'erro': str(e)})
            else:
                stats['criados'] += 1
    
    # =========================================================================
    # ETAPA 2: Identificar registros órfãos
    # =========================================================================
    print("\n" + "-"*80)
    print("ETAPA 2: Identificando registros órfãos")
    print("-"*80 + "\n")
    
    uids_auth = {user.uid for user in usuarios_auth.values()}
    emails_auth = {email.lower() for email in usuarios_auth.keys()}
    
    for usuario in usuarios_sistema:
        firebase_uid = usuario.get('firebase_uid')
        email = usuario.get('email', '').lower()
        
        # É órfão se não tem firebase_uid OU o uid não existe no Firebase Auth
        # E também não tem email correspondente no Firebase Auth
        sem_uid = not firebase_uid or firebase_uid not in uids_auth
        sem_email = not email or email not in emails_auth
        
        if sem_uid and sem_email:
            stats['orfaos'].append({
                'doc_id': usuario.get('_doc_id'),
                'nome_completo': usuario.get('nome_completo', '-'),
                'email': usuario.get('email', '-'),
                'firebase_uid': firebase_uid or '-',
                'workspaces': usuario.get('workspaces', [])
            })
            print(f"⚠️  Órfão encontrado: {usuario.get('nome_completo', '-')} ({usuario.get('email', '-')})")
    
    # =========================================================================
    # RELATÓRIO FINAL
    # =========================================================================
    print("\n" + "="*80)
    print("RELATÓRIO FINAL")
    print("="*80 + "\n")
    
    print(f"✅ Criados: {stats['criados']}")
    print(f"📝 Atualizados: {stats['atualizados']}")
    print(f"✓ Sem alterações: {stats['sem_alteracao']}")
    print(f"⚠️  Órfãos encontrados: {len(stats['orfaos'])}")
    print(f"❌ Erros: {len(stats['erros'])}")
    
    if stats['orfaos']:
        print("\n" + "-"*80)
        print("REGISTROS ÓRFÃOS (requerem decisão manual):")
        print("-"*80 + "\n")
        for orfao in stats['orfaos']:
            print(f"  • {orfao['nome_completo']} ({orfao['email']})")
            print(f"    Doc ID: {orfao['doc_id']}")
            print(f"    Workspaces: {', '.join(orfao['workspaces']) if orfao['workspaces'] else 'Nenhum'}")
            print()
    
    if stats['erros']:
        print("\n" + "-"*80)
        print("ERROS ENCONTRADOS:")
        print("-"*80 + "\n")
        for erro in stats['erros']:
            print(f"  • {erro['email']}: {erro['erro']}")
    
    print("\n" + "="*80)
    if dry_run:
        print("⚠️  MODO DRY RUN: Execute sem --dry-run para aplicar alterações")
    else:
        print("✅ Sincronização concluída!")
    print("="*80 + "\n")
    
    return stats


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Sincroniza usuários entre Firebase Auth e usuarios_sistema')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo dry-run: mostra o que seria feito sem modificar dados'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Aplica alterações (padrão é dry-run)'
    )
    
    args = parser.parse_args()
    
    # Por padrão, executa em dry-run a menos que --apply seja especificado
    dry_run = not args.apply
    
    if not dry_run:
        # Pede confirmação antes de aplicar
        print("\n⚠️  ATENÇÃO: Você está prestes a modificar dados em usuarios_sistema!")
        print("   Um backup será criado automaticamente antes das alterações.")
        resposta = input("\n   Deseja continuar? (sim/não): ").strip().lower()
        
        if resposta not in ['sim', 's', 'yes', 'y']:
            print("\n❌ Operação cancelada pelo usuário.\n")
            sys.exit(0)
    
    sincronizar_usuarios(dry_run=dry_run)
