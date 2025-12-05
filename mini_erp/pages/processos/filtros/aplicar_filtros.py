"""
aplicar_filtros.py - Aplica todos os filtros em sequência.

Orquestra a aplicação de todos os filtros aos processos.
"""

from typing import List, Dict, Any

from .filtro_pesquisa import aplicar_filtro_pesquisa
from .filtro_area import aplicar_filtro_area
from .filtro_casos import aplicar_filtro_casos
from .filtro_clientes import aplicar_filtro_clientes, aplicar_filtro_parte_contraria
from .filtro_status import aplicar_filtro_status


def aplicar_todos_filtros(
    rows: List[Dict[str, Any]],
    filtros: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Aplica todos os filtros aos processos em sequência.
    
    IMPORTANTE: Se nenhum filtro estiver aplicado, retorna TODOS os processos.
    Não exclui processos com status vazio ou None quando nenhum filtro está ativo.
    
    Args:
        rows: Lista de processos/acompanhamentos
        filtros: Dicionário com valores dos filtros:
            - search_term: str - Termo de pesquisa
            - area: str - Área jurídica
            - case: str - Caso vinculado
            - client: str - Cliente
            - parte: str - Parte (mesmo que clientes)
            - opposing: str - Parte contrária
            - status: str - Status do processo
    
    Returns:
        Lista filtrada de processos
    """
    filtrados = rows
    
    # Lista de filtros ativos para log
    filtros_ativos = []
    
    # Aplica cada filtro se houver valor
    if filtros.get('search_term'):
        termo = filtros['search_term'].strip()
        if termo:
            filtrados = aplicar_filtro_pesquisa(filtrados, termo)
            filtros_ativos.append(f"pesquisa='{termo}'")
    
    if filtros.get('area'):
        area = filtros['area'].strip()
        if area:
            filtrados = aplicar_filtro_area(filtrados, area)
            filtros_ativos.append(f"área='{area}'")
    
    if filtros.get('case'):
        caso = filtros['case'].strip()
        if caso:
            filtrados = aplicar_filtro_casos(filtrados, caso)
            filtros_ativos.append(f"caso='{caso}'")
    
    if filtros.get('client'):
        cliente = filtros['client'].strip()
        if cliente:
            filtrados = aplicar_filtro_clientes(filtrados, cliente)
            filtros_ativos.append(f"cliente='{cliente}'")
    
    if filtros.get('parte'):
        parte = filtros['parte'].strip()
        if parte:
            # Parte usa mesma lógica que clientes
            filtrados = aplicar_filtro_clientes(filtrados, parte)
            filtros_ativos.append(f"parte='{parte}'")
    
    if filtros.get('opposing'):
        opposing = filtros['opposing'].strip()
        if opposing:
            filtrados = aplicar_filtro_parte_contraria(filtrados, opposing)
            filtros_ativos.append(f"parte_contrária='{opposing}'")
    
    if filtros.get('status'):
        status = filtros['status'].strip()
        if status:
            filtrados = aplicar_filtro_status(filtrados, status)
            filtros_ativos.append(f"status='{status}'")
    
    # Log de debug
    if filtros_ativos:
        print(f"[FILTER_ROWS] Aplicando filtros: {', '.join(filtros_ativos)}")
        print(f"[FILTER_ROWS] Total de registros após filtros: {len(filtrados)}")
    else:
        print(f"[FILTER_ROWS] Nenhum filtro ativo - retornando todos os {len(filtrados)} registros")
    
    return filtrados




