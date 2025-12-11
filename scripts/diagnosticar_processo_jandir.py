#!/usr/bin/env python3
"""
Script de diagnóstico para processo de Jandir José Leismann.

Executa diagnóstico completo para identificar por que um processo não aparece na lista.
"""

import os
import sys

# Adiciona o diretório do projeto ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.pages.processos.diagnostico_processo import (
    diagnosticar_processo_nao_aparece,
    diagnosticar_processo_por_id,
    forcar_invalidacao_cache_e_recarregar,
    verificar_processo_salvo_recentemente
)
from mini_erp.core import get_processes_list, invalidate_cache

def main():
    print("="*80)
    print("DIAGNÓSTICO: Processo de Jandir José Leismann")
    print("="*80)
    print()
    
    # 1. Busca processos recentes (últimos 10 minutos)
    print("1. Buscando processos salvos recentemente (últimos 10 minutos)...")
    processos_recentes = verificar_processo_salvo_recentemente(minutos=10)
    
    if processos_recentes:
        print(f"   ✓ Encontrados {len(processos_recentes)} processo(s) recente(s):")
        for proc in processos_recentes:
            print(f"     - {proc['titulo']} (há {proc['minutos_atras']} min)")
            print(f"       Clientes: {proc['clientes']}")
            print(f"       ID: {proc['id']}")
    else:
        print("   ✗ Nenhum processo salvo nos últimos 10 minutos")
    print()
    
    # 2. Busca processos relacionados a Jandir
    print("2. Buscando processos relacionados a 'Jandir'...")
    diagnostico_jandir = diagnosticar_processo_nao_aparece('Jandir', cliente_esperado='Jandir José Leismann')
    print()
    
    # 3. Busca processos relacionados a 'José Leismann'
    print("3. Buscando processos relacionados a 'José Leismann'...")
    diagnostico_leismann = diagnosticar_processo_nao_aparece('José Leismann')
    print()
    
    # 4. Lista todos os processos com seus clientes
    print("4. Listando todos os processos e seus clientes (primeiros 20)...")
    processos = get_processes_list()
    print(f"   Total de processos no sistema: {len(processos)}")
    
    processos_com_clientes = 0
    processos_sem_clientes = 0
    
    for i, proc in enumerate(processos[:20]):  # Mostra apenas os 20 primeiros
        titulo = proc.get('title', 'Sem título')
        clientes = proc.get('clients', [])
        
        if clientes and len(clientes) > 0:
            processos_com_clientes += 1
            clientes_str = ', '.join(str(c) for c in clientes[:3])  # Mostra apenas 3 primeiros
            if len(clientes) > 3:
                clientes_str += f' (+{len(clientes) - 3} mais)'
            print(f"   [{i+1}] {titulo[:60]}")
            print(f"       Clientes: {clientes_str}")
        else:
            processos_sem_clientes += 1
            print(f"   [{i+1}] {titulo[:60]} ⚠️  SEM CLIENTES")
    
    if len(processos) > 20:
        print(f"   ... e mais {len(processos) - 20} processo(s)")
    
    print(f"\n   Processos com clientes: {processos_com_clientes}")
    print(f"   Processos sem clientes: {processos_sem_clientes}")
    print()
    
    # 5. Resumo de problemas
    print("5. RESUMO DE PROBLEMAS IDENTIFICADOS:")
    print("   " + "-"*76)
    
    todos_problemas = []
    
    if diagnostico_jandir.get('problemas_identificados'):
        todos_problemas.extend(diagnostico_jandir['problemas_identificados'])
    
    if diagnostico_leismann.get('problemas_identificados'):
        todos_problemas.extend(diagnostico_leismann['problemas_identificados'])
    
    if processos_sem_clientes > 0:
        todos_problemas.append({
            'tipo': 'PROCESSOS_SEM_CLIENTES',
            'descricao': f'{processos_sem_clientes} processo(s) sem clientes vinculados',
            'solucao': 'Verificar se campo "clients" está sendo salvo corretamente ao criar processos'
        })
    
    if todos_problemas:
        for i, prob in enumerate(todos_problemas, 1):
            print(f"   [{i}] [{prob['tipo']}] {prob['descricao']}")
            print(f"       Solução: {prob.get('solucao', 'N/A')}")
    else:
        print("   ✓ Nenhum problema identificado!")
    print()
    
    # 6. Recomendações
    print("6. RECOMENDAÇÕES:")
    print("   " + "-"*76)
    
    recomendacoes = []
    
    if processos_sem_clientes > 0:
        recomendacoes.append("Verificar validação de campo 'clients' antes de salvar processo")
        recomendacoes.append("Garantir que modal de processo sempre salve o campo 'clients'")
    
    if todos_problemas:
        for prob in todos_problemas:
            if prob.get('solucao') and prob['solucao'] not in recomendacoes:
                recomendacoes.append(prob['solucao'])
    
    if not recomendacoes:
        recomendacoes.append("Processos parecem estar sendo salvos corretamente")
    
    for i, rec in enumerate(recomendacoes, 1):
        print(f"   {i}. {rec}")
    print()
    
    # 7. Próximos passos
    print("7. PRÓXIMOS PASSOS:")
    print("   " + "-"*76)
    print("   1. Se processo foi criado recentemente, verificar se aparece após:")
    print("      - Invalidar cache: scripts/diagnosticar_processo_jandir.py --invalidate-cache")
    print("      - Recarregar página no navegador")
    print("   2. Se processo tem ID conhecido, diagnosticar especificamente:")
    print("      - python3 scripts/diagnosticar_processo_jandir.py --id PROCESSO_ID")
    print("   3. Verificar Firestore Console para confirmar que processo foi salvo")
    print("   4. Verificar logs do servidor durante criação do processo")
    print()
    
    print("="*80)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("="*80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnostica problema com processo não aparecendo na lista')
    parser.add_argument('--invalidate-cache', action='store_true', help='Invalida cache de processos e clientes')
    parser.add_argument('--id', type=str, help='ID do processo para diagnóstico específico')
    parser.add_argument('--buscar', type=str, help='Texto para buscar no título ou clientes')
    
    args = parser.parse_args()
    
    if args.invalidate_cache:
        print("Invalidando cache...")
        invalidate_cache('processes')
        invalidate_cache('clients')
        print("✓ Cache invalidado!")
        sys.exit(0)
    
    if args.id:
        print(f"Diagnosticando processo específico: {args.id}")
        diagnostico = diagnosticar_processo_por_id(args.id)
        print(f"Existe no Firestore: {diagnostico.get('existe_no_firestore')}")
        print(f"Existe na lista: {diagnostico.get('existe_na_lista')}")
        if diagnostico.get('problemas'):
            print("Problemas:", diagnostico['problemas'])
        sys.exit(0)
    
    if args.buscar:
        diagnostico = diagnosticar_processo_nao_aparece(args.buscar)
        print(f"Processos encontrados no Firestore: {len(diagnostico.get('processos_encontrados_no_firestore', []))}")
        print(f"Processos encontrados na lista: {len(diagnostico.get('processos_encontrados_na_lista', []))}")
        sys.exit(0)
    
    main()








