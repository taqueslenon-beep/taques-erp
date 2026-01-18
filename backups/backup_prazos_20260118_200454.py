#!/usr/bin/env python3
"""
Backup da collection 'prazos' do Firestore
Gerado em: 2026-01-18 20:04:54
"""
import json
import sys
from datetime import datetime

# Adiciona o diretório do projeto ao path
sys.path.insert(0, '/Users/lenontaques/Documents/taques-erp')

from mini_erp.firebase_config import get_db

def backup_collection(collection_name: str, output_file: str):
    """Faz backup de uma collection do Firestore para JSON."""
    db = get_db()
    docs = db.collection(collection_name).stream()
    
    data = []
    for doc in docs:
        item = doc.to_dict()
        item['_id'] = doc.id
        # Converter timestamps para ISO format
        for key, value in item.items():
            if hasattr(value, 'timestamp'):
                item[key] = value.timestamp()
        data.append(item)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    return len(data)

if __name__ == '__main__':
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'/Users/lenontaques/Documents/taques-erp/backups/backup_prazos_{timestamp}.json'
    
    print(f"🔄 Iniciando backup da collection 'prazos'...")
    count = backup_collection('prazos', output_file)
    print(f"✅ Backup concluído! {count} documentos salvos em:")
    print(f"   {output_file}")
