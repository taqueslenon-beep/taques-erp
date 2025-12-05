#!/usr/bin/env python3
"""
Script para forçar limpeza de duplicatas no Firebase SEM confirmação.
CUIDADO: Este script DELETA dados permanentemente!
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

def force_cleanup():
    db = get_db()
    
    print("="*60)
    print("LIMPEZA FORÇADA DE DUPLICATAS")
    print("="*60)
    
    # Carregar todos os casos
    docs = list(db.collection('cases').stream())
    print(f"Total de documentos: {len(docs)}")
    
    # Agrupar por nome+ano
    by_name_year = {}
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        name = data.get('name', '')
        year = data.get('year', '')
        key = f"{name}|{year}"
        
        if key not in by_name_year:
            by_name_year[key] = []
        by_name_year[key].append(doc_id)
    
    # Deletar duplicatas
    total_deleted = 0
    batch = db.batch()
    batch_count = 0
    
    for key, doc_ids in by_name_year.items():
        if len(doc_ids) > 1:
            # Ordenar e manter o primeiro
            doc_ids.sort()
            for doc_id in doc_ids[1:]:
                batch.delete(db.collection('cases').document(doc_id))
                batch_count += 1
                total_deleted += 1
                
                # Commit em lotes de 500 (limite do Firestore)
                if batch_count >= 450:
                    print(f"  Commitando lote... ({total_deleted} deletados até agora)")
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0
    
    # Commit final
    if batch_count > 0:
        batch.commit()
    
    print(f"\n✅ Total deletado: {total_deleted} documentos")
    
    # Verificar resultado
    docs_final = list(db.collection('cases').stream())
    print(f"✅ Casos restantes: {len(docs_final)}")
    
    return total_deleted

if __name__ == '__main__':
    force_cleanup()







