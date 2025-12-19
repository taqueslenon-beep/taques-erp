"""
Módulo de operações de banco de dados para prioridades.

Contém funções CRUD para gerenciar prioridades no Firestore.
"""

from typing import List, Dict, Any, Optional
from ..firebase_config import get_db
from ..models.prioridade import (
    PRIORIDADES_PADRAO,
    Prioridade,
    validar_prioridade,
    normalizar_prioridade
)


# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

def inicializar_prioridades() -> bool:
    """
    Inicializa as 4 prioridades padrão no Firestore se não existirem.
    
    Cria os documentos P1, P2, P3, P4 na coleção 'prioridades'.
    Se já existirem, não sobrescreve (preserva dados existentes).
    
    Returns:
        True se inicialização foi bem-sucedida, False caso contrário
    """
    try:
        db = get_db()
        collection_ref = db.collection('prioridades')
        
        prioridades_criadas = 0
        prioridades_existentes = 0
        
        for prioridade_data in PRIORIDADES_PADRAO:
            codigo = prioridade_data['codigo']
            doc_ref = collection_ref.document(codigo)
            
            # Verifica se já existe
            if doc_ref.get().exists:
                prioridades_existentes += 1
                continue
            
            # Cria novo documento
            doc_ref.set(prioridade_data)
            prioridades_criadas += 1
        
        if prioridades_criadas > 0:
            print(f"✅ {prioridades_criadas} prioridade(s) criada(s) no Firestore")
        
        if prioridades_existentes > 0:
            print(f"ℹ️  {prioridades_existentes} prioridade(s) já existente(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar prioridades: {e}")
        return False


# =============================================================================
# LEITURA
# =============================================================================

def listar_prioridades() -> List[Dict[str, Any]]:
    """
    Retorna lista de todas as prioridades ordenadas por ordem (1-4).
    
    Returns:
        Lista de dicionários com dados das prioridades, ordenada por ordem
    """
    try:
        db = get_db()
        collection_ref = db.collection('prioridades')
        
        # Busca todas as prioridades
        docs = collection_ref.stream()
        
        prioridades = []
        for doc in docs:
            data = doc.to_dict()
            if data:
                prioridades.append(data)
        
        # Ordena por ordem (1-4)
        prioridades.sort(key=lambda x: x.get('ordem', 999))
        
        return prioridades
        
    except Exception as e:
        print(f"⚠️  Erro ao listar prioridades: {e}")
        # Retorna prioridades padrão em caso de erro
        return PRIORIDADES_PADRAO.copy()


def obter_prioridade(codigo: str) -> Optional[Dict[str, Any]]:
    """
    Retorna dados de uma prioridade específica.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Dicionário com dados da prioridade ou None se não encontrada
    """
    if not validar_prioridade(codigo):
        print(f"⚠️  Código de prioridade inválido: {codigo}")
        return None
    
    try:
        db = get_db()
        doc_ref = db.collection('prioridades').document(codigo)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        
        # Se não existe no Firestore, retorna da lista padrão
        for prioridade in PRIORIDADES_PADRAO:
            if prioridade['codigo'] == codigo:
                return prioridade.copy()
        
        return None
        
    except Exception as e:
        print(f"⚠️  Erro ao obter prioridade {codigo}: {e}")
        # Retorna da lista padrão em caso de erro
        for prioridade in PRIORIDADES_PADRAO:
            if prioridade['codigo'] == codigo:
                return prioridade.copy()
        return None


def obter_cor_prioridade(codigo: str) -> str:
    """
    Retorna a cor hexadecimal de uma prioridade.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Cor hexadecimal (ex: '#DC2626')
    """
    prioridade = obter_prioridade(codigo)
    if prioridade:
        return prioridade.get('cor_hex', '#6B7280')
    
    # Fallback para P4
    return PRIORIDADES_PADRAO[3]['cor_hex']


def obter_ordem_prioridade(codigo: str) -> int:
    """
    Retorna a ordem numérica de uma prioridade.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Ordem numérica (1-4)
    """
    prioridade = obter_prioridade(codigo)
    if prioridade:
        return prioridade.get('ordem', 4)
    
    # Fallback para P4
    return PRIORIDADES_PADRAO[3]['ordem']











