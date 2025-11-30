"""
obter_opcoes_filtros.py - Extrai opções únicas para dropdowns de filtros.

Consolida todas as funções de extração de opções de filtros.
"""

from typing import List, Dict, Any

from .filtro_area import obter_opcoes_area
from .filtro_casos import obter_opcoes_casos
from .filtro_clientes import obter_opcoes_clientes, obter_opcoes_parte_contraria
from .filtro_status import obter_opcoes_status


def obter_todas_opcoes_filtros(rows: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extrai todas as opções únicas para todos os filtros.
    
    Args:
        rows: Lista de processos/acompanhamentos
    
    Returns:
        Dicionário com opções de cada filtro:
        {
            'area': List[str],
            'cases': List[str],
            'clients': List[str],
            'parte': List[str],  # Mesmo que clients
            'opposing': List[str],
            'status': List[str]
        }
    """
    opcoes = {
        'area': obter_opcoes_area(rows),
        'cases': obter_opcoes_casos(rows),
        'clients': obter_opcoes_clientes(rows),
        'parte': obter_opcoes_clientes(rows),  # Parte usa mesma lista que clientes
        'opposing': obter_opcoes_parte_contraria(rows),
        'status': obter_opcoes_status(rows),
    }
    
    print(f"[FILTER_OPTIONS] ✓ Opções construídas: área={len(opcoes['area'])}, casos={len(opcoes['cases'])}, clientes={len(opcoes['clients'])}, status={len(opcoes['status'])}")
    
    return opcoes

