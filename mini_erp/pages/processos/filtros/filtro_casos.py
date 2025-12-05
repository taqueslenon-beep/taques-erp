"""
filtro_casos.py - Filtro por casos vinculados.

Filtra processos por casos vinculados, suportando múltiplos casos por processo
e acompanhamentos de terceiros.
"""

from typing import List, Dict, Any


def aplicar_filtro_casos(rows: List[Dict[str, Any]], valor_filtro: str) -> List[Dict[str, Any]]:
    """
    Aplica filtro de casos aos processos.
    
    Filtra processos e acompanhamentos de terceiros por caso vinculado.
    
    Lógica de filtragem:
    1. Normaliza valor do filtro (remove espaços, converte para minúsculas)
    2. Para cada processo, verifica se algum caso em cases_list corresponde
    3. Usa dupla verificação: igualdade exata OU substring matching
    4. Processos com múltiplos casos aparecem se qualquer caso corresponder
    
    Args:
        rows: Lista de processos/acompanhamentos
        valor_filtro: Valor do filtro de casos
    
    Returns:
        Lista filtrada de processos
    """
    if not valor_filtro or not valor_filtro.strip():
        return rows
    
    case_filter_value = valor_filtro.strip()
    
    filtrados = []
    for r in rows:
        cases_list = r.get('cases_list') or []
        
        # Verifica se algum caso corresponde ao filtro
        matches = any(
            str(c).strip().lower() == case_filter_value.lower() or 
            case_filter_value.lower() in str(c).strip().lower()
            for c in cases_list if c
        )
        
        if matches:
            filtrados.append(r)
    
    return filtrados


def obter_opcoes_casos(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Extrai opções únicas de casos dos processos.
    
    Extrai casos únicos do campo 'cases_list' de todos os processos,
    garantindo que apenas casos realmente vinculados apareçam no filtro.
    
    Args:
        rows: Lista de processos/acompanhamentos
    
    Returns:
        Lista de casos únicos, ordenados
    """
    all_cases = set()
    
    for row in rows:
        cases_list = row.get('cases_list') or []
        for case in cases_list:
            if case is None:
                continue
            
            case_str = str(case).strip()
            if not case_str:
                continue
            
            # Validação: ignora números puros soltos
            try:
                float_val = float(case_str)
                if case_str.replace('.', '').replace('-', '').isdigit():
                    continue
            except (ValueError, TypeError):
                pass
            
            all_cases.add(case_str)
    
    return [''] + sorted(all_cases, key=str.lower)




