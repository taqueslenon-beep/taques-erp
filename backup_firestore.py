#!/usr/bin/env python3
"""
Backup das collections do Firestore - TAQUES-ERP
"""
import json
import os
import sys

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mini_erp.database import get_db, ensure_firebase_initialized

def backup_collection(db, collection_name):
    """Exporta uma collection para lista de dicts."""
    docs = []
    try:
        collection_ref = db.collection(collection_name)
        for doc in collection_ref.stream():
            data = doc.to_dict()
            data['_id'] = doc.id
            # Converter timestamps para string
            for key, value in data.items():
                if hasattr(value, 'isoformat'):
                    data[key] = value.isoformat()
                elif hasattr(value, 'timestamp'):
                    data[key] = value.timestamp()
            docs.append(data)
        print(f"  ✓ {collection_name}: {len(docs)} documentos")
    except Exception as e:
        print(f"  ✗ {collection_name}: Erro - {e}")
    return docs

def main():
    print("\n" + "="*60)
    print("BACKUP FIRESTORE - TAQUES-ERP")
    print("="*60 + "\n")
    
    # Inicializa Firebase
    ensure_firebase_initialized()
    db = get_db()
    
    # Collections para backup
    collections = [
        'vg_casos',
        'prioridades', 
        'users',
        'pessoas',
        'processos',
        'entregaveis',  # Nova collection
    ]
    
    # Estrutura do backup
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'collections': {}
    }
    
    print("Exportando collections:\n")
    for col in collections:
        backup_data['collections'][col] = backup_collection(db, col)
    
    # Salvar arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backups/backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Backup salvo em: {filename}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
