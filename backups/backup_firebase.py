#!/usr/bin/env python3
"""
Script de backup das collections do Firebase Firestore
Projeto: TAQUES-ERP
"""

import json
import os
import sys
from datetime import datetime

# Adiciona o diretório do projeto ao path
sys.path.insert(0, '/Users/lenontaques/Documents/taques-erp')

from mini_erp.core.firebase_config import get_db

def backup_collection(db, collection_name):
    """Exporta uma collection para dicionário."""
    docs = db.collection(collection_name).stream()
    data = []
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['_id'] = doc.id
        data.append(doc_data)
    return data

def main():
    # Timestamp para nome do arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Collections a fazer backup
    collections = [
        'oportunidades',      # Nova collection do módulo Novos Negócios
        'pessoas',            # Inclui leads
        'vg_casos',
        'prioridades',
        'users'
    ]
    
    print(f"[BACKUP] Iniciando backup - {timestamp}")
    
    try:
        db = get_db()
        backup_data = {}
        
        for collection in collections:
            print(f"  → Exportando: {collection}")
            backup_data[collection] = backup_collection(db, collection)
            print(f"    ✓ {len(backup_data[collection])} documentos")
        
        # Salvar arquivo
        backup_dir = '/Users/lenontaques/Documents/taques-erp/backups'
        filename = f'backup_{timestamp}.json'
        filepath = os.path.join(backup_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[BACKUP] ✅ Concluído!")
        print(f"[BACKUP] Arquivo: {filepath}")
        
        # Mostrar resumo
        total_docs = sum(len(docs) for docs in backup_data.values())
        print(f"[BACKUP] Total: {total_docs} documentos em {len(collections)} collections")
        
    except Exception as e:
        print(f"\n[BACKUP] ❌ Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
