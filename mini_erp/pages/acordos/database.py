"""
database.py - Funções de acesso a dados do módulo de Acordos.

Gerencia busca e cache de acordos do Firestore.
"""

import time
import threading
from typing import List, Dict, Any
from ...firebase_config import get_db


# Cache em memória com TTL de 5 minutos
_cache_acordos = None
_cache_timestamp = None
_cache_lock = threading.Lock()
CACHE_DURATION = 300  # 5 minutos em segundos


def buscar_todos_os_acordos() -> List[Dict[str, Any]]:
    """
    Busca todos os acordos cadastrados no Firestore.
    
    Retorna:
        Lista de dicionários com dados dos acordos, cada um contendo:
        - _id: ID do documento no Firestore
        - titulo: Título/Número do acordo
        - data_assinatura: Data de assinatura (timestamp ou string)
        - partes_envolvidas: Lista de partes envolvidas
        - status: Status do acordo (Ativo, Concluído, Rescindido, etc)
        - descricao: Descrição do acordo (opcional)
        - Campos adicionais conforme existam no Firestore
    
    Tratamento de erros:
        - Retorna lista vazia em caso de erro
        - Loga erro no console
        - Retorna cache antigo se disponível
    """
    global _cache_acordos, _cache_timestamp
    
    now = time.time()
    
    # Verifica cache sem lock (leitura rápida)
    if _cache_acordos is not None and _cache_timestamp is not None:
        if now - _cache_timestamp < CACHE_DURATION:
            return _cache_acordos
    
    # Usa lock para evitar múltiplas consultas simultâneas
    with _cache_lock:
        # Verifica novamente dentro do lock
        if _cache_acordos is not None and _cache_timestamp is not None:
            if now - _cache_timestamp < CACHE_DURATION:
                return _cache_acordos
        
        # Consulta Firestore
        try:
            db = get_db()
            
            # Tenta buscar da coleção 'agreements' (padrão)
            # Se não existir, tenta 'acordos'
            collection_name = 'agreements'
            docs = db.collection(collection_name).stream()
            
            acordos = []
            for doc in docs:
                acordo = doc.to_dict()
                acordo['_id'] = doc.id  # Guarda o ID do documento
                acordos.append(acordo)
            
            # Atualiza cache
            _cache_acordos = acordos
            _cache_timestamp = time.time()
            
            return acordos
            
        except Exception as e:
            print(f"[ERROR] Erro ao buscar acordos do Firestore: {e}")
            # Retorna cache antigo se houver erro
            if _cache_acordos is not None:
                return _cache_acordos
            return []


def buscar_acordo_por_id(acordo_id: str) -> Dict[str, Any]:
    """
    Busca um acordo específico por ID no Firestore.
    
    Args:
        acordo_id: ID do documento no Firestore
    
    Returns:
        Dicionário com dados do acordo ou None se não encontrado
    """
    try:
        db = get_db()
        doc_ref = db.collection('agreements').document(acordo_id)
        doc = doc_ref.get()
        
        if doc.exists:
            acordo = doc.to_dict()
            acordo['_id'] = doc.id
            return acordo
        else:
            return None
            
    except Exception as e:
        print(f"[ERROR] Erro ao buscar acordo {acordo_id} do Firestore: {e}")
        return None


def salvar_acordo(acordo_data: Dict[str, Any], acordo_id: str = None) -> str:
    """
    Salva um novo acordo ou atualiza um existente no Firestore.
    
    Args:
        acordo_data: Dicionário com dados do acordo
        acordo_id: ID do documento para atualização (None para criar novo)
    
    Returns:
        ID do documento no Firestore
    """
    try:
        db = get_db()
        
        # Remove _id dos dados (é metadado)
        acordo_para_salvar = {k: v for k, v in acordo_data.items() if k != '_id'}
        
        if acordo_id:
            # UPDATE: Atualizar acordo existente
            import time
            acordo_para_salvar['updated_at'] = time.time()
            
            db.collection('agreements').document(acordo_id).update(acordo_para_salvar)
            
            # Invalida cache
            invalidar_cache_acordos()
            
            return acordo_id
        else:
            # CREATE: Criar novo acordo
            import time
            acordo_para_salvar['created_at'] = time.time()
            
            # Salva no Firestore
            doc_ref = db.collection('agreements').add(acordo_para_salvar)
            acordo_id = doc_ref[1].id
            
            # Invalida cache
            invalidar_cache_acordos()
            
            return acordo_id
        
    except Exception as e:
        print(f"[ERROR] Erro ao salvar/atualizar acordo no Firestore: {e}")
        raise


def invalidar_cache_acordos():
    """
    Invalida o cache de acordos, forçando nova busca no Firestore.
    """
    global _cache_acordos, _cache_timestamp
    
    with _cache_lock:
        _cache_acordos = None
        _cache_timestamp = None

