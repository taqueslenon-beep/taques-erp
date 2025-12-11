#!/usr/bin/env python3
"""
Testa várias queries para ver onde o RECURSO ESPECIAL é excluído.
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

db = get_db()

print("=" * 80)
print("TESTE DE QUERIES - ONDE O RECURSO ESPECIAL DESAPARECE")
print("=" * 80)

# Query 1: TODOS os processos
print("\n[QUERY 1] Todos os processos (sem where, sem limit):")
try:
    todos = list(db.collection('processes').stream())
    encontrado = False
    recurso_doc = None
    
    for doc in todos:
        data = doc.to_dict()
        title = data.get('title', '')
        if 'RECURSO ESPECIAL' in title.upper():
            encontrado = True
            recurso_doc = (doc, data)
            break
    
    print(f"  Total: {len(todos)} documentos")
    print(f"  RECURSO ESPECIAL? {'✓ SIM' if encontrado else '✗ NÃO'}")
    
    if recurso_doc:
        doc, data = recurso_doc
        print(f"    ID: {doc.id}")
        print(f"    Título: {data.get('title')}")
        print(f"    Status: {repr(data.get('status'))}")
except Exception as e:
    print(f"  ✗ Erro: {e}")

# Query 2: Apenas com limit
print("\n[QUERY 2] Com limit(30):")
try:
    limit30 = list(db.collection('processes').limit(30).stream())
    encontrado = any('RECURSO ESPECIAL' in d.to_dict().get('title', '').upper() for d in limit30)
    print(f"  Total: {len(limit30)} documentos")
    print(f"  RECURSO ESPECIAL? {'✓ SIM' if encontrado else '✗ NÃO'}")
except Exception as e:
    print(f"  ✗ Erro: {e}")

# Query 3: Filtrar por status 'Futuro/Previsto'
print("\n[QUERY 3] Status == 'Futuro/Previsto':")
try:
    futuro_previsto = list(db.collection('processes').where('status', '==', 'Futuro/Previsto').stream())
    encontrado = any('RECURSO ESPECIAL' in d.to_dict().get('title', '').upper() for d in futuro_previsto)
    print(f"  Total: {len(futuro_previsto)} documentos")
    print(f"  RECURSO ESPECIAL? {'✓ SIM' if encontrado else '✗ NÃO'}")
except Exception as e:
    print(f"  ✗ Erro: {e}")

# Query 4: Todos os status diferentes
print("\n[QUERY 4] Todos os status únicos no banco:")
try:
    todos = list(db.collection('processes').stream())
    status_valores = {}
    
    for doc in todos:
        data = doc.to_dict()
        status = data.get('status')
        if status is None:
            status = '[None]'
        elif not status:
            status = '[Vazio]'
        
        if status not in status_valores:
            status_valores[status] = []
        status_valores[status].append((doc, data))
    
    for status in sorted(status_valores.keys()):
        docs_com_status = status_valores[status]
        encontrado = any('RECURSO ESPECIAL' in d[1].get('title', '').upper() for d in docs_com_status)
        marker = '✓ CONTÉM RECURSO' if encontrado else ''
        print(f"  '{status}': {len(docs_com_status)} documento(s) {marker}")
        
        if encontrado:
            for doc, data in docs_com_status:
                if 'RECURSO ESPECIAL' in data.get('title', '').upper():
                    print(f"    → {data.get('title')} (ID: {doc.id})")
except Exception as e:
    print(f"  ✗ Erro: {e}")
    import traceback
    traceback.print_exc()

# Query 5: Procurar RECURSO ESPECIAL especificamente
print("\n[QUERY 5] Procurando RECURSO ESPECIAL em todos os documentos:")
try:
    todos = list(db.collection('processes').stream())
    recurso_doc = None
    
    for doc in todos:
        data = doc.to_dict()
        title = data.get('title', '')
        if 'RECURSO ESPECIAL' in title.upper():
            print(f"  ✓ Encontrado!")
            print(f"    ID: {doc.id}")
            print(f"    Título: {data.get('title')}")
            print(f"    Status: {repr(data.get('status'))}")
            print(f"    Status tipo: {type(data.get('status'))}")
            print(f"    Process Type: {repr(data.get('process_type'))}")
            print(f"    Todos os campos: {list(data.keys())}")
            recurso_doc = (doc, data)
            break
    
    if not recurso_doc:
        print(f"  ✗ Não encontrado em nenhum documento")
except Exception as e:
    print(f"  ✗ Erro: {e}")
    import traceback
    traceback.print_exc()

# Query 6: Testar get_processes_list() do core
print("\n[QUERY 6] Testando get_processes_list() do core:")
try:
    from mini_erp.core import get_processes_list
    processos_core = get_processes_list()
    
    encontrado = False
    for proc in processos_core:
        title = proc.get('title', '')
        if 'RECURSO ESPECIAL' in title.upper():
            encontrado = True
            print(f"  ✓ Encontrado via get_processes_list()!")
            print(f"    Título: {proc.get('title')}")
            print(f"    Status: {repr(proc.get('status'))}")
            print(f"    _id: {proc.get('_id')}")
            break
    
    if not encontrado:
        print(f"  ✗ NÃO encontrado via get_processes_list()")
        print(f"  Total retornado: {len(processos_core)} processos")
    
except Exception as e:
    print(f"  ✗ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)








