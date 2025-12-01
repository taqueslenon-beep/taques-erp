"""
filtro_pesquisa.py - Filtro de pesquisa por texto.

Permite buscar processos por título, número, etc.
"""

from typing import List, Dict, Any


def aplicar_filtro_pesquisa(rows: List[Dict[str, Any]], termo: str) -> List[Dict[str, Any]]:
    """
    Aplica filtro de pesquisa aos processos.
    
    Busca no título (usando title_raw para não incluir indentação hierárquica).
    
    Args:
        rows: Lista de processos/acompanhamentos
        termo: Termo de busca
    
    Returns:
        Lista filtrada de processos
    """
    if not termo or not termo.strip():
        return rows
    
    termo_lower = termo.lower()
    filtrados = [
        r for r in rows 
        if termo_lower in (r.get('title_raw') or r.get('title') or '').lower()
    ]
    
    return filtrados


