#!/usr/bin/env python3
"""
Script para limpar casos duplicados no Firebase.
Mantém apenas o caso mais antigo (menor doc_id) para cada nome+ano.

Execute: python scripts/cleanup_duplicate_cases.py

ATENÇÃO: Este script DELETA dados. Faça backup antes de executar!
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

def cleanup_duplicates(dry_run=True):
    """
    Remove casos duplicados do Firebase.
    
    Args:
        dry_run: Se True, apenas mostra o que seria deletado sem deletar de fato.
    """
    db = get_db()
    
    print("\n" + "="*60)
    print("LIMPEZA DE CASOS DUPLICADOS")
    print("="*60)
    print(f"Modo: {'SIMULAÇÃO (dry_run)' if dry_run else '⚠️  EXECUÇÃO REAL - DELETANDO!'}")
    print()
    
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
        by_name_year[key].append({
            'doc_id': doc_id,
            'title': data.get('title', ''),
            'case_type': data.get('case_type', ''),
            'data': data
        })
    
    # Encontrar duplicatas
    duplicates_to_delete = []
    for key, items in by_name_year.items():
        if len(items) > 1:
            # Ordenar por doc_id para manter o mais antigo
            items.sort(key=lambda x: x['doc_id'])
            
            # Manter o primeiro, marcar os outros para deleção
            keep = items[0]
            to_delete = items[1:]
            
            name, year = key.split('|')
            print(f"\n📋 Duplicata encontrada: '{name}' / {year}")
            print(f"   ✅ MANTER: {keep['doc_id']} - {keep['title']}")
            for item in to_delete:
                print(f"   ❌ DELETAR: {item['doc_id']} - {item['title']}")
                duplicates_to_delete.append(item)
    
    if not duplicates_to_delete:
        print("\n✅ Nenhuma duplicata encontrada!")
        return
    
    print(f"\n{'='*60}")
    print(f"Total de documentos a deletar: {len(duplicates_to_delete)}")
    print(f"{'='*60}")
    
    if dry_run:
        print("\n⚠️  Modo SIMULAÇÃO - nada foi deletado.")
        print("Para deletar de verdade, execute:")
        print("  python scripts/cleanup_duplicate_cases.py --execute")
        return
    
    # Confirmar antes de deletar
    confirm = input("\n⚠️  ATENÇÃO: Isso irá DELETAR os documentos acima. Continuar? (digite 'SIM' para confirmar): ")
    if confirm != 'SIM':
        print("Operação cancelada.")
        return
    
    # Deletar duplicatas
    print("\nDeletando...")
    for item in duplicates_to_delete:
        doc_id = item['doc_id']
        try:
            db.collection('cases').document(doc_id).delete()
            print(f"  ✅ Deletado: {doc_id}")
        except Exception as e:
            print(f"  ❌ Erro ao deletar {doc_id}: {e}")
    
    print(f"\n✅ Limpeza concluída! {len(duplicates_to_delete)} documentos deletados.")

if __name__ == '__main__':
    # Verifica se deve executar de verdade
    execute = '--execute' in sys.argv
    cleanup_duplicates(dry_run=not execute)







