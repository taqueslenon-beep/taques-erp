#!/usr/bin/env python3
"""
Backup das collections do Firebase Firestore
Gerado em: $(date)
"""
import json
import os
from datetime import datetime

# Inicializa Firebase
from mini_erp.firebase_config import ensure_firebase_initialized, get_db

def backup_collection(db, collection_name):
    """Exporta uma collection para lista de dicts"""
    docs = db.collection(collection_name).stream()
    data = []
    for doc in docs:
        item = doc.to_dict()
        item['_id'] = doc.id
        # Converter timestamps para string
        for key, value in item.items():
            if hasattr(value, 'isoformat'):
                item[key] = value.isoformat()
        data.append(item)
    return data

def main():
    ensure_firebase_initialized()
    db = get_db()
    
    # Collections para backup
    collections = ['vg_casos', 'vg_pessoas', 'processes', 'users']
    
    backup_data = {}
    for col in collections:
        try:
            backup_data[col] = backup_collection(db, col)
            print(f"✅ {col}: {len(backup_data[col])} documentos")
        except Exception as e:
            print(f"⚠️  {col}: Erro - {e}")
            backup_data[col] = []
    
    # Salvar arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backups/backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Backup salvo em: {filename}")
    print(f"📦 Total: {sum(len(v) for v in backup_data.values())} documentos")

if __name__ == '__main__':
    main()
