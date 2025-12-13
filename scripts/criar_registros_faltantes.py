#!/usr/bin/env python3
"""
Script temporário para criar registros faltantes no Firebase.

Cria:
- Usuário Lenon na coleção usuarios_sistema
- 2 clientes na coleção vg_pessoas

Uso:
    python scripts/criar_registros_faltantes.py
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

COLECAO_USUARIOS = 'usuarios_sistema'
COLECAO_PESSOAS = 'vg_pessoas'

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================


def verificar_usuario_existente(db, usuario_id: str) -> bool:
    """Verifica se um usuário já existe pelo ID do documento."""
    try:
        doc = db.collection(COLECAO_USUARIOS).document(usuario_id).get()
        return doc.exists
    except Exception as e:
        print(f"    Erro ao verificar usuário '{usuario_id}': {e}")
        return False


def criar_usuario_lenon(db) -> bool:
    """Cria o usuário Lenon na coleção usuarios_sistema."""
    usuario_id = 'lenon_taques'
    
    print(f"\n👤 Verificando usuário '{usuario_id}'...")
    
    if verificar_usuario_existente(db, usuario_id):
        print(f"   ⚠️  Usuário '{usuario_id}' já existe - PULANDO")
        return False
    
    agora = datetime.now()
    
    dados_usuario = {
        'nome_completo': 'Lenon Gustavo Batista Taques',
        'nome_exibicao': 'Lenon',
        'email': '',
        'telefone': '',
        'perfil': 'interno',
        'workspaces': ['schmidmeier', 'visao_geral'],
        'ativo': True,
        'firebase_uid': '',
        'observacoes': 'Administrador do sistema',
        'created_at': agora,
        'updated_at': agora,
    }
    
    try:
        db.collection(COLECAO_USUARIOS).document(usuario_id).set(dados_usuario)
        print(f"   ✅ Usuário '{usuario_id}' criado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar usuário '{usuario_id}': {e}")
        return False


def verificar_cliente_existente(db, full_name: str) -> bool:
    """Verifica se um cliente já existe pelo full_name."""
    try:
        query = db.collection(COLECAO_PESSOAS).where('full_name', '==', full_name).limit(1)
        docs = list(query.stream())
        return len(docs) > 0
    except Exception as e:
        print(f"    Erro ao verificar cliente '{full_name}': {e}")
        return False


def criar_cliente(db, dados_cliente: dict) -> bool:
    """Cria um cliente na coleção vg_pessoas."""
    full_name = dados_cliente.get('full_name', '')
    
    print(f"\n👥 Verificando cliente '{full_name}'...")
    
    if verificar_cliente_existente(db, full_name):
        print(f"   ⚠️  Cliente '{full_name}' já existe - PULANDO")
        return False
    
    agora = datetime.now()
    
    dados_cliente['created_at'] = agora
    dados_cliente['updated_at'] = agora
    
    try:
        db.collection(COLECAO_PESSOAS).add(dados_cliente)
        print(f"   ✅ Cliente '{full_name}' criado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar cliente '{full_name}': {e}")
        return False


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================


def main():
    print("=" * 70)
    print("CRIAÇÃO DE REGISTROS FALTANTES NO FIREBASE")
    print("=" * 70)
    print()
    
    print("🔌 Conectando ao Firebase...")
    try:
        db = get_db()
        print("   ✅ Conectado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firebase: {e}")
        return
    
    # Criar usuário Lenon
    usuario_criado = criar_usuario_lenon(db)
    
    # Criar cliente 1: RACER AUTO E PICK-UPS LTDA
    cliente1 = {
        'full_name': 'RACER AUTO E PICK-UPS LTDA',
        'nome_exibicao': 'RACER AUTO E PICK-UPS LTDA',
        'apelido': 'RACER',
        'tipo_pessoa': 'PJ',
        'cpf': '',
        'cnpj': '',
        'email': '',
        'telefone': '',
        'endereco': '',
        'observacoes': 'Importado via migração',
    }
    cliente1_criado = criar_cliente(db, cliente1)
    
    # Criar cliente 2: SBM OFICINA MECÂNICA LTDA (MECÂNICA MASTER)
    cliente2 = {
        'full_name': 'SBM OFICINA MECÂNICA LTDA (MECÂNICA MASTER)',
        'nome_exibicao': 'SBM OFICINA MECÂNICA LTDA (MECÂNICA MASTER)',
        'apelido': 'MECÂNICA MASTER',
        'tipo_pessoa': 'PJ',
        'cpf': '',
        'cnpj': '',
        'email': '',
        'telefone': '',
        'endereco': '',
        'observacoes': 'Importado via migração',
    }
    cliente2_criado = criar_cliente(db, cliente2)
    
    # Relatório final
    print()
    print("=" * 70)
    print("RELATÓRIO FINAL")
    print("=" * 70)
    print(f"Usuário Lenon:        {'✅ CRIADO' if usuario_criado else '⏭️  JÁ EXISTIA'}")
    print(f"Cliente RACER:        {'✅ CRIADO' if cliente1_criado else '⏭️  JÁ EXISTIA'}")
    print(f"Cliente MECÂNICA:     {'✅ CRIADO' if cliente2_criado else '⏭️  JÁ EXISTIA'}")
    print("=" * 70)
    print()
    
    total_criados = sum([usuario_criado, cliente1_criado, cliente2_criado])
    
    if total_criados > 0:
        print(f"✅ {total_criados} registro(s) criado(s) com sucesso!")
    else:
        print("ℹ️  Todos os registros já existiam no Firebase")
    
    print()


if __name__ == '__main__':
    main()



