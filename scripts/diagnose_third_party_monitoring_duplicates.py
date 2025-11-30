#!/usr/bin/env python3
"""
Script de diagnóstico de duplicatas em Acompanhamentos de Terceiros.

Uso:
    python scripts/diagnose_third_party_monitoring_duplicates.py
"""
import sys
import os
from collections import defaultdict
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos do projeto
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from mini_erp.firebase_config import get_db

def main():
    """Executa o diagnóstico de duplicatas."""
    print("=" * 70)
    print("DIAGNÓSTICO DE DUPLICATAS DE ACOMPANHAMENTOS DE TERCEIROS")
    print("=" * 70)
    print()

    try:
        db = get_db()
        print("🔍 Conectado ao Firestore...")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firestore: {e}")
        return 1

    # 1. Auditoria de Dados Existentes
    print("🔍 Listando todos os acompanhamentos...")
    try:
        monitoring_ref = db.collection('third_party_monitoring')
        all_monitorings = list(monitoring_ref.stream())
        total_records = len(all_monitorings)
        print(f"   Total de registros encontrados: {total_records}")
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        return 1

    if not all_monitorings:
        print("\n✅ Nenhum acompanhamento encontrado.")
        return 0

    # Estruturas para detecção de duplicatas
    by_process_case = defaultdict(list)
    by_id = defaultdict(list)
    
    all_data = []
    for doc in all_monitorings:
        doc_data = doc.to_dict()
        doc_data['_id'] = doc.id
        all_data.append(doc_data)
        
        # Agrupa por ID (para checar IDs duplicados)
        by_id[doc.id].append(doc_data)

        # Agrupa por processo_id e caso_id
        processo_id = doc_data.get('processo_id')
        caso_id = doc_data.get('caso_id')
        if processo_id and caso_id:
            by_process_case[(processo_id, caso_id)].append(doc_data)
        else:
            # Lidar com registros sem processo_id ou caso_id se necessário
            pass

    # 2. Detectar duplicatas
    duplicate_groups_by_process_case = {k: v for k, v in by_process_case.items() if len(v) > 1}
    duplicate_ids = {k: v for k, v in by_id.items() if len(v) > 1}

    print("\n" + "=" * 70)
    print("RELATÓRIO DE DUPLICATAS")
    print("=" * 70)
    
    print(f"\n📊 RESUMO:")
    print(f"   - Total de registros analisados: {total_records}")
    
    if not duplicate_groups_by_process_case and not duplicate_ids:
        print("\n✅ Nenhuma duplicata encontrada! O sistema está íntegro.")
        return 0

    # Relatório de duplicatas por (processo_id, caso_id)
    if duplicate_groups_by_process_case:
        total_duplicates_by_process = sum(len(v) for v in duplicate_groups_by_process_case.values())
        print(f"\n🔴 Encontrados {len(duplicate_groups_by_process_case)} grupos de duplicatas por (processo_id, caso_id):")
        print(f"   - Total de registros duplicados (neste critério): {total_duplicates_by_process}")
        
        for (processo_id, caso_id), items in duplicate_groups_by_process_case.items():
            print(f"\n   - Grupo (Processo: {processo_id}, Caso: {caso_id}) - {len(items)} registros")
            for item in sorted(items, key=lambda x: x.get('data_criacao') or ''):
                created_at = item.get('data_criacao', 'N/A')
                print(f"     - ID: {item.get('_id')} | Criado em: {created_at}")
    else:
        print("\n✅ Nenhuma duplicata por (processo_id, caso_id) encontrada.")
        
    # Relatório de duplicatas por _id (BUG crítico)
    if duplicate_ids:
        print(f"\n🚨🚨 CRÍTICO: Encontrados {len(duplicate_ids)} IDs duplicados!")
        for doc_id, items in duplicate_ids.items():
            print(f"   - ID: {doc_id} aparece {len(items)} vezes.")
    else:
        print("\n✅ Nenhum ID de documento duplicado encontrado.")

    print("\n" + "=" * 70)
    print("PRÓXIMOS PASSOS")
    print("=" * 70)
    print("\n1. Analise o relatório acima para entender a extensão das duplicatas.")
    print("2. O próximo passo será implementar a lógica de limpeza (remoção de duplicatas).")

    return 0

if __name__ == '__main__':
    sys.exit(main())
