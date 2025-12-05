"""
filtro_status.py - Filtro por status do processo.

Filtra processos por status (Em andamento, Concluído, Futuro/Previsto, etc).
"""

from typing import List, Dict, Any


def aplicar_filtro_status(rows: List[Dict[str, Any]], valor_filtro: str) -> List[Dict[str, Any]]:
    """
    Aplica filtro de status aos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
        valor_filtro: Valor do filtro de status
    
    Returns:
        Lista filtrada de processos
    """
    if not valor_filtro or not valor_filtro.strip():
        return rows
    
    valor_limpo = valor_filtro.strip()
    filtrados = [
        r for r in rows 
        if (r.get('status') or '').strip() == valor_limpo
    ]
    
    return filtrados


def obter_opcoes_status(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Extrai opções únicas de status dos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
    
    Returns:
        Lista de status únicos, ordenados
    """
    statuses = set()
    for r in rows:
        status = r.get('status', '')
        if status and str(status).strip():
            statuses.add(str(status).strip())
    
    return [''] + sorted(statuses)




