"""
Script de validação de integridade dos processos.

Verifica se todos os processos aparecem em todas as visualizações,
identificando processos "fantasmas" que aparecem apenas em filtros específicos.
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.core import get_processes_list
from mini_erp.firebase_config import get_db


def validar_processos():
    """
    Valida integridade dos processos no Firestore.
    
    Verifica:
    - Se todos os processos têm status válido
    - Se processos aparecem em todas as queries
    - Se há processos "fantasmas" (aparecem em filtro mas não em visualização padrão)
    """
    print("=" * 80)
    print("VALIDAÇÃO DE INTEGRIDADE DOS PROCESSOS")
    print("=" * 80)
    print()
    
    # 1. Buscar todos os processos do Firestore diretamente
    print("1. Buscando todos os processos do Firestore...")
    db = get_db()
    all_docs = list(db.collection('processes').stream())
    all_processes_firestore = []
    for doc in all_docs:
        data = doc.to_dict()
        data['_id'] = doc.id
        all_processes_firestore.append(data)
    
    print(f"   ✓ Total de processos no Firestore: {len(all_processes_firestore)}")
    print()
    
    # 2. Buscar via get_processes_list() (função do core)
    print("2. Buscando processos via get_processes_list()...")
    all_processes_core = get_processes_list()
    print(f"   ✓ Total de processos via core: {len(all_processes_core)}")
    print()
    
    # 3. Verificar se contagens batem
    if len(all_processes_firestore) != len(all_processes_core):
        print(f"   ⚠️  DISCREPÂNCIA: Firestore={len(all_processes_firestore)}, Core={len(all_processes_core)}")
    else:
        print(f"   ✓ Contagens batem: {len(all_processes_firestore)} processos")
    print()
    
    # 4. Buscar processo específico "RECURSO ESPECIAL"
    print("3. Buscando processo 'RECURSO ESPECIAL'...")
    recurso_especial_firestore = None
    recurso_especial_core = None
    
    for proc in all_processes_firestore:
        if 'RECURSO ESPECIAL' in (proc.get('title') or '').upper():
            recurso_especial_firestore = proc
            break
    
    for proc in all_processes_core:
        if 'RECURSO ESPECIAL' in (proc.get('title') or '').upper():
            recurso_especial_core = proc
            break
    
    if recurso_especial_firestore:
        print(f"   ✓ Encontrado no Firestore:")
        print(f"     Título: {recurso_especial_firestore.get('title')}")
        print(f"     Status: '{recurso_especial_firestore.get('status')}'")
        print(f"     Process Type: '{recurso_especial_firestore.get('process_type')}'")
        print(f"     Doc ID: {recurso_especial_firestore.get('_id')}")
    else:
        print(f"   ❌ NÃO encontrado no Firestore!")
    
    if recurso_especial_core:
        print(f"   ✓ Encontrado via get_processes_list():")
        print(f"     Título: {recurso_especial_core.get('title')}")
        print(f"     Status: '{recurso_especial_core.get('status')}'")
        print(f"     Process Type: '{recurso_especial_core.get('process_type')}'")
        print(f"     Doc ID: {recurso_especial_core.get('_id')}")
    else:
        print(f"   ❌ NÃO encontrado via get_processes_list()!")
    
    if recurso_especial_firestore and not recurso_especial_core:
        print()
        print("   🚨 PROBLEMA CRÍTICO: Processo existe no Firestore mas não é retornado por get_processes_list()!")
    print()
    
    # 5. Agrupar processos por status
    print("4. Agrupando processos por status...")
    processos_por_status = {}
    processos_sem_status = []
    
    for proc in all_processes_core:
        status = proc.get('status') or ''
        if not status:
            processos_sem_status.append(proc)
            status = '(sem status)'
        
        if status not in processos_por_status:
            processos_por_status[status] = []
        processos_por_status[status].append(proc)
    
    print(f"   Status encontrados: {list(processos_por_status.keys())}")
    for status, procs in processos_por_status.items():
        print(f"   - {status}: {len(procs)} processos")
    
    if processos_sem_status:
        print(f"   ⚠️  {len(processos_sem_status)} processos sem status:")
        for proc in processos_sem_status:
            print(f"      - {proc.get('title', 'Sem título')} (process_type: {proc.get('process_type')})")
    print()
    
    # 6. Verificar processos com status "Futuro/Previsto"
    print("5. Verificando processos com status 'Futuro/Previsto'...")
    processos_previstos = processos_por_status.get('Futuro/Previsto', [])
    print(f"   ✓ Total: {len(processos_previstos)} processos")
    
    if recurso_especial_core:
        if recurso_especial_core in processos_previstos:
            print(f"   ✓ 'RECURSO ESPECIAL' está na lista de processos previstos")
        else:
            print(f"   ❌ 'RECURSO ESPECIAL' NÃO está na lista de processos previstos!")
            print(f"      Status do processo: '{recurso_especial_core.get('status')}'")
    print()
    
    # 7. Verificar integridade: soma de processos por status deve ser igual ao total
    print("6. Verificando integridade (soma de processos por status)...")
    total_por_status = sum(len(procs) for procs in processos_por_status.values())
    total_geral = len(all_processes_core)
    
    if total_por_status == total_geral:
        print(f"   ✓ Integridade OK: {total_geral} processos = {total_por_status} por status")
    else:
        print(f"   ⚠️  DISCREPÂNCIA: Total={total_geral}, Soma por status={total_por_status}")
        print(f"      Diferença: {abs(total_geral - total_por_status)} processos")
    print()
    
    # 8. Listar todos os processos para validação manual
    print("7. Lista completa de processos (para validação manual):")
    print()
    for i, proc in enumerate(sorted(all_processes_core, key=lambda p: (p.get('title') or '').lower()), 1):
        status = proc.get('status') or '(sem status)'
        title = proc.get('title') or 'Sem título'
        print(f"   {i:2d}. {title[:60]:60s} | Status: {status:20s} | ID: {proc.get('_id', 'N/A')[:20]}")
    
    print()
    print("=" * 80)
    print("VALIDAÇÃO CONCLUÍDA")
    print("=" * 80)
    
    # Resumo final
    erros = []
    if len(all_processes_firestore) != len(all_processes_core):
        erros.append(f"Discrepância entre Firestore ({len(all_processes_firestore)}) e Core ({len(all_processes_core)})")
    
    if recurso_especial_firestore and not recurso_especial_core:
        erros.append("Processo 'RECURSO ESPECIAL' existe no Firestore mas não é retornado pelo Core")
    
    if total_por_status != total_geral:
        erros.append(f"Discrepância na soma de processos por status ({total_por_status} vs {total_geral})")
    
    if processos_sem_status:
        erros.append(f"{len(processos_sem_status)} processos sem status definido")
    
    if erros:
        print()
        print("❌ ERROS ENCONTRADOS:")
        for erro in erros:
            print(f"   - {erro}")
        return False
    else:
        print()
        print("✓ Nenhum erro encontrado. Todos os processos estão íntegros.")
        return True


if __name__ == '__main__':
    try:
        sucesso = validar_processos()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO ao executar validação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)








