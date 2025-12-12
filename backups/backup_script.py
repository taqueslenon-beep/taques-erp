#!/usr/bin/env python3
"""
Script de backup das collections do Firebase Firestore
Projeto: TAQUES-ERP
"""

import json
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.core import get_db

def backup_collections():
    """Exporta collections afetadas para arquivo JSON"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/backup_{timestamp}.json'
    
    db = get_db()
    
    # Collections a fazer backup
    collections = ['vg_casos', 'prioridades', 'users', 'pessoas', 'processos']
    
    backup_data = {
        'timestamp': timestamp,
        'collections': {}
    }
    
    for collection_name in collections:
        try:
            docs = db.collection(collection_name).stream()
            backup_data['collections'][collection_name] = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['_id'] = doc.id
                backup_data['collections'][collection_name].append(doc_data)
            
            count = len(backup_data['collections'][collection_name])
            print(f'✅ {collection_name}: {count} documentos')
        except Exception as e:
            print(f'⚠️  {collection_name}: Erro - {e}')
            backup_data['collections'][collection_name] = []
    
    # Salvar arquivo
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f'\n📁 Backup salvo em: {backup_file}')
    return backup_file

if __name__ == '__main__':
    print('🔄 Iniciando backup do Firebase Firestore...\n')
    backup_collections()
    print('\n✅ Backup concluído!')
