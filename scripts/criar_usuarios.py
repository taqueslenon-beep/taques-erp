#!/usr/bin/env python3
"""
Script para criar novos usuários no sistema TAQUES-ERP.
Valida duplicação por email antes de criar.

Execução: python scripts/criar_usuarios.py
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db, init_firebase
from google.cloud.firestore import SERVER_TIMESTAMP

# Usuários a serem criados
USUARIOS = [
    {
        "email": "flaviana.friedrich@gmail.com",
        "nome_exibicao": "Flaviana Friedrich",
        "permissao": "usuario",
        "status": "ativo",
    },
    {
        "email": "douglasmarco@gmail.com",
        "nome_exibicao": "Douglas Prado Marcos",
        "permissao": "usuario",
        "status": "ativo",
    },
    {
        "email": "bernataques@gmail.com",
        "nome_exibicao": "Berna Taques",
        "permissao": "usuario",
        "status": "ativo",
    },
]

COLECAO = 'users'


def verificar_email_existe(email: str) -> bool:
    """Verifica se já existe usuário com o email informado."""
    try:
        db = get_db()
        # Busca por email na coleção users
        query = db.collection(COLECAO).where('email', '==', email).limit(1)
        docs = list(query.stream())
        return len(docs) > 0
    except Exception as e:
        print(f"Erro ao verificar email {email}: {e}")
        return False


def criar_usuario(dados: Dict[str, Any]) -> tuple:
    """
    Cria um novo usuário no Firestore.
    
    Returns:
        (sucesso: bool, mensagem: str)
    """
    email = dados.get('email', '').strip()
    nome_exibicao = dados.get('nome_exibicao', '').strip()
    permissao = dados.get('permissao', 'usuario')
    status = dados.get('status', 'ativo')
    
    # Validações
    if not email:
        return False, "Email é obrigatório"
    
    if not nome_exibicao:
        return False, "Nome de exibição é obrigatório"
    
    if permissao not in ['usuario', 'administrador']:
        return False, f"Permissão inválida: {permissao}. Use 'usuario' ou 'administrador'"
    
    if status not in ['ativo', 'inativo']:
        return False, f"Status inválido: {status}. Use 'ativo' ou 'inativo'"
    
    # Verifica se email já existe
    if verificar_email_existe(email):
        return False, f"Email {email} já existe no sistema"
    
    try:
        db = get_db()
        
        # Gera ID do documento a partir do email
        doc_id = email.replace('@', '-').replace('.', '-').lower()[:100]
        
        # Prepara dados do usuário
        usuario = {
            'email': email,
            'nome_exibicao': nome_exibicao,
            'permissao': permissao,
            'status': status,
            'data_criacao': SERVER_TIMESTAMP,
            'data_atualizacao': SERVER_TIMESTAMP,
            'criado_por': 'sistema',
        }
        
        # Salva no Firestore
        db.collection(COLECAO).document(doc_id).set(usuario)
        
        return True, f"Usuário {nome_exibicao} criado com sucesso"
        
    except Exception as e:
        return False, f"Erro ao criar usuário: {e}"


def listar_usuarios() -> List[Dict[str, Any]]:
    """Lista todos os usuários da coleção users."""
    try:
        db = get_db()
        docs = db.collection(COLECAO).stream()
        
        usuarios = []
        for doc in docs:
            usuario = doc.to_dict()
            usuario['_id'] = doc.id
            usuarios.append(usuario)
        
        return usuarios
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []


def main():
    """Função principal."""
    print("\n" + "="*70)
    print("CRIAÇÃO DE USUÁRIOS - TAQUES ERP")
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
    
    # Processa cada usuário
    for usuario in USUARIOS:
        email = usuario['email']
        nome = usuario['nome_exibicao']
        
        print(f"📝 Processando: {nome} ({email})")
        
        sucesso, mensagem = criar_usuario(usuario)
        
        if sucesso:
            print(f"   ✅ {mensagem}\n")
            criados += 1
        elif "já existe" in mensagem.lower():
            print(f"   ⚠️  {mensagem}\n")
            existentes += 1
        else:
            print(f"   ❌ {mensagem}\n")
            erros += 1
    
    # Resumo
    print("-"*70)
    print("RESUMO:")
    print(f"  ✅ Criados: {criados}")
    print(f"  ⚠️  Já existentes: {existentes}")
    print(f"  ❌ Erros: {erros}")
    print("-"*70)
    
    # Lista todos os usuários
    print("\n📋 USUÁRIOS NO SISTEMA:\n")
    
    usuarios = listar_usuarios()
    if usuarios:
        # Ordena por nome de exibição
        usuarios.sort(key=lambda u: u.get('nome_exibicao', '').lower())
        
        for u in usuarios:
            email = u.get('email', 'N/A')
            nome = u.get('nome_exibicao', 'N/A')
            permissao = u.get('permissao', 'N/A')
            status = u.get('status', 'N/A')
            
            status_emoji = "🟢" if status == "ativo" else "🔴"
            permissao_emoji = "👑" if permissao == "administrador" else "👤"
            
            print(f"  {status_emoji} {permissao_emoji} {nome}")
            print(f"     Email: {email} | Permissão: {permissao} | Status: {status}")
            print()
    else:
        print("  Nenhum usuário encontrado na coleção 'users'")
    
    print("="*70)
    print("FIM")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

