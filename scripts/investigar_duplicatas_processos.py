#!/usr/bin/env python3
"""
Script de Investigação de Duplicação de Dados - Módulo Processos

Este script investiga profundamente possíveis duplicações de processos no sistema:
1. Verifica duplicatas no Firestore (coleção 'processes')
2. Analisa cache em memória do frontend
3. Verifica consultas duplicadas
4. Analisa processos suspeitos específicos
5. Gera relatório completo com findings

USO:
    python scripts/investigar_duplicatas_processos.py
"""

import sys
import os
from typing import Dict, List, Any, Set
from collections import defaultdict
from datetime import datetime

# Adiciona o diretório raiz ao path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mini_erp.firebase_config import get_db
from mini_erp.core import get_processes_list, invalidate_cache
# Importa cache diretamente do módulo core
import mini_erp.core as core_module


# =============================================================================
# PROCESSOS SUSPEITOS PARA INVESTIGAÇÃO ESPECÍFICA
# =============================================================================

SUSPECT_PROCESSES = [
    {
        'title_pattern': 'AIA 137428',
        'client_pattern': 'REFLORESTA',
        'date_pattern': '03/02/2020',
        'status': 'Em andamento'
    },
    {
        'title_pattern': 'AIA 39820-A',
        'client_pattern': 'LUCIANE',
        'date_pattern': '12/01/2016',
        'status': 'Concluído'
    },
    {
        'title_pattern': 'AIA 39821-A',
        'client_pattern': 'EM APP LUCIANE',
        'date_pattern': '12/01/2020',
        'status': 'Concluído'
    },
    {
        'number_pattern': 'PMSC/46545/2020',
        'date_pattern': '25/08/2020'
    }
]


# =============================================================================
# FUNÇÕES DE INVESTIGAÇÃO
# =============================================================================

def get_all_processes_from_firestore() -> List[Dict[str, Any]]:
    """
    Busca TODOS os processos diretamente do Firestore, ignorando cache.
    
    Returns:
        Lista de processos com _id incluído
    """
    try:
        db = get_db()
        docs = db.collection('processes').stream()
        
        processes = []
        for doc in docs:
            data = doc.to_dict()
            data['_id'] = doc.id
            data['_firestore_id'] = doc.id  # Alias para clareza
            processes.append(data)
        
        return processes
    except Exception as e:
        print(f"❌ Erro ao buscar processos do Firestore: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_processes_from_cache() -> List[Dict[str, Any]]:
    """
    Obtém processos do cache em memória (se existir).
    
    Returns:
        Lista de processos do cache ou lista vazia
    """
    try:
        # Acessa cache através do módulo core
        cache = getattr(core_module, '_cache', {})
        if 'processes' in cache:
            return cache['processes']
        return []
    except Exception as e:
        print(f"⚠️  Erro ao acessar cache: {e}")
        return []


def find_duplicates_by_field(processes: List[Dict], field: str) -> Dict[str, List[Dict]]:
    """
    Encontra processos duplicados por um campo específico.
    
    Args:
        processes: Lista de processos
        field: Campo para verificar duplicação
    
    Returns:
        Dicionário {valor_do_campo: [processos_com_esse_valor]}
    """
    by_field = defaultdict(list)
    
    for proc in processes:
        value = proc.get(field)
        if value:
            # Normaliza para comparação
            if isinstance(value, str):
                value = value.strip().upper()
            by_field[value].append(proc)
    
    # Retorna apenas grupos com mais de 1 processo
    duplicates = {k: v for k, v in by_field.items() if len(v) > 1}
    return duplicates


def find_duplicates_by_multiple_fields(processes: List[Dict], fields: List[str]) -> Dict[str, List[Dict]]:
    """
    Encontra processos duplicados por combinação de campos.
    
    Args:
        processes: Lista de processos
        fields: Lista de campos para combinar
    
    Returns:
        Dicionário {chave_combinada: [processos_com_essa_combinacao]}
    """
    by_combo = defaultdict(list)
    
    for proc in processes:
        values = []
        for field in fields:
            value = proc.get(field)
            if isinstance(value, str):
                value = value.strip().upper()
            elif isinstance(value, list):
                # Para arrays, usa o primeiro valor ou string vazia
                value = str(value[0]).strip().upper() if value else ''
            values.append(str(value) if value else '')
        
        key = '|'.join(values)
        if key and key != '|':  # Ignora chaves vazias
            by_combo[key].append(proc)
    
    # Retorna apenas grupos com mais de 1 processo
    duplicates = {k: v for k, v in by_combo.items() if len(v) > 1}
    return duplicates


def analyze_suspect_processes(processes: List[Dict]) -> Dict[str, Any]:
    """
    Analisa processos suspeitos específicos mencionados pelo usuário.
    
    Args:
        processes: Lista de todos os processos
    
    Returns:
        Dicionário com resultados da análise
    """
    results = {
        'found': [],
        'not_found': [],
        'duplicates': []
    }
    
    for suspect in SUSPECT_PROCESSES:
        matches = []
        
        for proc in processes:
            title = (proc.get('title') or '').upper()
            number = (proc.get('number') or '').upper()
            client = str(proc.get('client') or proc.get('clients') or '').upper()
            date = str(proc.get('data_abertura') or proc.get('date') or '').upper()
            status = (proc.get('status') or '').upper()
            
            # Verifica padrões
            matches_pattern = False
            
            if suspect.get('title_pattern'):
                if suspect['title_pattern'].upper() in title:
                    matches_pattern = True
            
            if suspect.get('number_pattern'):
                if suspect['number_pattern'].upper() in number:
                    matches_pattern = True
            
            if suspect.get('client_pattern'):
                if suspect['client_pattern'].upper() in client:
                    matches_pattern = True
            
            if matches_pattern:
                matches.append({
                    '_id': proc.get('_id'),
                    'title': proc.get('title'),
                    'number': proc.get('number'),
                    'client': proc.get('client') or proc.get('clients'),
                    'date': proc.get('data_abertura') or proc.get('date'),
                    'status': proc.get('status'),
                    'all_fields': proc
                })
        
        if matches:
            if len(matches) > 1:
                results['duplicates'].append({
                    'suspect': suspect,
                    'matches': matches
                })
            else:
                results['found'].append({
                    'suspect': suspect,
                    'match': matches[0]
                })
        else:
            results['not_found'].append(suspect)
    
    return results


def analyze_cache_state() -> Dict[str, Any]:
    """
    Analisa o estado do cache em memória.
    
    Returns:
        Dicionário com informações do cache
    """
    try:
        cache = getattr(core_module, '_cache', {})
        cache_timestamp = getattr(core_module, '_cache_timestamp', {})
    except:
        cache = {}
        cache_timestamp = {}
    
    cache_info = {
        'has_cache': 'processes' in cache,
        'cache_size': 0,
        'cache_timestamp': None,
        'cache_age_seconds': None,
        'cache_duration': 300  # 5 minutos padrão
    }
    
    if cache_info['has_cache']:
        cached_processes = cache['processes']
        cache_info['cache_size'] = len(cached_processes)
        
        if 'processes' in cache_timestamp:
            cache_info['cache_timestamp'] = cache_timestamp['processes']
            import time
            cache_info['cache_age_seconds'] = time.time() - cache_info['cache_timestamp']
            cache_info['is_expired'] = cache_info['cache_age_seconds'] > cache_info['cache_duration']
    
    return cache_info


def compare_firestore_vs_cache(firestore_processes: List[Dict], cache_processes: List[Dict]) -> Dict[str, Any]:
    """
    Compara processos do Firestore com processos do cache.
    
    Args:
        firestore_processes: Processos do Firestore
        cache_processes: Processos do cache
    
    Returns:
        Dicionário com diferenças encontradas
    """
    comparison = {
        'firestore_count': len(firestore_processes),
        'cache_count': len(cache_processes),
        'count_difference': 0,
        'ids_in_firestore_not_in_cache': [],
        'ids_in_cache_not_in_firestore': [],
        'same_count': False
    }
    
    comparison['count_difference'] = abs(comparison['firestore_count'] - comparison['cache_count'])
    comparison['same_count'] = comparison['count_difference'] == 0
    
    # Cria sets de IDs
    firestore_ids = {p.get('_id') for p in firestore_processes if p.get('_id')}
    cache_ids = {p.get('_id') for p in cache_processes if p.get('_id')}
    
    comparison['ids_in_firestore_not_in_cache'] = list(firestore_ids - cache_ids)
    comparison['ids_in_cache_not_in_firestore'] = list(cache_ids - firestore_ids)
    
    return comparison


def generate_report(
    firestore_processes: List[Dict],
    cache_processes: List[Dict],
    duplicates_by_title: Dict,
    duplicates_by_number: Dict,
    duplicates_by_combo: Dict,
    suspect_analysis: Dict,
    cache_state: Dict,
    comparison: Dict
) -> str:
    """
    Gera relatório completo em texto.
    
    Returns:
        String com relatório formatado
    """
    report = []
    report.append("=" * 80)
    report.append("RELATÓRIO DE INVESTIGAÇÃO - DUPLICAÇÃO DE PROCESSOS")
    report.append("=" * 80)
    report.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append("")
    
    # 1. RESUMO EXECUTIVO
    report.append("=" * 80)
    report.append("1. RESUMO EXECUTIVO")
    report.append("=" * 80)
    report.append(f"Total de processos no Firestore: {len(firestore_processes)}")
    report.append(f"Total de processos no cache: {len(cache_processes)}")
    report.append(f"Duplicatas por título: {len(duplicates_by_title)} grupos")
    report.append(f"Duplicatas por número: {len(duplicates_by_number)} grupos")
    report.append(f"Duplicatas por combinação (título+número+data): {len(duplicates_by_combo)} grupos")
    report.append("")
    
    # 2. ESTADO DO CACHE
    report.append("=" * 80)
    report.append("2. ESTADO DO CACHE EM MEMÓRIA")
    report.append("=" * 80)
    report.append(f"Cache existe: {'Sim' if cache_state['has_cache'] else 'Não'}")
    if cache_state['has_cache']:
        report.append(f"Tamanho do cache: {cache_state['cache_size']} processos")
        if cache_state['cache_timestamp']:
            report.append(f"Timestamp do cache: {datetime.fromtimestamp(cache_state['cache_timestamp']).strftime('%d/%m/%Y %H:%M:%S')}")
            report.append(f"Idade do cache: {cache_state['cache_age_seconds']:.1f} segundos ({cache_state['cache_age_seconds']/60:.1f} minutos)")
            report.append(f"Cache expirado: {'Sim' if cache_state.get('is_expired') else 'Não'}")
    report.append("")
    
    # 3. COMPARAÇÃO FIRESTORE vs CACHE
    report.append("=" * 80)
    report.append("3. COMPARAÇÃO FIRESTORE vs CACHE")
    report.append("=" * 80)
    report.append(f"Processos no Firestore: {comparison['firestore_count']}")
    report.append(f"Processos no cache: {comparison['cache_count']}")
    report.append(f"Diferença: {comparison['count_difference']}")
    
    if comparison['ids_in_firestore_not_in_cache']:
        report.append(f"\n⚠️  IDs no Firestore mas NÃO no cache ({len(comparison['ids_in_firestore_not_in_cache'])}):")
        for doc_id in comparison['ids_in_firestore_not_in_cache'][:10]:
            proc = next((p for p in firestore_processes if p.get('_id') == doc_id), None)
            title = proc.get('title', 'Sem título') if proc else 'N/A'
            report.append(f"  - {doc_id}: {title}")
        if len(comparison['ids_in_firestore_not_in_cache']) > 10:
            report.append(f"  ... e mais {len(comparison['ids_in_firestore_not_in_cache']) - 10} processos")
    
    if comparison['ids_in_cache_not_in_firestore']:
        report.append(f"\n⚠️  IDs no cache mas NÃO no Firestore ({len(comparison['ids_in_cache_not_in_firestore'])}):")
        for doc_id in comparison['ids_in_cache_not_in_firestore'][:10]:
            proc = next((p for p in cache_processes if p.get('_id') == doc_id), None)
            title = proc.get('title', 'Sem título') if proc else 'N/A'
            report.append(f"  - {doc_id}: {title}")
        if len(comparison['ids_in_cache_not_in_firestore']) > 10:
            report.append(f"  ... e mais {len(comparison['ids_in_cache_not_in_firestore']) - 10} processos")
    
    report.append("")
    
    # 4. DUPLICATAS POR TÍTULO
    report.append("=" * 80)
    report.append("4. DUPLICATAS POR TÍTULO")
    report.append("=" * 80)
    if duplicates_by_title:
        report.append(f"⚠️  ENCONTRADAS {len(duplicates_by_title)} GRUPOS DE DUPLICATAS POR TÍTULO")
        for title, procs in list(duplicates_by_title.items())[:20]:
            report.append(f"\n  Título: '{title}' ({len(procs)} ocorrências)")
            for proc in procs:
                report.append(f"    - ID: {proc.get('_id')} | Número: {proc.get('number', 'N/A')} | Status: {proc.get('status', 'N/A')}")
        if len(duplicates_by_title) > 20:
            report.append(f"\n  ... e mais {len(duplicates_by_title) - 20} grupos")
    else:
        report.append("✅ Nenhuma duplicata por título encontrada")
    report.append("")
    
    # 5. DUPLICATAS POR NÚMERO
    report.append("=" * 80)
    report.append("5. DUPLICATAS POR NÚMERO DE PROCESSO")
    report.append("=" * 80)
    if duplicates_by_number:
        report.append(f"⚠️  ENCONTRADAS {len(duplicates_by_number)} GRUPOS DE DUPLICATAS POR NÚMERO")
        for number, procs in list(duplicates_by_number.items())[:20]:
            report.append(f"\n  Número: '{number}' ({len(procs)} ocorrências)")
            for proc in procs:
                report.append(f"    - ID: {proc.get('_id')} | Título: {proc.get('title', 'N/A')} | Status: {proc.get('status', 'N/A')}")
        if len(duplicates_by_number) > 20:
            report.append(f"\n  ... e mais {len(duplicates_by_number) - 20} grupos")
    else:
        report.append("✅ Nenhuma duplicata por número encontrada")
    report.append("")
    
    # 6. DUPLICATAS POR COMBINAÇÃO
    report.append("=" * 80)
    report.append("6. DUPLICATAS POR COMBINAÇÃO (Título + Número + Data)")
    report.append("=" * 80)
    if duplicates_by_combo:
        report.append(f"⚠️  ENCONTRADAS {len(duplicates_by_combo)} GRUPOS DE DUPLICATAS POR COMBINAÇÃO")
        for combo, procs in list(duplicates_by_combo.items())[:10]:
            parts = combo.split('|')
            report.append(f"\n  Combinação: Título={parts[0]}, Número={parts[1]}, Data={parts[2]} ({len(procs)} ocorrências)")
            for proc in procs:
                report.append(f"    - ID: {proc.get('_id')} | Status: {proc.get('status', 'N/A')}")
        if len(duplicates_by_combo) > 10:
            report.append(f"\n  ... e mais {len(duplicates_by_combo) - 10} grupos")
    else:
        report.append("✅ Nenhuma duplicata por combinação encontrada")
    report.append("")
    
    # 7. ANÁLISE DE PROCESSOS SUSPEITOS
    report.append("=" * 80)
    report.append("7. ANÁLISE DE PROCESSOS SUSPEITOS ESPECÍFICOS")
    report.append("=" * 80)
    
    if suspect_analysis['found']:
        report.append(f"\n✅ Processos encontrados (sem duplicatas): {len(suspect_analysis['found'])}")
        for item in suspect_analysis['found']:
            match = item['match']
            report.append(f"  - {match.get('title')} (ID: {match.get('_id')})")
    
    if suspect_analysis['duplicates']:
        report.append(f"\n⚠️  PROCESSOS SUSPEITOS COM DUPLICATAS: {len(suspect_analysis['duplicates'])}")
        for item in suspect_analysis['duplicates']:
            suspect = item['suspect']
            matches = item['matches']
            report.append(f"\n  Padrão: {suspect}")
            report.append(f"  Encontrados {len(matches)} processos:")
            for match in matches:
                report.append(f"    - ID: {match.get('_id')}")
                report.append(f"      Título: {match.get('title')}")
                report.append(f"      Número: {match.get('number', 'N/A')}")
                report.append(f"      Cliente: {match.get('client', 'N/A')}")
                report.append(f"      Data: {match.get('date', 'N/A')}")
                report.append(f"      Status: {match.get('status', 'N/A')}")
    
    if suspect_analysis['not_found']:
        report.append(f"\n❌ Processos não encontrados: {len(suspect_analysis['not_found'])}")
        for suspect in suspect_analysis['not_found']:
            report.append(f"  - {suspect}")
    
    report.append("")
    
    # 8. RECOMENDAÇÕES
    report.append("=" * 80)
    report.append("8. RECOMENDAÇÕES")
    report.append("=" * 80)
    
    has_duplicates = len(duplicates_by_title) > 0 or len(duplicates_by_number) > 0 or len(duplicates_by_combo) > 0
    has_cache_issues = not comparison['same_count'] or comparison['ids_in_firestore_not_in_cache'] or comparison['ids_in_cache_not_in_firestore']
    
    if has_duplicates:
        report.append("\n🔴 SEVERIDADE: CRÍTICA")
        report.append("   Duplicatas encontradas no Firestore!")
        report.append("   AÇÕES NECESSÁRIAS:")
        report.append("   1. Revisar cada grupo de duplicatas manualmente")
        report.append("   2. Identificar qual registro deve ser mantido")
        report.append("   3. Consolidar dados se necessário")
        report.append("   4. Executar script de limpeza (após backup)")
        report.append("   5. Implementar validação de unicidade no salvamento")
    elif has_cache_issues:
        report.append("\n🟡 SEVERIDADE: MODERADA")
        report.append("   Problemas de sincronização entre Firestore e cache")
        report.append("   AÇÕES NECESSÁRIAS:")
        report.append("   1. Invalidar cache manualmente")
        report.append("   2. Verificar lógica de invalidação de cache")
        report.append("   3. Considerar reduzir TTL do cache")
    else:
        report.append("\n🟢 SEVERIDADE: BAIXA")
        report.append("   Nenhuma duplicata crítica encontrada")
        report.append("   Sistema parece estar funcionando corretamente")
    
    report.append("")
    
    # 9. QUERIES PARA TESTE NO FIREBASE CONSOLE
    report.append("=" * 80)
    report.append("9. QUERIES PARA TESTE NO FIREBASE CONSOLE")
    report.append("=" * 80)
    report.append("\nPara verificar duplicatas diretamente no Firebase Console:")
    report.append("\n1. Buscar processos por título específico:")
    report.append("   Coleção: processes")
    report.append("   Filtro: title == 'AIA 137428 - REFLORESTA'")
    report.append("\n2. Buscar processos por número:")
    report.append("   Coleção: processes")
    report.append("   Filtro: number == 'PMSC/46545/2020'")
    report.append("\n3. Listar todos os processos ordenados por data de criação:")
    report.append("   Coleção: processes")
    report.append("   Ordenar por: created_at (se existir) ou _id")
    report.append("")
    
    report.append("=" * 80)
    report.append("FIM DO RELATÓRIO")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """Função principal de investigação."""
    print("=" * 80)
    print("🔍 INVESTIGAÇÃO DE DUPLICAÇÃO DE PROCESSOS")
    print("=" * 80)
    print()
    
    # 1. Buscar processos do Firestore (direto, sem cache)
    print("📊 Buscando processos do Firestore...")
    firestore_processes = get_all_processes_from_firestore()
    print(f"   ✓ {len(firestore_processes)} processos encontrados no Firestore")
    print()
    
    # 2. Buscar processos do cache
    print("📊 Buscando processos do cache em memória...")
    cache_processes = get_processes_from_cache()
    print(f"   ✓ {len(cache_processes)} processos encontrados no cache")
    print()
    
    # 3. Analisar estado do cache
    print("📊 Analisando estado do cache...")
    cache_state = analyze_cache_state()
    print(f"   ✓ Cache existe: {cache_state['has_cache']}")
    if cache_state['has_cache']:
        print(f"   ✓ Tamanho: {cache_state['cache_size']} processos")
    print()
    
    # 4. Comparar Firestore vs Cache
    print("📊 Comparando Firestore vs Cache...")
    comparison = compare_firestore_vs_cache(firestore_processes, cache_processes)
    print(f"   ✓ Diferença: {comparison['count_difference']} processos")
    print()
    
    # 5. Buscar duplicatas por título
    print("📊 Buscando duplicatas por título...")
    duplicates_by_title = find_duplicates_by_field(firestore_processes, 'title')
    print(f"   ✓ {len(duplicates_by_title)} grupos de duplicatas encontrados")
    print()
    
    # 6. Buscar duplicatas por número
    print("📊 Buscando duplicatas por número...")
    duplicates_by_number = find_duplicates_by_field(firestore_processes, 'number')
    print(f"   ✓ {len(duplicates_by_number)} grupos de duplicatas encontrados")
    print()
    
    # 7. Buscar duplicatas por combinação
    print("📊 Buscando duplicatas por combinação (título+número+data)...")
    duplicates_by_combo = find_duplicates_by_multiple_fields(
        firestore_processes,
        ['title', 'number', 'data_abertura']
    )
    print(f"   ✓ {len(duplicates_by_combo)} grupos de duplicatas encontrados")
    print()
    
    # 8. Analisar processos suspeitos
    print("📊 Analisando processos suspeitos específicos...")
    suspect_analysis = analyze_suspect_processes(firestore_processes)
    print(f"   ✓ {len(suspect_analysis['found'])} encontrados")
    print(f"   ✓ {len(suspect_analysis['duplicates'])} com duplicatas")
    print(f"   ✓ {len(suspect_analysis['not_found'])} não encontrados")
    print()
    
    # 9. Gerar relatório
    print("📊 Gerando relatório completo...")
    report = generate_report(
        firestore_processes,
        cache_processes,
        duplicates_by_title,
        duplicates_by_number,
        duplicates_by_combo,
        suspect_analysis,
        cache_state,
        comparison
    )
    
    # Salvar relatório em arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"relatorio_duplicatas_processos_{timestamp}.txt"
    report_path = os.path.join(PROJECT_ROOT, report_file)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"   ✓ Relatório salvo em: {report_file}")
    print()
    
    # Exibir resumo no console
    print("=" * 80)
    print("RESUMO DA INVESTIGAÇÃO")
    print("=" * 80)
    print(report[:2000])  # Primeiras 2000 caracteres
    print("...")
    print(f"\n📄 Relatório completo salvo em: {report_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()

