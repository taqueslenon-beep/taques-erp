"""
Módulo de operações de banco de dados para o módulo de Casos.

Contém funções que interagem com o Firestore via core.py,
incluindo operações de CRUD e sincronização de dados.
"""

import traceback
import time
from typing import List, Dict, Any

from ...core import (
    get_cases_list,
    get_processes_list,
    save_case as save_case_core,
    delete_case as delete_case_core,
    save_process as save_process_core,
    save_data,
    invalidate_cache,
    slugify,
    get_db
)

from .models import CASE_TYPE_OPTIONS, CASE_TYPE_PREFIX
from .business_logic import get_cases_by_type, get_case_sort_key, get_case_type

# Cache para usuários (5 minutos TTL)
_usuarios_cache = None
_usuarios_cache_timestamp = 0
# Cache de 15 minutos - otimizado para poucos registros
# Invalidação manual ocorre após operações de escrita (salvar/deletar)
CACHE_DURATION = 900  # 15 minutos em segundos


def remove_case(case_to_remove: dict) -> bool:
    """
    Remove caso da lista e atualiza dados persistidos.
    
    ESTRUTURA: Usa delete_case que já limpa referências em case_ids automaticamente.
    
    Args:
        case_to_remove: Dicionário do caso a ser removido
        
    Returns:
        True se removido com sucesso, False caso contrário
    """
    cases = get_cases_list()
    if case_to_remove not in cases:
        return False

    slug = case_to_remove.get('slug')
    case_type = get_case_type(case_to_remove)
    
    # Remove do Firestore (delete_case já limpa referências em processos automaticamente)
    if slug:
        delete_case_core(slug)
    else:
        # Fallback: se não tiver slug, tenta limpar manualmente
        case_title = case_to_remove.get('title')
        if case_title:
            for process in get_processes_list():
                related_cases = process.get('cases', [])
                if case_title in related_cases:
                    related_cases.remove(case_title)
                    save_process_core(process)

    if case_type == 'Novo':
        renumber_cases_of_type('Novo', force=True)
    
    return True


def renumber_cases_of_type(case_type: str, force: bool = False):
    """
    Renumera todos os casos de um tipo específico baseado na ordem cronológica.
    
    VERSÃO OTIMIZADA: Coleta todas as mudanças primeiro, depois aplica em batch.
    Isso evita salvamentos múltiplos desnecessários.
    
    Args:
        case_type: Tipo do caso ('Antigo', 'Novo' ou 'Futuro')
        force: Se True, força renumeração mesmo sem mudanças (default: False)
    """
    cases_of_type = get_cases_by_type(case_type)
    prefix = CASE_TYPE_PREFIX.get(case_type, 1)
    
    # Lista de casos que precisam atualização (coleta primeiro)
    cases_to_update = []
    
    for idx, case in enumerate(cases_of_type, start=1):
        name = case.get('name', '')
        year = case.get('year', '')
        new_title = f"{prefix}.{idx} - {name} / {year}"
        new_slug = slugify(f"{prefix}-{idx} {name} {year}")
        
        # APENAS se houver mudança
        needs_update = (
            case.get('title') != new_title or 
            case.get('number') != idx or 
            case.get('slug') != new_slug
        )
        
        if needs_update or force:
            old_slug = case.get('slug')
            case['title'] = new_title
            case['number'] = idx
            case['slug'] = new_slug
            
            cases_to_update.append({
                'case': case,
                'old_slug': old_slug,
                'new_slug': new_slug
            })
    
    # BATCH: Aplica todas as mudanças de uma vez
    if cases_to_update:
        db = get_db()
        for item in cases_to_update:
            case_data = item['case']
            old_slug = item['old_slug']
            new_slug = item['new_slug']
            
            # Se slug mudou, precisa deletar o antigo e criar o novo
            if old_slug != new_slug and old_slug:
                try:
                    old_doc = db.collection('cases').document(old_slug).get()
                    if old_doc.exists:
                        # Mescla dados antigos com novos
                        merged_data = old_doc.to_dict()
                        merged_data.update(case_data)
                        merged_data.pop('_id', None)
                        # Salva com novo slug
                        db.collection('cases').document(new_slug).set(merged_data)
                        # Deleta antigo
                        db.collection('cases').document(old_slug).delete()
                        print(f"   ✅ Renumerado: {old_slug} → {new_slug}")
                    else:
                        save_case_core(case_data)
                except Exception as e:
                    print(f"   ⚠️  Erro ao renumerar: {e}")
                    traceback.print_exc()
            else:
                # Slug igual, apenas atualiza
                save_case_core(case_data)
        
        print(f"   📝 Renumerados {len(cases_to_update)} caso(s) do tipo '{case_type}'")
        invalidate_cache('cases')
    else:
        print(f"   ✓ Nenhuma mudança necessária para '{case_type}'")


def renumber_all_cases():
    """
    Renumera todos os casos de todos os tipos para garantir consistência.
    """
    for case_type in CASE_TYPE_OPTIONS:
        renumber_cases_of_type(case_type)
    save_data()


def save_case(case: dict, skip_duplicate_check: bool = False):
    """
    Salva um caso no Firestore com proteção contra corrupção de dados.
    
    VERSÃO SIMPLIFICADA: Remove bloqueios desnecessários que causavam confusão.
    A deduplicação é feita no nível do Firestore (slug como ID).
    
    Args:
        case: Dicionário com dados do caso
        skip_duplicate_check: Mantido para compatibilidade, mas ignorado
    """
    # Simples: salva no Firestore usando slug como ID
    # Firestore impede duplicatas automaticamente (ID único)
    save_case_core(case)


def delete_case(slug: str):
    """
    Wrapper para deletar um caso do Firestore.
    
    Args:
        slug: Identificador único do caso
    """
    delete_case_core(slug)


def save_process(process: dict):
    """
    Wrapper para salvar um processo no Firestore.
    
    Args:
        process: Dicionário com dados do processo
    """
    save_process_core(process)


def get_usuarios_ativos() -> List[Dict[str, Any]]:
    """
    Busca todos os usuários ativos da coleção 'usuarios_sistema' no Firestore.
    
    Retorna lista com: _id, nome_completo, email, cargo/função (se houver).
    Ordena por nome_completo em ordem alfabética.
    Implementa cache local para evitar múltiplas consultas.
    
    Returns:
        Lista de dicionários com dados dos usuários ativos
    """
    global _usuarios_cache, _usuarios_cache_timestamp
    
    now = time.time()
    
    # Verifica cache
    if _usuarios_cache is not None and (now - _usuarios_cache_timestamp) < CACHE_DURATION:
        return _usuarios_cache
    
    try:
        db = get_db()
        docs = db.collection('usuarios_sistema').stream()
        
        usuarios = []
        for doc in docs:
            usuario = doc.to_dict() or {}
            usuario_id = doc.id
            
            # Verifica se usuário está ativo (assume ativo se não houver campo de status)
            status = usuario.get('status', 'ativo')
            active = usuario.get('active', True)
            
            # Considera ativo se status == 'ativo' ou active == True ou não houver campo
            if status == 'ativo' or active is True or (status is None and active is None):
                usuarios.append({
                    '_id': usuario_id,
                    'nome_completo': usuario.get('nome_completo') or usuario.get('name') or usuario.get('full_name') or '(sem nome)',
                    'email': usuario.get('email') or '',
                    'cargo': usuario.get('cargo') or usuario.get('funcao') or usuario.get('role') or '',
                    'funcao': usuario.get('funcao') or usuario.get('cargo') or usuario.get('role') or ''
                })
        
        # Ordena por nome_completo em ordem alfabética
        usuarios.sort(key=lambda x: x['nome_completo'].lower())
        
        # Atualiza cache
        _usuarios_cache = usuarios
        _usuarios_cache_timestamp = now
        
        return usuarios
    except Exception as e:
        print(f"Erro ao buscar usuários ativos: {e}")
        traceback.print_exc()
        # Retorna cache antigo se houver erro
        return _usuarios_cache or []

