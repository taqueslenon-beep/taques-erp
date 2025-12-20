"""
Módulo de operações de banco de dados para integração de prioridades com casos.

Contém funções para atualizar e consultar prioridades de casos no Firestore.
"""

from typing import List, Dict, Any, Optional
from ..firebase_config import get_db
from ..core import invalidate_cache, get_cases_list
from ..models.prioridade import (
    validar_prioridade,
    normalizar_prioridade,
    PRIORIDADE_PADRAO
)


# =============================================================================
# ATUALIZAÇÃO DE PRIORIDADES
# =============================================================================

def atualizar_prioridade_caso(caso_id: str, prioridade: str) -> bool:
    """
    Atualiza a prioridade de um caso específico.
    
    Args:
        caso_id: ID do caso (slug) no Firestore
        prioridade: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        True se atualização foi bem-sucedida, False caso contrário
    """
    if not caso_id:
        print("⚠️  ID do caso não fornecido")
        return False
    
    # Normaliza e valida a prioridade
    prioridade_normalizada = normalizar_prioridade(prioridade)
    
    if not validar_prioridade(prioridade_normalizada):
        print(f"⚠️  Prioridade inválida: {prioridade}")
        return False
    
    try:
        db = get_db()
        case_ref = db.collection('cases').document(caso_id)
        
        # Verifica se o caso existe
        if not case_ref.get().exists:
            print(f"⚠️  Caso não encontrado: {caso_id}")
            return False
        
        # Atualiza a prioridade
        case_ref.update({'prioridade': prioridade_normalizada})
        
        # Invalida cache para forçar reload
        invalidate_cache('cases')
        
        print(f"✅ Prioridade do caso {caso_id} atualizada para {prioridade_normalizada}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar prioridade do caso {caso_id}: {e}")
        return False


# =============================================================================
# CONSULTAS POR PRIORIDADE
# =============================================================================

def listar_casos_por_prioridade(prioridade: str) -> List[Dict[str, Any]]:
    """
    Retorna lista de casos filtrados por prioridade.
    
    Args:
        prioridade: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Lista de dicionários com dados dos casos da prioridade especificada
    """
    if not validar_prioridade(prioridade):
        print(f"⚠️  Prioridade inválida: {prioridade}")
        return []
    
    try:
        # Normaliza a prioridade
        prioridade_normalizada = normalizar_prioridade(prioridade)
        
        # Busca casos com a prioridade especificada
        db = get_db()
        cases_query = db.collection('cases').where('prioridade', '==', prioridade_normalizada)
        docs = cases_query.stream()
        
        casos = []
        for doc in docs:
            case_data = doc.to_dict()
            if case_data:
                case_data['_id'] = doc.id
                casos.append(case_data)
        
        return casos
        
    except Exception as e:
        print(f"⚠️  Erro ao listar casos por prioridade {prioridade}: {e}")
        # Fallback: busca em memória usando get_cases_list
        try:
            todos_casos = get_cases_list()
            return [
                caso for caso in todos_casos
                if normalizar_prioridade(caso.get('prioridade')) == normalizar_prioridade(prioridade)
            ]
        except Exception as e2:
            print(f"❌ Erro no fallback: {e2}")
            return []


def contar_casos_por_prioridade() -> Dict[str, int]:
    """
    Retorna dicionário com contagem de casos por prioridade.
    
    Returns:
        Dicionário no formato: {'P1': 5, 'P2': 10, 'P3': 8, 'P4': 20}
    """
    try:
        db = get_db()
        collection_ref = db.collection('cases')
        
        # Inicializa contadores
        contadores = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
        
        # Busca todos os casos
        docs = collection_ref.stream()
        
        for doc in docs:
            case_data = doc.to_dict()
            if case_data:
                prioridade = normalizar_prioridade(case_data.get('prioridade'))
                if prioridade in contadores:
                    contadores[prioridade] += 1
                else:
                    # Casos sem prioridade ou com prioridade inválida contam como P4
                    contadores['P4'] += 1
        
        return contadores
        
    except Exception as e:
        print(f"⚠️  Erro ao contar casos por prioridade: {e}")
        # Fallback: busca em memória
        try:
            todos_casos = get_cases_list()
            contadores = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
            
            for caso in todos_casos:
                prioridade = normalizar_prioridade(caso.get('prioridade'))
                if prioridade in contadores:
                    contadores[prioridade] += 1
                else:
                    contadores['P4'] += 1
            
            return contadores
        except Exception as e2:
            print(f"❌ Erro no fallback: {e2}")
            return {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}


def obter_casos_sem_prioridade() -> List[Dict[str, Any]]:
    """
    Retorna lista de casos que não possuem prioridade definida.
    
    Útil para migração de dados existentes.
    
    Returns:
        Lista de dicionários com dados dos casos sem prioridade
    """
    try:
        db = get_db()
        collection_ref = db.collection('cases')
        
        # Busca casos sem campo 'prioridade' ou com prioridade None/vazia
        docs = collection_ref.stream()
        
        casos_sem_prioridade = []
        for doc in docs:
            case_data = doc.to_dict()
            if case_data:
                prioridade = case_data.get('prioridade')
                if not prioridade or prioridade.strip() == '':
                    case_data['_id'] = doc.id
                    casos_sem_prioridade.append(case_data)
        
        return casos_sem_prioridade
        
    except Exception as e:
        print(f"⚠️  Erro ao obter casos sem prioridade: {e}")
        # Fallback: busca em memória
        try:
            todos_casos = get_cases_list()
            return [
                caso for caso in todos_casos
                if not caso.get('prioridade') or caso.get('prioridade', '').strip() == ''
            ]
        except Exception as e2:
            print(f"❌ Erro no fallback: {e2}")
            return []


def aplicar_prioridade_padrao_casos_sem_prioridade() -> int:
    """
    Aplica prioridade padrão (P4) a todos os casos que não possuem prioridade.
    
    Útil para migração de dados existentes.
    
    Returns:
        Número de casos atualizados
    """
    casos_sem_prioridade = obter_casos_sem_prioridade()
    
    if not casos_sem_prioridade:
        print("ℹ️  Nenhum caso sem prioridade encontrado")
        return 0
    
    atualizados = 0
    db = get_db()
    
    try:
        for caso in casos_sem_prioridade:
            caso_id = caso.get('_id') or caso.get('slug')
            if caso_id:
                if atualizar_prioridade_caso(caso_id, PRIORIDADE_PADRAO):
                    atualizados += 1
        
        print(f"✅ {atualizados} caso(s) atualizado(s) com prioridade padrão (P4)")
        return atualizados
        
    except Exception as e:
        print(f"❌ Erro ao aplicar prioridade padrão: {e}")
        return atualizados












