"""
Serviço de acesso a dados do módulo de Entregáveis.

Gerencia busca, criação, atualização e exclusão de entregáveis no Firestore.
"""

import time
import threading
from typing import List, Dict, Any, Optional
from ..firebase_config import get_db
from ..auth import get_current_user


# Cache em memória com TTL de 5 minutos
_cache_entregaveis = None
_cache_timestamp = None
_cache_lock = threading.Lock()
CACHE_DURATION = 300  # 5 minutos em segundos


def invalidar_cache():
    """
    Invalida o cache de entregáveis, forçando nova busca no Firestore.
    """
    global _cache_entregaveis, _cache_timestamp
    
    with _cache_lock:
        _cache_entregaveis = None
        _cache_timestamp = None


def listar_entregaveis() -> List[Dict[str, Any]]:
    """
    Busca todos os entregáveis cadastrados no Firestore.
    
    Returns:
        Lista de dicionários com dados dos entregáveis
    """
    global _cache_entregaveis, _cache_timestamp
    
    now = time.time()
    
    # Verifica cache sem lock (leitura rápida)
    if _cache_entregaveis is not None and _cache_timestamp is not None:
        if now - _cache_timestamp < CACHE_DURATION:
            return _cache_entregaveis
    
    # Usa lock para evitar múltiplas consultas simultâneas
    with _cache_lock:
        # Verifica novamente dentro do lock
        if _cache_entregaveis is not None and _cache_timestamp is not None:
            if now - _cache_timestamp < CACHE_DURATION:
                return _cache_entregaveis
        
        # Consulta Firestore
        try:
            db = get_db()
            docs = db.collection('entregaveis').stream()
            
            entregaveis = []
            for doc in docs:
                entregavel = doc.to_dict()
                entregavel['_id'] = doc.id  # Guarda o ID do documento
                entregaveis.append(entregavel)
            
            # Atualiza cache
            _cache_entregaveis = entregaveis
            _cache_timestamp = time.time()
            
            return entregaveis
            
        except Exception as e:
            print(f"[ERROR] Erro ao buscar entregáveis do Firestore: {e}")
            # Retorna cache antigo se houver erro
            if _cache_entregaveis is not None:
                return _cache_entregaveis
            return []


def listar_por_status(status: str) -> List[Dict[str, Any]]:
    """
    Busca entregáveis filtrados por status.
    
    Args:
        status: Status a filtrar
    
    Returns:
        Lista de entregáveis com o status especificado
    """
    todos = listar_entregaveis()
    return [e for e in todos if e.get('status') == status]


def listar_por_categoria(categoria: str) -> List[Dict[str, Any]]:
    """
    Busca entregáveis filtrados por categoria.
    
    Args:
        categoria: Categoria a filtrar
    
    Returns:
        Lista de entregáveis com a categoria especificada
    """
    todos = listar_entregaveis()
    return [e for e in todos if e.get('categoria') == categoria]


def buscar_entregavel_por_id(entregavel_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um entregável específico por ID no Firestore.
    
    Args:
        entregavel_id: ID do documento no Firestore
    
    Returns:
        Dicionário com dados do entregável ou None se não encontrado
    """
    try:
        db = get_db()
        doc_ref = db.collection('entregaveis').document(entregavel_id)
        doc = doc_ref.get()
        
        if doc.exists:
            entregavel = doc.to_dict()
            entregavel['_id'] = doc.id
            return entregavel
        else:
            return None
            
    except Exception as e:
        print(f"[ERROR] Erro ao buscar entregável {entregavel_id} do Firestore: {e}")
        return None


def criar_entregavel(dados: Dict[str, Any]) -> str:
    """
    Cria um novo entregável no Firestore.
    
    Args:
        dados: Dicionário com dados do entregável
    
    Returns:
        ID do documento criado no Firestore
    """
    try:
        db = get_db()
        
        # Remove _id dos dados (é metadado)
        dados_para_salvar = {k: v for k, v in dados.items() if k != '_id'}
        
        # Adiciona timestamps
        now = time.time()
        dados_para_salvar['criado_em'] = now
        dados_para_salvar['atualizado_em'] = now
        
        # Adiciona criado_por se não especificado
        if 'criado_por' not in dados_para_salvar:
            user = get_current_user()
            if user:
                dados_para_salvar['criado_por'] = user.get('uid', '')
        
        # Salva no Firestore
        doc_ref = db.collection('entregaveis').add(dados_para_salvar)
        entregavel_id = doc_ref[1].id
        
        # Invalida cache
        invalidar_cache()
        
        return entregavel_id
        
    except Exception as e:
        print(f"[ERROR] Erro ao criar entregável no Firestore: {e}")
        raise


def atualizar_entregavel(entregavel_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza um entregável existente no Firestore.
    
    Args:
        entregavel_id: ID do documento no Firestore
        dados: Dicionário com dados a atualizar
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        db = get_db()
        
        # Remove _id dos dados (é metadado)
        dados_para_atualizar = {k: v for k, v in dados.items() if k != '_id'}
        
        # Atualiza timestamp
        dados_para_atualizar['atualizado_em'] = time.time()
        
        # Atualiza no Firestore
        db.collection('entregaveis').document(entregavel_id).update(dados_para_atualizar)
        
        # Invalida cache
        invalidar_cache()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao atualizar entregável {entregavel_id} no Firestore: {e}")
        return False


def atualizar_status(entregavel_id: str, novo_status: str) -> bool:
    """
    Atualiza apenas o status de um entregável.
    
    Args:
        entregavel_id: ID do documento no Firestore
        novo_status: Novo status a definir
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    return atualizar_entregavel(entregavel_id, {'status': novo_status})


def atualizar_categoria(entregavel_id: str, nova_categoria: str) -> bool:
    """
    Atualiza apenas a categoria de um entregável.
    
    Args:
        entregavel_id: ID do documento no Firestore
        nova_categoria: Nova categoria a definir
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    return atualizar_entregavel(entregavel_id, {'categoria': nova_categoria})


def excluir_entregavel(entregavel_id: str) -> bool:
    """
    Exclui um entregável do Firestore.
    
    Args:
        entregavel_id: ID do documento no Firestore
    
    Returns:
        True se excluído com sucesso, False caso contrário
    """
    try:
        db = get_db()
        db.collection('entregaveis').document(entregavel_id).delete()
        
        # Invalida cache
        invalidar_cache()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao excluir entregável {entregavel_id} do Firestore: {e}")
        return False


