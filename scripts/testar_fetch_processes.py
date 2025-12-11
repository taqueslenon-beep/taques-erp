#!/usr/bin/env python3
"""
Testa diretamente a função fetch_processes() para ver se retorna RECURSO ESPECIAL.
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar função fetch_processes
from mini_erp.pages.processos.processos_page import fetch_processes

print("=" * 80)
print("TESTE DA FUNÇÃO fetch_processes()")
print("=" * 80)

try:
    rows = fetch_processes()
    
    print(f"\nTotal de processos retornados por fetch_processes(): {len(rows)}")
    
    # Procurar RECURSO ESPECIAL
    recurso_encontrado = None
    for row in rows:
        title = row.get('title', '')
        if 'RECURSO ESPECIAL' in title.upper():
            recurso_encontrado = row
            break
    
    if recurso_encontrado:
        print(f"\n✓ RECURSO ESPECIAL encontrado em fetch_processes()!")
        print(f"  Título: {recurso_encontrado.get('title')}")
        print(f"  Status: {repr(recurso_encontrado.get('status'))}")
        print(f"  _id: {recurso_encontrado.get('_id')}")
        print(f"  Todos os campos da row:")
        for key, value in recurso_encontrado.items():
            print(f"    {key}: {repr(value)}")
    else:
        print(f"\n❌ RECURSO ESPECIAL NÃO encontrado em fetch_processes()!")
        print(f"\nLista de todos os processos retornados:")
        for i, row in enumerate(rows, 1):
            title = row.get('title', '[SEM TÍTULO]')
            status = row.get('status', '[SEM STATUS]')
            print(f"  {i:2d}. {title[:60]:60s} | Status: {status}")
    
    # Verificar se há algum processo sendo filtrado
    print(f"\nVerificando processos por status:")
    status_count = {}
    for row in rows:
        status = row.get('status') or '[Vazio]'
        if status not in status_count:
            status_count[status] = 0
        status_count[status] += 1
    
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count} processo(s)")
    
except Exception as e:
    print(f"\n❌ Erro ao executar fetch_processes(): {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)








