"""
visualizacoes - Módulo de visualizações de processos.

Contém as diferentes formas de visualizar processos:
- Visualização padrão (tabela principal)
- Visualização de acesso aos processos
"""

from .visualizacao_padrao import processos
from .visualizacao_acesso import acesso_processos

__all__ = ['processos', 'acesso_processos']




