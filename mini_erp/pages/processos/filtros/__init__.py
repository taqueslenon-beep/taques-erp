"""
filtros - Módulo de filtros para processos.

Cada filtro é um módulo separado:
- filtro_area: Filtro por área jurídica
- filtro_casos: Filtro por casos vinculados
- filtro_clientes: Filtro por clientes
- filtro_status: Filtro por status
- filtro_pesquisa: Filtro de pesquisa por texto
- filtros_manager: Gerencia estado compartilhado de todos os filtros
- aplicar_filtros: Aplica todos os filtros em sequência
- obter_opcoes_filtros: Extrai opções para dropdowns
"""

from .filtros_manager import FiltrosManager, criar_gerenciador_filtros
from .filtro_helper import criar_dropdown_filtro
from .aplicar_filtros import aplicar_todos_filtros
from .obter_opcoes_filtros import obter_todas_opcoes_filtros

__all__ = [
    'FiltrosManager',
    'criar_gerenciador_filtros',
    'criar_dropdown_filtro',
    'aplicar_todos_filtros',
    'obter_todas_opcoes_filtros',
]

