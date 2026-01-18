#!/usr/bin/env python3
"""
Script de Backup do Firebase Firestore
Exporta collections específicas para arquivo JSON
"""

import os
import sys
import json
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mini_erp.firebase_config import get_db

def backup_collection(db, collection_name):
    """Faz backup de uma collection"""
    print(f"📦 Exportando collection: {collection_name}...")
    
    try:
        docs = db.collection(collection_name).stream()
        data = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            
            # Converter timestamps para string
            for key, value in doc_data.items():
                if hasattr(value, 'isoformat'):
                    doc_data[key] = value.isoformat()
            
            data.append(doc_data)
        
        print(f"   ✓ {len(data)} documentos exportados")
        return data
    
    except Exception as e:
        print(f"   ✗ Erro ao exportar {collection_name}: {e}")
        return []


def main():
    """Executa backup das collections"""
    print("=" * 70)
    print("🔒 BACKUP DO FIREBASE FIRESTORE - TAQUES-ERP")
    print("=" * 70)
    
    # Collections para backup (incluindo a nova collection audiencias)
    collections = [
        'audiencias',          # Nova collection
        'vg_casos',
        'prioridades', 
        'usuarios_sistema',
        'vg_pessoas',
        'processes'
    ]
    
    # Conectar ao Firebase
    print("\n🔌 Conectando ao Firebase...")
    db = get_db()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao Firebase")
        sys.exit(1)
    
    print("   ✓ Conectado com sucesso")
    
    # Fazer backup de cada collection
    print(f"\n📦 Iniciando backup de {len(collections)} collections...\n")
    
    backup_data = {}
    total_docs = 0
    
    for collection_name in collections:
        data = backup_collection(db, collection_name)
        backup_data[collection_name] = data
        total_docs += len(data)
    
    # Gerar nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.json"
    filepath = os.path.join('/Users/lenontaques/Documents/taques-erp/backups', filename)
    
    # Salvar backup
    print(f"\n💾 Salvando backup em: {filename}")
    
    backup_metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_collections': len(collections),
        'total_documents': total_docs,
        'collections': list(collections)
    }
    
    final_backup = {
        'metadata': backup_metadata,
        'data': backup_data
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final_backup, f, ensure_ascii=False, indent=2)
    
    print(f"   ✓ Backup salvo com sucesso!")
    print(f"\n{'=' * 70}")
    print("✅ BACKUP CONCLUÍDO")
    print(f"{'=' * 70}")
    print(f"📊 Resumo:")
    print(f"   • Collections: {len(collections)}")
    print(f"   • Documentos: {total_docs}")
    print(f"   • Arquivo: {filename}")
    print(f"   • Tamanho: {os.path.getsize(filepath) / 1024:.2f} KB")
    print(f"{'=' * 70}\n")


if __name__ == '__main__':
    main()
