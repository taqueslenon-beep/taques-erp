#!/usr/bin/env python3
"""
Script para criar usuários iniciais do sistema TAQUES-ERP.
Execução: python scripts/criar_usuarios_iniciais.py
"""

import sys
import os
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db, init_firebase
from google.cloud.firestore import SERVER_TIMESTAMP

# Definição dos usuários a serem criados
USUARIOS_INICIAIS = [
    # === CLIENTES SCHMIDMEIER ===
    # Acesso APENAS ao workspace Schmidmeier
    # Login será configurado posteriormente
    {
        "nome_completo": "Carlos Schmidmeier",
        "nome_exibicao": "Carlos",
        "email": "",  # Será preenchido depois
        "telefone": "",
        "perfil": "cliente",
        "workspaces": ["schmidmeier"],
        "ativo": True,
        "firebase_uid": "",  # Será vinculado ao criar login
        "observacoes": "Cliente - Grupo Schmidmeier. Login pendente.",
    },
    {
        "nome_completo": "Luciane Schmidmeier",
        "nome_exibicao": "Luciane",
        "email": "",
        "telefone": "",
        "perfil": "cliente",
        "workspaces": ["schmidmeier"],
        "ativo": True,
        "firebase_uid": "",
        "observacoes": "Cliente - Grupo Schmidmeier. Login pendente.",
    },
    {
        "nome_completo": "Jhonny Schmidmeier",
        "nome_exibicao": "Jhonny",
        "email": "",
        "telefone": "",
        "perfil": "cliente",
        "workspaces": ["schmidmeier"],
        "ativo": True,
        "firebase_uid": "",
        "observacoes": "Cliente - Grupo Schmidmeier. Login pendente.",
    },
    
    # === USUÁRIOS INTERNOS - TAQUES ===
    # Acesso a AMBOS workspaces (Schmidmeier + Visão Geral)
    # São usuários do escritório, não administradores
    {
        "nome_completo": "Gilberto Taques",
        "nome_exibicao": "Gilberto",
        "email": "",  # Será preenchido depois
        "telefone": "",
        "perfil": "interno",
        "workspaces": ["schmidmeier", "visao_geral"],
        "ativo": True,
        "firebase_uid": "",
        "observacoes": "Usuário interno - Escritório Taques. Acesso aos dois workspaces.",
    },
    {
        "nome_completo": "Berna Taques",
        "nome_exibicao": "Berna",
        "email": "",
        "telefone": "",
        "perfil": "interno",
        "workspaces": ["schmidmeier", "visao_geral"],
        "ativo": True,
        "firebase_uid": "",
        "observacoes": "Usuário interno - Escritório Taques. Acesso aos dois workspaces.",
    },
]


def criar_usuarios():
    """Cria os usuários iniciais no Firestore."""
    print("\n" + "="*70)
    print("CRIAÇÃO DE USUÁRIOS INICIAIS - TAQUES ERP")
    print("="*70 + "\n")
    
    # Inicializa Firebase
    try:
        init_firebase()
    except Exception as e:
        print(f"Erro ao inicializar Firebase: {e}")
        return
    
    db = get_db()
    colecao = db.collection('usuarios_sistema')
    
    criados = 0
    existentes = 0
    erros = 0
    
    for usuario in USUARIOS_INICIAIS:
        try:
            # Gera ID a partir do nome
            doc_id = usuario['nome_completo'].lower().replace(' ', '_')
            
            # Verifica se já existe
            doc_ref = colecao.document(doc_id)
            if doc_ref.get().exists:
                print(f"⚠️  Já existe: {usuario['nome_completo']}")
                existentes += 1
                continue
            
            # Adiciona timestamps
            usuario['_id'] = doc_id
            usuario['created_at'] = SERVER_TIMESTAMP
            usuario['updated_at'] = SERVER_TIMESTAMP
            
            # Salva no Firestore
            doc_ref.set(usuario)
            
            perfil_emoji = "👤" if usuario['perfil'] == 'cliente' else "👨‍💼"
            workspaces = ', '.join(usuario['workspaces'])
            print(f"✅ Criado: {perfil_emoji} {usuario['nome_completo']}")
            print(f"   Perfil: {usuario['perfil']} | Workspaces: {workspaces}")
            
            criados += 1
            
        except Exception as e:
            print(f"❌ Erro ao criar {usuario['nome_completo']}: {e}")
            erros += 1
    
    # Resumo
    print("\n" + "-"*70)
    print("RESUMO:")
    print(f"  ✅ Criados: {criados}")
    print(f"  ⚠️  Já existentes: {existentes}")
    print(f"  ❌ Erros: {erros}")
    print("-"*70)
    
    # Lista todos os usuários
    print("\n📋 USUÁRIOS NO SISTEMA:\n")
    
    docs = colecao.stream()
    for doc in docs:
        u = doc.to_dict()
        perfil_emoji = "👤" if u.get('perfil') == 'cliente' else "👨‍💼"
        workspaces = ', '.join(u.get('workspaces', []))
        print(f"  {perfil_emoji} {u.get('nome_completo', 'N/A')}")
        print(f"     Perfil: {u.get('perfil', 'N/A')} | Workspaces: {workspaces}")
        print(f"     Email: {u.get('email') or '(pendente)'}")
        print()
    
    print("="*70)
    print("FIM")
    print("="*70 + "\n")


if __name__ == "__main__":
    criar_usuarios()








