#!/usr/bin/env python3
"""
Script para verificar se os números exibidos no painel estão corretos e sincronizados.

Compara:
1. Total de casos vs casos reais no banco
2. Casos por tipo (Antigo/Novo/Futuro)
3. Total de processos vs processos reais no banco
4. Processos por status (Ativos, Concluídos, Previstos)
5. Acompanhamentos de terceiros
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.core import get_cases_list, get_processes_list, invalidate_cache
from mini_erp.pages.processos.database import contar_todos_acompanhamentos
from mini_erp.pages.painel.helpers import get_case_type
from collections import Counter


def verificar_casos():
    """Verifica contagens de casos."""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE CASOS")
    print("="*60)
    
    # Força atualização do cache
    invalidate_cache('cases')
    casos = get_cases_list()
    
    total_casos = len(casos)
    print(f"\n✓ Total de Casos no banco: {total_casos}")
    
    # Contar por tipo
    tipos = Counter()
    for caso in casos:
        tipo = get_case_type(caso)
        tipos[tipo] += 1
    
    print(f"\n✓ Distribuição por tipo:")
    print(f"  - Antigos: {tipos.get('Antigo', 0)}")
    print(f"  - Novos: {tipos.get('Novo', 0)}")
    print(f"  - Futuros: {tipos.get('Futuro', 0)}")
    
    soma_tipos = sum(tipos.values())
    if soma_tipos != total_casos:
        print(f"\n⚠️  ATENÇÃO: Soma dos tipos ({soma_tipos}) != Total ({total_casos})")
    else:
        print(f"\n✓ Soma dos tipos confere com total: {soma_tipos}")
    
    return {
        'total': total_casos,
        'antigos': tipos.get('Antigo', 0),
        'novos': tipos.get('Novo', 0),
        'futuros': tipos.get('Futuro', 0)
    }


def verificar_processos():
    """Verifica contagens de processos."""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE PROCESSOS")
    print("="*60)
    
    # Força atualização do cache
    invalidate_cache('processes')
    processos = get_processes_list()
    
    total_processos = len(processos)
    print(f"\n✓ Total de Processos no banco: {total_processos}")
    
    # Contar por status
    status_concluidos = {'Concluído', 'Concluído com pendências'}
    status_ativos = {'Em andamento', 'Em monitoramento'}
    status_previstos = {'Futuro/Previsto'}
    
    processos_concluidos = sum(1 for p in processos if p.get('status') in status_concluidos)
    processos_ativos = sum(1 for p in processos if p.get('status') in status_ativos)
    processos_previstos = sum(1 for p in processos if p.get('status') in status_previstos)
    
    print(f"\n✓ Processos Concluídos: {processos_concluidos}")
    print(f"  (Status: 'Concluído' ou 'Concluído com pendências')")
    
    print(f"\n✓ Processos Ativos: {processos_ativos}")
    print(f"  (Status: 'Em andamento' ou 'Em monitoramento')")
    
    print(f"\n✓ Processos Previstos: {processos_previstos}")
    print(f"  (Status: 'Futuro/Previsto')")
    
    # Verificar se a soma faz sentido
    soma_categorias = processos_concluidos + processos_ativos + processos_previstos
    outros_status = total_processos - soma_categorias
    
    if outros_status > 0:
        print(f"\n⚠️  ATENÇÃO: {outros_status} processos com outros status não categorizados")
        # Mostrar quais são os outros status
        outros = Counter(p.get('status', 'Sem status') for p in processos 
                       if p.get('status') not in status_concluidos 
                       and p.get('status') not in status_ativos 
                       and p.get('status') not in status_previstos)
        print(f"  Status encontrados: {dict(outros)}")
    else:
        print(f"\n✓ Todos os processos estão categorizados")
    
    # Verificar se há processos deletados (soft delete)
    processos_deletados = sum(1 for p in processos if p.get('isDeleted') is True)
    if processos_deletados > 0:
        print(f"\n⚠️  ATENÇÃO: {processos_deletados} processos marcados como deletados (isDeleted=True)")
        print(f"  (Esses processos NÃO devem aparecer no painel)")
    
    return {
        'total': total_processos,
        'concluidos': processos_concluidos,
        'ativos': processos_ativos,
        'previstos': processos_previstos,
        'outros': outros_status,
        'deletados': processos_deletados
    }


def verificar_acompanhamentos():
    """Verifica contagem de acompanhamentos de terceiros."""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE ACOMPANHAMENTOS DE TERCEIROS")
    print("="*60)
    
    try:
        total_acompanhamentos = contar_todos_acompanhamentos()
        print(f"\n✓ Total de Acompanhamentos de Terceiros: {total_acompanhamentos}")
        return {'total': total_acompanhamentos}
    except Exception as e:
        print(f"\n❌ Erro ao contar acompanhamentos: {e}")
        import traceback
        traceback.print_exc()
        return {'total': 0, 'erro': str(e)}


def verificar_sincronizacao():
    """Verifica se há problemas de sincronização (cache vs banco)."""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE SINCRONIZAÇÃO (CACHE)")
    print("="*60)
    
    # Primeira leitura (pode usar cache)
    casos_cache = get_cases_list()
    processos_cache = get_processes_list()
    
    # Força invalidação e lê novamente
    invalidate_cache('cases')
    invalidate_cache('processes')
    
    casos_fresh = get_cases_list()
    processos_fresh = get_processes_list()
    
    print(f"\n✓ Casos:")
    print(f"  - Com cache: {len(casos_cache)}")
    print(f"  - Sem cache (fresh): {len(casos_fresh)}")
    
    if len(casos_cache) != len(casos_fresh):
        print(f"  ⚠️  DIFERENÇA DETECTADA! Cache pode estar desatualizado.")
    else:
        print(f"  ✓ Cache sincronizado")
    
    print(f"\n✓ Processos:")
    print(f"  - Com cache: {len(processos_cache)}")
    print(f"  - Sem cache (fresh): {len(processos_fresh)}")
    
    if len(processos_cache) != len(processos_fresh):
        print(f"  ⚠️  DIFERENÇA DETECTADA! Cache pode estar desatualizado.")
    else:
        print(f"  ✓ Cache sincronizado")
    
    print(f"\n💡 O cache tem duração de 5 minutos (300 segundos).")
    print(f"   Se você acabou de adicionar/remover dados, pode levar até 5 min para atualizar.")


def main():
    """Executa todas as verificações."""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE NÚMEROS DO PAINEL")
    print("="*60)
    print("\nEste script verifica se os números exibidos no painel estão corretos.")
    print("Compara os dados do banco com os cálculos esperados.\n")
    
    try:
        # Verificações
        dados_casos = verificar_casos()
        dados_processos = verificar_processos()
        dados_acompanhamentos = verificar_acompanhamentos()
        verificar_sincronizacao()
        
        # Resumo final
        print("\n" + "="*60)
        print("RESUMO FINAL")
        print("="*60)
        print(f"\n📊 Números que devem aparecer no painel:")
        print(f"\n  CASOS:")
        print(f"    - Total: {dados_casos['total']}")
        print(f"    - Antigos: {dados_casos['antigos']}")
        print(f"    - Novos: {dados_casos['novos']}")
        print(f"    - Futuros: {dados_casos['futuros']}")
        
        print(f"\n  PROCESSOS:")
        print(f"    - Total: {dados_processos['total']}")
        print(f"    - Ativos: {dados_processos['ativos']}")
        print(f"    - Concluídos: {dados_processos['concluidos']}")
        print(f"    - Previstos: {dados_processos['previstos']}")
        print(f"    - Acompanhamentos de Terceiros: {dados_acompanhamentos['total']}")
        
        if dados_processos['outros'] > 0:
            print(f"\n  ⚠️  {dados_processos['outros']} processos com status não categorizado")
        
        if dados_processos['deletados'] > 0:
            print(f"\n  ⚠️  {dados_processos['deletados']} processos deletados (não aparecem no painel)")
        
        print("\n" + "="*60)
        print("✓ Verificação concluída!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante verificação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()








