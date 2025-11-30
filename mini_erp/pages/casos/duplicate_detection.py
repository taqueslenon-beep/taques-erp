"""
Módulo de detecção e correção de duplicatas de casos.

Fornece funções para identificar, analisar e corrigir casos duplicados
no sistema, garantindo integridade dos dados.
"""

import traceback
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from datetime import datetime

from ...core import get_db, get_cases_list, delete_case, save_case


def find_duplicate_cases() -> Dict[str, Any]:
    """
    Identifica todos os casos duplicados no banco de dados.
    
    Retorna um dicionário com:
    - 'by_slug': Casos com mesmo slug (duplicatas exatas)
    - 'by_title': Casos com mesmo título mas slugs diferentes
    - 'by_name_year': Casos com mesmo nome e ano mas slugs diferentes
    - 'stats': Estatísticas gerais
    
    Returns:
        Dicionário com grupos de duplicatas e estatísticas
    """
    db = get_db()
    all_docs = db.collection('cases').stream()
    
    # Agrupa por diferentes critérios
    by_slug = defaultdict(list)
    by_title = defaultdict(list)
    by_name_year = defaultdict(list)
    
    all_cases = []
    
    for doc in all_docs:
        case_data = doc.to_dict()
        case_data['_id'] = doc.id
        case_data['_firestore_id'] = doc.id  # ID do Firestore
        all_cases.append(case_data)
        
        slug = case_data.get('slug')
        title = case_data.get('title', '')
        name = case_data.get('name', '')
        year = case_data.get('year', '')
        
        # Agrupa por slug
        if slug:
            by_slug[slug].append(case_data)
        
        # Agrupa por título
        if title:
            by_title[title].append(case_data)
        
        # Agrupa por nome + ano
        if name and year:
            key = f"{name}|{year}"
            by_name_year[key].append(case_data)
    
    # Filtra apenas grupos com duplicatas (mais de 1 item)
    duplicates_by_slug = {k: v for k, v in by_slug.items() if len(v) > 1}
    duplicates_by_title = {k: v for k, v in by_title.items() if len(v) > 1}
    duplicates_by_name_year = {k: v for k, v in by_name_year.items() if len(v) > 1}
    
    # Estatísticas
    total_cases = len(all_cases)
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
            'total_cases': total_cases,
            'total_duplicate_groups': total_duplicate_groups,
            'total_duplicate_cases': total_duplicate_cases,
            'unique_cases_after_dedup': total_cases - total_duplicate_cases
        },
        'all_cases': all_cases
    }


def analyze_duplicate_group(group: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analisa um grupo de casos duplicados e determina qual manter.
    
    Critérios de prioridade (mais importante primeiro):
    1. Caso com mais dados preenchidos (menos campos vazios)
    2. Caso mais recente (baseado em timestamp ou _id)
    3. Caso com slug válido
    
    Args:
        group: Lista de casos duplicados
        
    Returns:
        Dicionário com:
        - 'keep': Caso a ser mantido
        - 'remove': Lista de casos a serem removidos
        - 'reason': Motivo da escolha
    """
    if len(group) <= 1:
        return {'keep': group[0] if group else None, 'remove': [], 'reason': 'Sem duplicatas'}
    
    def score_case(case: Dict[str, Any]) -> Tuple[int, str]:
        """Calcula score do caso (maior = melhor)"""
        score = 0
        reasons = []
        
        # Conta campos preenchidos
        filled_fields = sum(1 for k, v in case.items() 
                          if v and k not in ['_id', '_firestore_id'] 
                          and not (isinstance(v, list) and len(v) == 0)
                          and not (isinstance(v, str) and v.strip() == ''))
        score += filled_fields * 10
        reasons.append(f'{filled_fields} campos preenchidos')
        
        # Prioriza casos com slug válido
        if case.get('slug'):
            score += 100
            reasons.append('tem slug')
        
        # Prioriza casos com número
        if case.get('number'):
            score += 50
            reasons.append('tem número')
        
        # Prioriza casos com processos vinculados
        if case.get('process_ids'):
            score += len(case.get('process_ids', [])) * 5
            reasons.append(f'{len(case.get("process_ids", []))} processos vinculados')
        
        # Prioriza casos com clientes
        if case.get('clients'):
            score += len(case.get('clients', [])) * 2
            reasons.append(f'{len(case.get("clients", []))} clientes')
        
        return score, ', '.join(reasons)
    
    # Calcula score para cada caso
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
    """
    Mescla dados de casos duplicados no caso principal.
    
    Preserva todos os dados úteis dos casos removidos no caso mantido.
    
    Args:
        keep_case: Caso a ser mantido
        remove_cases: Lista de casos a serem mesclados
        
    Returns:
        Caso atualizado com dados mesclados
    """
    merged = keep_case.copy()
    
    for remove_case in remove_cases:
        # Mescla processos (sem duplicatas)
        keep_process_ids = set(merged.get('process_ids', []))
        remove_process_ids = set(remove_case.get('process_ids', []))
        merged['process_ids'] = list(keep_process_ids | remove_process_ids)
        
        keep_processes = set(merged.get('processes', []))
        remove_processes = set(remove_case.get('processes', []))
        merged['processes'] = list(keep_processes | remove_processes)
        
        # Mescla clientes (sem duplicatas)
        keep_clients = set(merged.get('clients', []))
        remove_clients = set(remove_case.get('clients', []))
        merged['clients'] = list(keep_clients | remove_clients)
        
        # Mescla links (sem duplicatas baseado em URL)
        keep_links = {link.get('url'): link for link in merged.get('links', [])}
        for link in remove_case.get('links', []):
            url = link.get('url')
            if url and url not in keep_links:
                keep_links[url] = link
        merged['links'] = list(keep_links.values())
        
        # Mescla teses (sem duplicatas baseado em nome)
        keep_theses = {tese.get('name'): tese for tese in merged.get('theses', [])}
        for tese in remove_case.get('theses', []):
            name = tese.get('name')
            if name and name not in keep_theses:
                keep_theses[name] = tese
        merged['theses'] = list(keep_theses.values())
        
        # Mescla cálculos (preserva todos)
        keep_calcs = merged.get('calculations', [])
        remove_calcs = remove_case.get('calculations', [])
        merged['calculations'] = keep_calcs + remove_calcs
        
        # Preenche campos vazios com dados dos casos removidos
        for key, value in remove_case.items():
            if key not in ['_id', '_firestore_id', 'slug', 'title', 'number']:
                if not merged.get(key) and value:
                    merged[key] = value
    
    return merged


def deduplicate_cases(dry_run: bool = True) -> Dict[str, Any]:
    """
    Remove duplicatas de casos no banco de dados.
    
    Args:
        dry_run: Se True, apenas analisa sem fazer alterações
        
    Returns:
        Dicionário com relatório da operação
    """
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
    
    # Processa duplicatas por slug (mais crítico)
    print("🔍 Processando duplicatas por slug...")
    for slug, group in duplicates['by_slug'].items():
        analysis = analyze_duplicate_group(group)
        keep_case = analysis['keep']
        remove_cases = analysis['remove']
        
        print(f"\n   Slug: {slug}")
        print(f"   Manter: {keep_case.get('title', 'Sem título')} (ID: {keep_case.get('_firestore_id')})")
        print(f"   Motivo: {analysis['reason']}")
        print(f"   Remover: {len(remove_cases)} caso(s)")
        
        # Mescla dados
        merged_case = merge_case_data(keep_case, remove_cases)
        
        if not dry_run:
            try:
                # Salva caso mesclado
                save_case(merged_case)
                
                # Remove casos duplicados
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
    
    # Processa duplicatas por título (menos crítico, mas importante)
    print("\n🔍 Processando duplicatas por título...")
    processed_titles = set()
    
    for title, group in duplicates['by_title'].items():
        # Pula se já processou por slug
        if any(c.get('slug') in duplicates['by_slug'] for c in group):
            continue
        
        if title in processed_titles:
            continue
        
        analysis = analyze_duplicate_group(group)
        keep_case = analysis['keep']
        remove_cases = analysis['remove']
        
        print(f"\n   Título: {title}")
        print(f"   Manter: {keep_case.get('_firestore_id')}")
        print(f"   Remover: {len(remove_cases)} caso(s)")
        
        merged_case = merge_case_data(keep_case, remove_cases)
        
        if not dry_run:
            try:
                save_case(merged_case)
                for remove_case in remove_cases:
                    firestore_id = remove_case.get('_firestore_id')
                    if firestore_id:
                        db.collection('cases').document(firestore_id).delete()
                actions.append({
                    'type': 'merged_by_title',
                    'title': title,
                    'kept': keep_case.get('_firestore_id'),
                    'removed': [c.get('_firestore_id') for c in remove_cases]
                })
            except Exception as e:
                print(f"      ❌ Erro: {e}")
        else:
            actions.append({
                'type': 'would_merge_by_title',
                'title': title,
                'kept': keep_case.get('_firestore_id'),
                'removed': [c.get('_firestore_id') for c in remove_cases]
            })
        
        processed_titles.add(title)
    
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


def log_save_case(case: Dict[str, Any], caller: str, stack_info: Optional[str] = None):
    """
    Registra log de salvamento de caso para debugging.
    
    Args:
        case: Caso sendo salvo
        caller: Nome da função que chamou save_case
        stack_info: Informações da stack trace (opcional)
    """
    timestamp = datetime.now().isoformat()
    slug = case.get('slug', 'NO_SLUG')
    title = case.get('title', 'NO_TITLE')
    
    log_entry = {
        'timestamp': timestamp,
        'caller': caller,
        'slug': slug,
        'title': title,
        'case_id': case.get('_id'),
        'stack': stack_info
    }
    
    # Imprime log (pode ser melhorado para salvar em arquivo ou banco)
    print(f"📝 SAVE_CASE LOG: {timestamp} | Caller: {caller} | Slug: {slug} | Title: {title}")
    
    # TODO: Salvar em arquivo de log ou coleção do Firestore para análise


def check_for_duplicates_before_save(case: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Verifica se já existe caso duplicado antes de salvar.
    
    Args:
        case: Caso a ser salvo
        
    Returns:
        Lista de casos duplicados encontrados (vazia se não houver)
    """
    slug = case.get('slug')
    title = case.get('title', '')
    
    if not slug and not title:
        return []
    
    db = get_db()
    duplicates = []
    
    # Verifica por slug
    if slug:
        existing = db.collection('cases').document(slug).get()
        if existing.exists:
            existing_data = existing.to_dict()
            existing_data['_id'] = existing.id
            duplicates.append(existing_data)
    
    # Verifica por título (se slug não encontrou nada)
    if not duplicates and title:
        query = db.collection('cases').where('title', '==', title).limit(10).stream()
        for doc in query:
            if doc.id != slug:  # Não é o mesmo documento
                case_data = doc.to_dict()
                case_data['_id'] = doc.id
                duplicates.append(case_data)
    
    return duplicates




