"""
Módulo de operações de banco de dados para o módulo de Casos.

ATUALIZADO: Agora usa a coleção vg_casos com filtro por grupo_nome = "Schmidmeier".
Mantém compatibilidade com formato antigo através de camada de conversão.

Contém funções que interagem com o Firestore,
incluindo operações de CRUD e sincronização de dados.
"""

import traceback
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...core import (
    get_processes_list,
    save_process as save_process_core,
    save_data,
    invalidate_cache,
    slugify
)
from ...firebase_config import get_db
from ..visao_geral.pessoas.database_grupo import buscar_grupo_por_nome

from .models import CASE_TYPE_OPTIONS, CASE_TYPE_PREFIX
from .business_logic import get_cases_by_type, get_case_sort_key, get_case_type
from .compatibilidade import converter_vg_para_antigo, converter_antigo_para_vg

# Nome da coleção Firebase
COLECAO_CASOS = 'vg_casos'
GRUPO_NOME = 'Schmidmeier'

# Cache para grupo
_grupo_cache = None
_grupo_id_cache = None

# Cache para usuários (5 minutos TTL)
_usuarios_cache = None
_usuarios_cache_timestamp = 0
# Cache de 15 minutos - otimizado para poucos registros
# Invalidação manual ocorre após operações de escrita (salvar/deletar)
CACHE_DURATION = 900  # 15 minutos em segundos


def _obter_grupo_id() -> Optional[str]:
    """
    Obtém o ID do grupo Schmidmeier (com cache).
    
    Returns:
        ID do grupo ou None se não encontrado
    """
    global _grupo_id_cache
    
    if _grupo_id_cache:
        return _grupo_id_cache
    
    grupo = buscar_grupo_por_nome(GRUPO_NOME)
    if grupo:
        _grupo_id_cache = grupo._id
        return _grupo_id_cache
    
    return None


def _converter_timestamps(documento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte campos DatetimeWithNanoseconds do Firebase para string ISO.
    
    Args:
        documento: Dicionário com dados do Firebase
        
    Returns:
        Dicionário com timestamps convertidos para string
    """
    if documento is None:
        return {}
    
    dados = dict(documento)
    campos_data = ['created_at', 'updated_at']
    
    for campo in campos_data:
        if campo in dados and dados[campo] is not None:
            try:
                if hasattr(dados[campo], 'isoformat'):
                    dados[campo] = dados[campo].isoformat()
                elif hasattr(dados[campo], 'strftime'):
                    dados[campo] = dados[campo].strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                dados[campo] = None
    
    return dados


def get_cases_list() -> List[Dict[str, Any]]:
    """
    Retorna todos os casos do Schmidmeier da coleção vg_casos.
    Filtra por grupo_nome = "Schmidmeier" e converte para formato antigo.
    
    Returns:
        Lista de casos no formato antigo (compatível com interface)
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []
        
        # Busca casos filtrados por grupo
        docs = db.collection(COLECAO_CASOS).where('grupo_nome', '==', GRUPO_NOME).stream()
        
        casos_vg = []
        for doc in docs:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            caso = _converter_timestamps(caso)
            casos_vg.append(caso)
        
        # Converte para formato antigo
        casos_antigos = [converter_vg_para_antigo(c) for c in casos_vg]
        
        return casos_antigos
        
    except Exception as e:
        print(f"Erro ao buscar casos do Schmidmeier: {e}")
        traceback.print_exc()
        return []


def remove_case(case_to_remove: dict) -> bool:
    """
    Remove caso da lista e atualiza dados persistidos.
    
    ESTRUTURA: Usa delete_case que já limpa referências em case_ids automaticamente.
    
    Args:
        case_to_remove: Dicionário do caso a ser removido
        
    Returns:
        True se removido com sucesso, False caso contrário
    """
    slug = case_to_remove.get('slug')
    if not slug:
        return False
    
    case_type = get_case_type(case_to_remove)
    
    # Remove do Firestore (delete_case já limpa referências em processos automaticamente)
    delete_case(slug)
    
    # Limpa referências em processos
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
            
            # Se slug mudou, precisa atualizar o slug_original
            if old_slug != new_slug and old_slug:
                try:
                    db = get_db()
                    if not db:
                        continue
                    
                    # Busca caso antigo pelo slug_original
                    old_docs = db.collection(COLECAO_CASOS).where('slug_original', '==', old_slug).where('grupo_nome', '==', GRUPO_NOME).limit(1).stream()
                    
                    for old_doc in old_docs:
                        # Atualiza slug_original e outros campos
                        caso_vg = converter_antigo_para_vg(case_data, _obter_grupo_id(), GRUPO_NOME)
                        caso_vg['updated_at'] = datetime.now()
                        caso_vg.pop('_id', None)
                        
                        # Atualiza documento existente
                        old_doc.reference.update(caso_vg)
                        print(f"   ✅ Renumerado: {old_slug} → {new_slug}")
                        break
                    else:
                        # Caso não encontrado, cria novo
                        save_case(case_data)
                except Exception as e:
                    print(f"   ⚠️  Erro ao renumerar: {e}")
                    traceback.print_exc()
            else:
                # Slug igual, apenas atualiza
                save_case(case_data)
        
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
    Salva um caso no Firestore (coleção vg_casos).
    Converte do formato antigo para vg_casos antes de salvar.
    
    Args:
        case: Dicionário com dados do caso (formato antigo)
        skip_duplicate_check: Mantido para compatibilidade, mas ignorado
    """
    try:
        grupo_id = _obter_grupo_id()
        if not grupo_id:
            print("⚠️  Erro: Grupo 'Schmidmeier' não encontrado. Caso não será salvo.")
            return
        
        # Converte para formato vg_casos
        caso_vg = converter_antigo_para_vg(case, grupo_id, GRUPO_NOME)
        
        # Usa slug_original como ID do documento
        doc_id = caso_vg.get('slug_original') or case.get('slug') or slugify(case.get('title', ''))
        
        # Atualiza timestamp
        caso_vg['updated_at'] = datetime.now()
        
        # Remove _id dos dados
        caso_vg.pop('_id', None)
        
        # Salva no Firestore
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return
        
        db.collection(COLECAO_CASOS).document(doc_id).set(caso_vg, merge=True)
        
        # Invalida cache
        invalidate_cache('cases')
        
    except Exception as e:
        print(f"Erro ao salvar caso: {e}")
        traceback.print_exc()


def delete_case(slug: str):
    """
    Deleta um caso do Firestore (coleção vg_casos).
    
    Args:
        slug: Identificador único do caso (slug_original)
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return
        
        # Busca o caso pelo slug_original
        docs = db.collection(COLECAO_CASOS).where('slug_original', '==', slug).where('grupo_nome', '==', GRUPO_NOME).limit(1).stream()
        
        for doc in docs:
            doc.reference.delete()
            print(f"✅ Caso deletado: {slug}")
            invalidate_cache('cases')
            return
        
        print(f"⚠️  Caso não encontrado: {slug}")
        
    except Exception as e:
        print(f"Erro ao deletar caso: {e}")
        traceback.print_exc()


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

