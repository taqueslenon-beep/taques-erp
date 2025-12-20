#!/usr/bin/env python3
"""
Script para criar contas no Firebase Authentication e vincular aos
usuários existentes na coleção 'users' do Firestore.

Execução: python scripts/criar_usuarios_auth.py
"""

import sys
import os
from typing import Dict, Any, Optional

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db, init_firebase, get_auth
from firebase_admin import auth
from google.cloud.firestore import SERVER_TIMESTAMP

# Usuários a criar no Firebase Auth
USUARIOS = [
    {
        "email": "flaviana.friedrich@gmail.com",
        "senha": "Taques@2024",
        "nome_exibicao": "Flaviana Friedrich",
    },
    {
        "email": "douglasmarco@gmail.com",
        "senha": "Taques@2024",
        "nome_exibicao": "Douglas Prado Marcos",
    },
    {
        "email": "bernataques@gmail.com",
        "senha": "Taques@2024",
        "nome_exibicao": "Berna Taques",
    },
]

COLECAO_FIRESTORE = 'users'
SENHA_MINIMA = 6


def verificar_email_existe_auth(email: str) -> Optional[str]:
    """
    Verifica se email já existe no Firebase Auth.
    
    Returns:
        UID do usuário se existir, None caso contrário
    """
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"Erro ao verificar email {email}: {e}")
        return None


def buscar_usuario_firestore(email: str) -> Optional[Dict[str, Any]]:
    """Busca usuário na coleção 'users' do Firestore por email."""
    try:
        db = get_db()
        query = db.collection(COLECAO_FIRESTORE).where('email', '==', email).limit(1)
        docs = list(query.stream())
        
        if docs:
            usuario = docs[0].to_dict()
            usuario['_id'] = docs[0].id
            return usuario
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário no Firestore: {e}")
        return None


def criar_usuario_auth(dados: Dict[str, Any]) -> tuple:
    """
    Cria usuário no Firebase Authentication e atualiza Firestore.
    
    Args:
        dados: Dict com email, senha, nome_exibicao
        
    Returns:
        (sucesso: bool, mensagem: str, uid: str ou None)
    """
    email = dados.get('email', '').strip()
    senha = dados.get('senha', '').strip()
    nome_exibicao = dados.get('nome_exibicao', '').strip()
    
    # Validações
    if not email:
        return False, "Email é obrigatório", None
    
    if not senha:
        return False, "Senha é obrigatória", None
    
    if len(senha) < SENHA_MINIMA:
        return False, f"Senha deve ter no mínimo {SENHA_MINIMA} caracteres", None
    
    if not nome_exibicao:
        return False, "Nome de exibição é obrigatório", None
    
    # Verifica se email já existe no Auth
    uid_existente = verificar_email_existe_auth(email)
    if uid_existente:
        return False, f"Email {email} já existe no Firebase Auth (UID: {uid_existente})", uid_existente
    
    # Busca usuário no Firestore
    usuario_firestore = buscar_usuario_firestore(email)
    if not usuario_firestore:
        return False, f"Usuário {email} não encontrado na coleção 'users' do Firestore", None
    
    try:
        # Cria usuário no Firebase Auth
        user_record = auth.create_user(
            email=email,
            password=senha,
            display_name=nome_exibicao,
            email_verified=False,  # Usuário deve verificar depois
        )
        
        uid = user_record.uid
        
        # Define display_name nos custom claims
        try:
            auth.set_custom_user_claims(uid, {'display_name': nome_exibicao})
        except Exception as e:
            print(f"Aviso: Erro ao definir custom claims: {e}")
        
        # Atualiza Firestore com UID
        try:
            db = get_db()
            doc_id = usuario_firestore.get('_id')
            
            if not doc_id:
                # Se não tem _id, tenta gerar do email
                doc_id = email.replace('@', '-').replace('.', '-').lower()[:100]
            
            db.collection(COLECAO_FIRESTORE).document(doc_id).update({
                'uid': uid,
                'auth_vinculado': True,
                'data_atualizacao': SERVER_TIMESTAMP,
            })
        except Exception as e:
            print(f"Aviso: Erro ao atualizar Firestore: {e}")
            # Não falha a criação, apenas avisa
        
        return True, f"Usuário {nome_exibicao} criado com sucesso no Firebase Auth", uid
        
    except Exception as e:
        error_msg = str(e)
        if "email already exists" in error_msg.lower():
            return False, f"Email {email} já existe no Firebase Auth", None
        return False, f"Erro ao criar usuário: {error_msg}", None


def main():
    """Função principal."""
    print("\n" + "="*70)
    print("CRIAÇÃO DE CONTAS NO FIREBASE AUTHENTICATION")
    print("="*70 + "\n")
    
    # Inicializa Firebase
    try:
        init_firebase()
        print("✅ Firebase inicializado\n")
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        return
    
    criados = 0
    existentes = 0
    erros = 0
    nao_encontrados = 0
    
    # Processa cada usuário
    for usuario in USUARIOS:
        email = usuario['email']
        nome = usuario['nome_exibicao']
        
        print(f"📝 Processando: {nome} ({email})")
        
        sucesso, mensagem, uid = criar_usuario_auth(usuario)
        
        if sucesso:
            print(f"   ✅ {mensagem}")
            print(f"      UID: {uid}")
            print(f"      Senha inicial: {usuario['senha']}")
            print(f"      ⚠️  Usuário deve trocar a senha no primeiro login\n")
            criados += 1
        elif "já existe" in mensagem.lower():
            print(f"   ⚠️  {mensagem}\n")
            existentes += 1
        elif "não encontrado" in mensagem.lower():
            print(f"   ⚠️  {mensagem}\n")
            nao_encontrados += 1
        else:
            print(f"   ❌ {mensagem}\n")
            erros += 1
    
    # Resumo
    print("-"*70)
    print("RESUMO:")
    print(f"  ✅ Criados: {criados}")
    print(f"  ⚠️  Já existentes no Auth: {existentes}")
    print(f"  ⚠️  Não encontrados no Firestore: {nao_encontrados}")
    print(f"  ❌ Erros: {erros}")
    print("-"*70)
    
    # Lista usuários criados
    if criados > 0:
        print("\n📋 USUÁRIOS CRIADOS NO FIREBASE AUTH:\n")
        for usuario in USUARIOS:
            email = usuario['email']
            nome = usuario['nome_exibicao']
            senha = usuario['senha']
            
            # Verifica se foi criado
            uid = verificar_email_existe_auth(email)
            if uid:
                print(f"  ✅ {nome}")
                print(f"     Email: {email}")
                print(f"     UID: {uid}")
                print(f"     Senha inicial: {senha}")
                print()
    
    print("="*70)
    print("IMPORTANTE:")
    print("  - Todos os usuários devem trocar a senha no primeiro login")
    print("  - Os usuários agora aparecem na página de Configurações")
    print("  - Verifique se os emails estão corretos antes de enviar")
    print("="*70)
    print("FIM")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()










