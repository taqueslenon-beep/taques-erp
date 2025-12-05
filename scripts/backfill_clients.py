#!/usr/bin/env python3
"""
Script de Backfill: Migra clientes dos casos para a coleção 'clients'.

Executa:
1. Busca todos os casos
2. Extrai nomes de clientes do campo 'clients' (array ou string)
3. Cria novos documentos na coleção 'clients' se não existirem
4. Opcionalmente vincula os casos aos clientes (linked_cases)

Uso:
    python scripts/backfill_clients.py
    python scripts/backfill_clients.py --dry-run  # Simula sem gravar
"""

import os
import sys
import argparse
import time
from typing import Dict, List, Set, Any

# Garante que o diretório do projeto esteja no sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from google.cloud.firestore import SERVER_TIMESTAMP
from mini_erp.firebase_config import get_db


def sanitize_doc_id(name: str) -> str:
    """
    Sanitiza nome para uso como ID de documento no Firestore.
    Remove caracteres problemáticos e limita tamanho.
    """
    if not name:
        return ""
    
    # Remove/substitui caracteres problemáticos
    doc_id = name.strip()
    doc_id = doc_id.replace('/', '-')
    doc_id = doc_id.replace('\\', '-')
    doc_id = doc_id.replace(' ', '-')
    doc_id = doc_id.replace('.', '-')
    doc_id = doc_id.lower()
    
    # Remove caracteres duplicados e limita tamanho
    while '--' in doc_id:
        doc_id = doc_id.replace('--', '-')
    
    return doc_id.strip('-')[:100]


def ensure_list(value) -> List[str]:
    """Converte valor para lista, tratando None, string e array."""
    if isinstance(value, list):
        return [v for v in value if v]  # Remove valores vazios
    if value is None:
        return []
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def get_existing_clients(db) -> Dict[str, Dict[str, Any]]:
    """
    Retorna dicionário de clientes existentes.
    Chave: nome em minúsculas (para comparação case-insensitive)
    Valor: documento do cliente
    """
    existing = {}
    
    try:
        docs = db.collection('clients').stream()
        for doc in docs:
            client_data = doc.to_dict()
            client_data['_id'] = doc.id
            
            # Indexa por full_name e name (compatibilidade)
            full_name = client_data.get('full_name', '') or client_data.get('name', '')
            if full_name:
                existing[full_name.lower().strip()] = client_data
            
            # Também indexa por cpf_cnpj se existir
            cpf_cnpj = client_data.get('cpf_cnpj', '') or client_data.get('document', '')
            if cpf_cnpj:
                existing[cpf_cnpj.strip()] = client_data
                
    except Exception as e:
        print(f"⚠️  Erro ao buscar clientes existentes: {e}")
    
    return existing


def extract_clients_from_cases(db) -> Dict[str, Set[str]]:
    """
    Extrai todos os clientes mencionados nos casos.
    
    Returns:
        Dict mapeando nome_cliente -> set de case_ids onde aparece
    """
    clients_map: Dict[str, Set[str]] = {}
    
    try:
        docs = db.collection('cases').stream()
        
        for doc in docs:
            case_data = doc.to_dict()
            case_id = doc.id
            
            # Campo 'clients' pode ser array ou string
            client_names = ensure_list(case_data.get('clients'))
            
            # Também verifica campos alternativos
            if not client_names:
                client_name = case_data.get('client_name') or case_data.get('client')
                client_names = ensure_list(client_name)
            
            for name in client_names:
                name = name.strip()
                if name:
                    if name not in clients_map:
                        clients_map[name] = set()
                    clients_map[name].add(case_id)
        
        print(f"📋 Encontrados {len(clients_map)} clientes únicos em {sum(len(v) for v in clients_map.values())} referências")
        
    except Exception as e:
        print(f"❌ Erro ao extrair clientes dos casos: {e}")
        import traceback
        traceback.print_exc()
    
    return clients_map


def create_client_document(full_name: str, linked_cases: List[str]) -> Dict[str, Any]:
    """
    Cria estrutura de documento para novo cliente.
    """
    return {
        'full_name': full_name,
        'name': full_name,  # Compatibilidade
        'display_name': '',
        'nickname': '',
        'cpf_cnpj': '',
        'document': '',  # Compatibilidade
        'email': '',
        'phone': '',
        'bonds': [],
        'linked_cases': linked_cases,
        'created_at': SERVER_TIMESTAMP,
        'updated_at': SERVER_TIMESTAMP,
    }


def backfill_clients(dry_run: bool = False, batch_size: int = 20):
    """
    Executa o backfill de clientes dos casos para a coleção clients.
    
    Args:
        dry_run: Se True, apenas simula sem gravar
        batch_size: Número de documentos por batch (para evitar quotas)
    """
    print("=" * 60)
    print("🔄 BACKFILL: Clientes dos Casos -> Coleção 'clients'")
    print("=" * 60)
    
    if dry_run:
        print("⚠️  MODO DRY-RUN: Nenhuma alteração será gravada\n")
    
    db = get_db()
    
    # 1. Busca clientes existentes
    print("\n📂 Buscando clientes existentes...")
    existing_clients = get_existing_clients(db)
    print(f"   → {len(existing_clients)} clientes já cadastrados")
    
    # 2. Extrai clientes dos casos
    print("\n📋 Extraindo clientes dos casos...")
    clients_from_cases = extract_clients_from_cases(db)
    
    if not clients_from_cases:
        print("\n✅ Nenhum cliente encontrado nos casos. Nada a fazer.")
        return
    
    # 3. Identifica clientes novos
    new_clients = []
    existing_updates = []
    
    for client_name, case_ids in clients_from_cases.items():
        client_key = client_name.lower().strip()
        
        if client_key in existing_clients:
            # Cliente já existe - verificar se precisa atualizar linked_cases
            existing = existing_clients[client_key]
            current_linked = set(existing.get('linked_cases', []))
            new_linked = current_linked | case_ids
            
            if new_linked != current_linked:
                existing_updates.append({
                    'doc_id': existing['_id'],
                    'name': client_name,
                    'linked_cases': list(new_linked)
                })
        else:
            new_clients.append({
                'name': client_name,
                'linked_cases': list(case_ids)
            })
    
    print(f"\n📊 Resumo:")
    print(f"   → {len(new_clients)} clientes novos a criar")
    print(f"   → {len(existing_updates)} clientes existentes a atualizar (linked_cases)")
    print(f"   → {len(clients_from_cases) - len(new_clients) - len(existing_updates)} clientes já atualizados")
    
    if not new_clients and not existing_updates:
        print("\n✅ Todos os clientes já estão sincronizados!")
        return
    
    # 4. Cria novos clientes em batches
    if new_clients:
        print(f"\n📝 Criando {len(new_clients)} novos clientes...")
        
        created_count = 0
        batch = db.batch()
        batch_count = 0
        
        for client_info in new_clients:
            client_name = client_info['name']
            linked_cases = client_info['linked_cases']
            
            doc_id = sanitize_doc_id(client_name)
            if not doc_id:
                print(f"   ⚠️  Ignorando cliente com nome inválido: '{client_name}'")
                continue
            
            client_doc = create_client_document(client_name, linked_cases)
            
            if dry_run:
                print(f"   [DRY-RUN] Criaria: {client_name} (ID: {doc_id}, casos: {len(linked_cases)})")
            else:
                doc_ref = db.collection('clients').document(doc_id)
                batch.set(doc_ref, client_doc)
                batch_count += 1
                
                # Commit batch quando atingir limite
                if batch_count >= batch_size:
                    batch.commit()
                    created_count += batch_count
                    print(f"   ✓ Batch commitado ({created_count} clientes criados)")
                    batch = db.batch()
                    batch_count = 0
                    time.sleep(0.1)  # Throttle para evitar quota
        
        # Commit do último batch
        if not dry_run and batch_count > 0:
            batch.commit()
            created_count += batch_count
            print(f"   ✓ Batch final commitado ({created_count} clientes criados no total)")
    
    # 5. Atualiza clientes existentes (linked_cases)
    if existing_updates:
        print(f"\n🔄 Atualizando {len(existing_updates)} clientes existentes...")
        
        updated_count = 0
        batch = db.batch()
        batch_count = 0
        
        for update_info in existing_updates:
            doc_id = update_info['doc_id']
            client_name = update_info['name']
            linked_cases = update_info['linked_cases']
            
            if dry_run:
                print(f"   [DRY-RUN] Atualizaria: {client_name} (linked_cases: {len(linked_cases)})")
            else:
                doc_ref = db.collection('clients').document(doc_id)
                batch.update(doc_ref, {
                    'linked_cases': linked_cases,
                    'updated_at': SERVER_TIMESTAMP
                })
                batch_count += 1
                
                if batch_count >= batch_size:
                    batch.commit()
                    updated_count += batch_count
                    print(f"   ✓ Batch commitado ({updated_count} clientes atualizados)")
                    batch = db.batch()
                    batch_count = 0
                    time.sleep(0.1)
        
        if not dry_run and batch_count > 0:
            batch.commit()
            updated_count += batch_count
            print(f"   ✓ Batch final commitado ({updated_count} clientes atualizados no total)")
    
    # 6. Resumo final
    print("\n" + "=" * 60)
    if dry_run:
        print("✅ DRY-RUN concluído. Nenhuma alteração foi gravada.")
        print(f"   Seriam criados: {len(new_clients)} clientes")
        print(f"   Seriam atualizados: {len(existing_updates)} clientes")
    else:
        print("✅ Backfill concluído com sucesso!")
        print(f"   Criados: {len(new_clients)} clientes")
        print(f"   Atualizados: {len(existing_updates)} clientes")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Backfill de clientes dos casos para a coleção clients'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Simula a execução sem gravar no Firestore'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=20,
        help='Número de operações por batch (default: 20)'
    )
    
    args = parser.parse_args()
    
    try:
        backfill_clients(dry_run=args.dry_run, batch_size=args.batch_size)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()








