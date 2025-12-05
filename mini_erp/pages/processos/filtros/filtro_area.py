"""
filtro_area.py - Filtro por área jurídica.

Extrai e filtra processos por área (Administrativo, Criminal, Cível, etc).
"""

from typing import List, Dict, Any


def aplicar_filtro_area(rows: List[Dict[str, Any]], valor_filtro: str) -> List[Dict[str, Any]]:
    """
    Aplica filtro de área aos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
        valor_filtro: Valor do filtro de área
    
    Returns:
        Lista filtrada de processos
    """
    if not valor_filtro or not valor_filtro.strip():
        return rows
    
    valor_limpo = valor_filtro.strip()
    filtrados = [
        r for r in rows 
        if (r.get('area') or '').strip() == valor_limpo
    ]
    
    return filtrados


def obter_opcoes_area(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Extrai opções únicas de área dos processos.
    
    Args:
        rows: Lista de processos/acompanhamentos
    
    Returns:
        Lista de áreas únicas, ordenadas
    """
    areas = set()
    for r in rows:
        area = r.get('area', '')
        if area and str(area).strip():
            areas.add(str(area).strip())
    
    return [''] + sorted(areas)




