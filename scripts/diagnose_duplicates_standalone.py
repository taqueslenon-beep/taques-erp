#!/usr/bin/env python3
"""
Script standalone de diagnóstico de duplicatas de casos.

Não depende de imports do sistema, carrega tudo diretamente.
"""

import sys
import os
import traceback
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Importa apenas o necessário do core (sem passar por pages)
from mini_erp.core import get_db, get_cases_list, delete_case, save_case, slugify


def find_duplicate_cases() -> Dict[str, Any]:
    """Identifica todos os casos duplicados no banco de dados."""
    db = get_db()
    all_docs = db.collection('cases').stream()
    
    by_slug = defaultdict(list)
    by_title = defaultdict(list)
    by_name_year = defaultdict(list)
    
    all_cases = []
    
    for doc in all_docs:
        case_data = doc.to_dict()
        case_data['_id'] = doc.id
        case_data['_firestore_id'] = doc.id
        all_cases.append(case_data)
        
        slug = case_data.get('slug')
        title = case_data.get('title', '')
        name = case_data.get('name', '')
        year = case_data.get('year', '')
        
        if slug:
            by_slug[slug].append(case_data)
        if title:
            by_title[title].append(case_data)
        if name and year:
            key = f"{name}|{year}"
            by_name_year[key].append(case_data)
    
    duplicates_by_slug = {k: v for k, v in by_slug.items() if len(v) > 1}
    duplicates_by_title = {k: v for k, v in by_title.items() if len(v) > 1}
    duplicates_by_name_year = {k: v for k, v in by_name_year.items() if len(v) > 1}
    
    total_duplicate_groups = (
        len(duplicates_by_slug) + 
        len(duplicates_by_title) + 
        len(duplicates_by_name_year)
    )
    total_duplicate_cases = sum(
        len(v) - 1 for v in duplicates_by_slug.values()
    ) + sum(
        len(v) - 1 for v in duplicates_by_title.values()
    ) + sum(
        len(v) - 1 for v in duplicates_by_name_year.values()
    )
    
    return {
        'by_slug': duplicates_by_slug,
        'by_title': duplicates_by_title,
        'by_name_year': duplicates_by_name_year,
        'stats': {
            'total_cases': len(all_cases),
            'total_duplicate_groups': total_duplicate_groups,
            'total_duplicate_cases': total_duplicate_cases,
            'unique_cases_after_dedup': len(all_cases) - total_duplicate_cases
        },
        'all_cases': all_cases
    }


def analyze_duplicate_group(group: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa um grupo de casos duplicados e determina qual manter."""
    if len(group) <= 1:
        return {'keep': group[0] if group else None, 'remove': [], 'reason': 'Sem duplicatas'}
    
    def score_case(case: Dict[str, Any]) -> Tuple[int, str]:
        score = 0
        reasons = []
        
        filled_fields = sum(1 for k, v in case.items() 
                          if v and k not in ['_id', '_firestore_id'] 
                          and not (isinstance(v, list) and len(v) == 0)
                          and not (isinstance(v, str) and v.strip() == ''))
        score += filled_fields * 10
        reasons.append(f'{filled_fields} campos preenchidos')
        
        if case.get('slug'):
            score += 100
            reasons.append('tem slug')
        if case.get('number'):
            score += 50
            reasons.append('tem número')
        if case.get('process_ids'):
            score += len(case.get('process_ids', [])) * 5
            reasons.append(f'{len(case.get("process_ids", []))} processos vinculados')
        if case.get('clients'):
            score += len(case.get('clients', [])) * 2
            reasons.append(f'{len(case.get("clients", []))} clientes')
        
        return score, ', '.join(reasons)
    
    scored = [(score_case(case), case) for case in group]
    scored.sort(key=lambda x: x[0][0], reverse=True)
    
    keep_case = scored[0][1]
    remove_cases = [case for _, case in scored[1:]]
    reason = scored[0][0][1]
    
    return {
        'keep': keep_case,
        'remove': remove_cases,
        'reason': reason
    }


def merge_case_data(keep_case: Dict[str, Any], remove_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mescla dados de casos duplicados no caso principal."""
    merged = keep_case.copy()
    
    for remove_case in remove_cases:
        keep_process_ids = set(merged.get('process_ids', []))
        remove_process_ids = set(remove_case.get('process_ids', []))
        merged['process_ids'] = list(keep_process_ids | remove_process_ids)
        
        keep_processes = set(merged.get('processes', []))
        remove_processes = set(remove_case.get('processes', []))
        merged['processes'] = list(keep_processes | remove_processes)
        
        keep_clients = set(merged.get('clients', []))
        remove_clients = set(remove_case.get('clients', []))
        merged['clients'] = list(keep_clients | remove_clients)
        
        keep_links = {link.get('url'): link for link in merged.get('links', [])}
        for link in remove_case.get('links', []):
            url = link.get('url')
            if url and url not in keep_links:
                keep_links[url] = link
        merged['links'] = list(keep_links.values())
        
        keep_theses = {tese.get('name'): tese for tese in merged.get('theses', [])}
        for tese in remove_case.get('theses', []):
            name = tese.get('name')
            if name and name not in keep_theses:
                keep_theses[name] = tese
        merged['theses'] = list(keep_theses.values())
        
        keep_calcs = merged.get('calculations', [])
        remove_calcs = remove_case.get('calculations', [])
        merged['calculations'] = keep_calcs + remove_calcs
        
        for key, value in remove_case.items():
            if key not in ['_id', '_firestore_id', 'slug', 'title', 'number']:
                if not merged.get(key) and value:
                    merged[key] = value
    
    return merged


def deduplicate_cases(dry_run: bool = True) -> Dict[str, Any]:
    """Remove duplicatas de casos no banco de dados."""
    print(f"\n{'='*60}")
    print(f"🔍 INICIANDO DEDUPLICAÇÃO DE CASOS (dry_run={dry_run})")
    print(f"{'='*60}\n")
    
    duplicates = find_duplicate_cases()
    stats = duplicates['stats']
    
    print(f"📊 Estatísticas:")
    print(f"   Total de casos: {stats['total_cases']}")
    print(f"   Grupos de duplicatas: {stats['total_duplicate_groups']}")
    print(f"   Casos duplicados: {stats['total_duplicate_cases']}")
    print(f"   Casos únicos após dedup: {stats['unique_cases_after_dedup']}\n")
    
    if stats['total_duplicate_cases'] == 0:
        print("✅ Nenhuma duplicata encontrada!")
        return {
            'success': True,
            'dry_run': dry_run,
            'stats': stats,
            'actions': []
        }
    
    actions = []
    db = get_db()
    
    print("🔍 Processando duplicatas por slug...")
    for slug, group in duplicates['by_slug'].items():
        analysis = analyze_duplicate_group(group)
        keep_case = analysis['keep']
        remove_cases = analysis['remove']
        
        print(f"\n   Slug: {slug}")
        print(f"   Manter: {keep_case.get('title', 'Sem título')} (ID: {keep_case.get('_firestore_id')})")
        print(f"   Motivo: {analysis['reason']}")
        print(f"   Remover: {len(remove_cases)} caso(s)")
        
        merged_case = merge_case_data(keep_case, remove_cases)
        
        if not dry_run:
            try:
                save_case(merged_case)
                
                for remove_case in remove_cases:
                    firestore_id = remove_case.get('_firestore_id')
                    if firestore_id:
                        db.collection('cases').document(firestore_id).delete()
                        print(f"      ✅ Removido: {remove_case.get('title', 'Sem título')} (ID: {firestore_id})")
                
                actions.append({
                    'type': 'merged_by_slug',
                    'slug': slug,
                    'kept': keep_case.get('_firestore_id'),
                    'removed': [c.get('_firestore_id') for c in remove_cases],
                    'merged_data': True
                })
            except Exception as e:
                print(f"      ❌ Erro ao processar: {e}")
                traceback.print_exc()
        else:
            actions.append({
                'type': 'would_merge_by_slug',
                'slug': slug,
                'kept': keep_case.get('_firestore_id'),
                'removed': [c.get('_firestore_id') for c in remove_cases]
            })
    
    print(f"\n{'='*60}")
    if dry_run:
        print("✅ ANÁLISE CONCLUÍDA (DRY RUN - Nenhuma alteração foi feita)")
        print("   Execute com dry_run=False para aplicar as correções")
    else:
        print("✅ DEDUPLICAÇÃO CONCLUÍDA")
    print(f"{'='*60}\n")
    
    return {
        'success': True,
        'dry_run': dry_run,
        'stats': stats,
        'actions': actions
    }


def main():
    """Executa diagnóstico e opcionalmente corrige duplicatas."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnóstico de duplicatas de casos')
    parser.add_argument('--fix', action='store_true', help='Corrige duplicatas encontradas')
    parser.add_argument('--no-dry-run', action='store_true', help='Aplica correções (modifica banco)')
    args = parser.parse_args()
    
    print("="*70)
    print("DIAGNÓSTICO DE DUPLICATAS DE CASOS")
    print("="*70)
    print()
    
    print("🔍 Buscando duplicatas...")
    duplicates = find_duplicate_cases()
    stats = duplicates['stats']
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Total de casos no banco: {stats['total_cases']}")
    print(f"   Grupos de duplicatas encontrados: {stats['total_duplicate_groups']}")
    print(f"   Total de casos duplicados: {stats['total_duplicate_cases']}")
    print(f"   Casos únicos após dedup: {stats['unique_cases_after_dedup']}")
    
    if stats['total_duplicate_cases'] == 0:
        print("\n✅ Nenhuma duplicata encontrada! Sistema está íntegro.")
        return 0
    
    print("\n" + "="*70)
    print("DETALHES DAS DUPLICATAS")
    print("="*70)
    
    if duplicates['by_slug']:
        print("\n🔴 DUPLICATAS POR SLUG (mais crítico):")
        for slug, group in list(duplicates['by_slug'].items())[:20]:
            print(f"\n   Slug: {slug} ({len(group)} duplicatas)")
            for idx, case in enumerate(group, 1):
                print(f"      {idx}. ID: {case.get('_firestore_id')} | Título: {case.get('title', 'Sem título')}")
        if len(duplicates['by_slug']) > 20:
            print(f"\n   ... e mais {len(duplicates['by_slug']) - 20} grupo(s)")
    
    if duplicates['by_title']:
        print("\n🟡 DUPLICATAS POR TÍTULO:")
        for title, group in list(duplicates['by_title'].items())[:10]:
            print(f"\n   Título: {title}")
            for case in group:
                print(f"      - ID: {case.get('_firestore_id')} | Slug: {case.get('slug', 'Sem slug')}")
        if len(duplicates['by_title']) > 10:
            print(f"\n   ... e mais {len(duplicates['by_title']) - 10} grupo(s)")
    
    if args.fix:
        print("\n" + "="*70)
        print("CORREÇÃO DE DUPLICATAS")
        print("="*70)
        
        dry_run = not args.no_dry_run
        
        if dry_run:
            print("\n⚠️  MODO DRY-RUN: Nenhuma alteração será feita")
            print("   Execute com --fix --no-dry-run para aplicar correções")
        else:
            print("\n⚠️  ATENÇÃO: Esta operação irá modificar o banco de dados!")
            response = input("   Deseja continuar? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                print("   Operação cancelada.")
                return 1
        
        result = deduplicate_cases(dry_run=dry_run)
        
        if result['success']:
            print("\n✅ Operação concluída com sucesso!")
            print(f"   Ações realizadas: {len(result['actions'])}")
            return 0
        else:
            print("\n❌ Erro durante a correção")
            return 1
    else:
        print("\n" + "="*70)
        print("PRÓXIMOS PASSOS")
        print("="*70)
        print("\nPara corrigir duplicatas, execute:")
        print("   python scripts/diagnose_duplicates_standalone.py --fix          # Simular")
        print("   python scripts/diagnose_duplicates_standalone.py --fix --no-dry-run # Aplicar")
        return 0


if __name__ == '__main__':
    sys.exit(main())

