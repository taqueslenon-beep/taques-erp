#!/usr/bin/env python3
"""
Extrai TODOS os dados do documento "RECURSO ESPECIAL - STJ" do Firestore.
Propósito: Diagnóstico completo - verificar corrupção, campos ausentes, etc.
"""

import json
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db
from firebase_admin import firestore

print("=" * 80)
print("EXTRAÇÃO COMPLETA - RECURSO ESPECIAL - STJ")
print("=" * 80)
print()

db = get_db()

# BUSCA 1: Por título exato
print("[BUSCA 1] Procurando por título exato 'RECURSO ESPECIAL - STJ - JHONNY - RIO NEGRINHO 2020'...")
try:
    query1 = db.collection('processes').where('title', '==', 'RECURSO ESPECIAL - STJ - JHONNY - RIO NEGRINHO 2020').stream()
    docs1 = list(query1)
    
    if docs1:
        print(f"✓ Encontrado {len(docs1)} documento(s) com título exato")
        for doc in docs1:
            data = doc.to_dict()
            data['_id'] = doc.id
            print(f"\nDocumento ID: {doc.id}")
            print(f"Dados completos:")
            print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    else:
        print("✗ Nenhum documento com título exato encontrado")
except Exception as e:
    print(f"✗ Erro na busca 1: {e}")

# BUSCA 2: Por título parcial (buscar em todos)
print("\n" + "=" * 80)
print("[BUSCA 2] Procurando por título contendo 'RECURSO ESPECIAL' em TODOS os processos...")
try:
    todos_processos = list(db.collection('processes').stream())
    encontrados = []
    
    for doc in todos_processos:
        data = doc.to_dict()
        title = data.get('title', '')
        if 'RECURSO ESPECIAL' in title.upper() or 'RECURSO ESPECIAL' in str(title):
            encontrados.append((doc, data))
    
    if encontrados:
        print(f"✓ Encontrado {len(encontrados)} documento(s) contendo 'RECURSO ESPECIAL'")
        for doc, data in encontrados:
            data['_id'] = doc.id
            print(f"\nDocumento ID: {doc.id}")
            print(f"Título: {data.get('title')}")
            print(f"Status: {data.get('status')}")
            print(f"Status (repr): {repr(data.get('status'))}")
            print(f"Tipo de status: {type(data.get('status'))}")
            print(f"Process Type: {data.get('process_type')}")
            print(f"Todos os campos:")
            print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    else:
        print("✗ Nenhum documento contendo 'RECURSO ESPECIAL' encontrado")
except Exception as e:
    print(f"✗ Erro na busca 2: {e}")
    import traceback
    traceback.print_exc()

# BUSCA 3: Procurar em TODOS os processos
print("\n" + "=" * 80)
print("[BUSCA 3] Verificando TODOS os processos...")
try:
    todos_processos = list(db.collection('processes').stream())
    print(f"Total de processos no banco: {len(todos_processos)}")
    
    print("\nLista de todos os processos:")
    for i, doc in enumerate(todos_processos, 1):
        data = doc.to_dict()
        title = data.get('title', '[SEM TÍTULO]')
        status = data.get('status', '[SEM STATUS]')
        doc_id = doc.id
        print(f"{i:2d}. {title[:60]:60s} | Status: {str(status):20s} | ID: {doc_id[:20]}")
except Exception as e:
    print(f"✗ Erro na busca 3: {e}")
    import traceback
    traceback.print_exc()

# BUSCA 4: Contar por status
print("\n" + "=" * 80)
print("[BUSCA 4] Contagem por status:")
try:
    todos_processos = list(db.collection('processes').stream())
    status_count = {}
    for doc in todos_processos:
        data = doc.to_dict()
        status = data.get('status')
        if status is None:
            status = '[None]'
        elif not status:
            status = '[Vazio]'
        if status not in status_count:
            status_count[status] = 0
        status_count[status] += 1
    
    for status, count in sorted(status_count.items()):
        print(f"  Status '{status}': {count} processo(s)")
except Exception as e:
    print(f"✗ Erro na busca 4: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)





