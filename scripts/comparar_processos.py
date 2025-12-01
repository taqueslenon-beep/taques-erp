#!/usr/bin/env python3
"""
Compara estrutura do "RECURSO ESPECIAL" com processo que funciona.
Objetivo: Identificar diferenças de campos ou tipos.
"""

import json
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

db = get_db()

print("=" * 80)
print("COMPARAÇÃO DE ESTRUTURA")
print("=" * 80)

try:
    # Buscar RECURSO ESPECIAL
    todos_processos = list(db.collection('processes').stream())
    
    recurso_doc = None
    for doc in todos_processos:
        data = doc.to_dict()
        title = data.get('title', '')
        if 'RECURSO ESPECIAL' in title.upper():
            recurso_doc = (doc, data)
            break
    
    # Buscar um processo que funciona (primeiro que não seja RECURSO ESPECIAL)
    funcionando_doc = None
    for doc in todos_processos:
        data = doc.to_dict()
        title = data.get('title', '')
        if 'RECURSO ESPECIAL' not in title.upper() and title:
            funcionando_doc = (doc, data)
            break
    
    if recurso_doc and funcionando_doc:
        recurso_id, recurso_data = recurso_doc
        funcionando_id, funcionando_data = funcionando_doc
        
        print(f"\nPROCESSO 1 (RECURSO ESPECIAL):")
        print(f"  ID: {recurso_id.id}")
        print(f"  Título: {recurso_data.get('title')}")
        print(f"  Status: {repr(recurso_data.get('status'))}")
        print(f"  Process Type: {repr(recurso_data.get('process_type'))}")
        print(f"  Campos: {list(recurso_data.keys())}")
        print(f"  Total de campos: {len(recurso_data)}")
        
        print(f"\nPROCESSO 2 (FUNCIONANDO):")
        print(f"  ID: {funcionando_id.id}")
        print(f"  Título: {funcionando_data.get('title')}")
        print(f"  Status: {repr(funcionando_data.get('status'))}")
        print(f"  Process Type: {repr(funcionando_data.get('process_type'))}")
        print(f"  Campos: {list(funcionando_data.keys())}")
        print(f"  Total de campos: {len(funcionando_data)}")
        
        print(f"\nDIFERENÇAS DE CAMPOS:")
        campos_recurso = set(recurso_data.keys())
        campos_funcionando = set(funcionando_data.keys())
        
        faltando = campos_funcionando - campos_recurso
        extras = campos_recurso - campos_funcionando
        
        if faltando:
            print(f"  ⚠️  Campos que faltam em RECURSO ESPECIAL: {faltando}")
        if extras:
            print(f"  ⚠️  Campos extras em RECURSO ESPECIAL: {extras}")
        if not faltando and not extras:
            print(f"  ✓ Mesmos campos em ambos")
        
        # Comparar cada campo comum
        print(f"\nDETALHES DE CADA CAMPO COMUM:")
        todos_campos = campos_recurso | campos_funcionando
        diferencas = []
        for campo in sorted(todos_campos):
            valor_r = recurso_data.get(campo)
            valor_f = funcionando_data.get(campo)
            
            # Comparação mais inteligente
            if campo == '_id':
                continue  # Ignora ID do documento
            
            if valor_r != valor_f:
                diferencas.append(campo)
                print(f"  {campo}:")
                print(f"    RECURSO:      {repr(valor_r)} (tipo: {type(valor_r).__name__})")
                print(f"    FUNCIONANDO:  {repr(valor_f)} (tipo: {type(valor_f).__name__})")
        
        if not diferencas:
            print(f"  ✓ Nenhuma diferença significativa encontrada")
        
        # Verificar campos críticos
        print(f"\nCAMPOS CRÍTICOS:")
        campos_criticos = ['status', 'process_type', 'title', '_id']
        for campo in campos_criticos:
            valor_r = recurso_data.get(campo)
            valor_f = funcionando_data.get(campo)
            print(f"  {campo}:")
            print(f"    RECURSO:      {repr(valor_r)}")
            print(f"    FUNCIONANDO:  {repr(valor_f)}")
            if valor_r != valor_f:
                print(f"    ⚠️  DIFERENTE!")
        
    elif not recurso_doc:
        print("\n✗ RECURSO ESPECIAL não encontrado no banco!")
    elif not funcionando_doc:
        print("\n✗ Não conseguiu encontrar processo de comparação")
    
except Exception as e:
    print(f"\n✗ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)



