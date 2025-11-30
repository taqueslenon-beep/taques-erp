"""
processos - Módulo de gerenciamento de processos jurídicos.

Este pacote contém todos os componentes necessários para o gerenciamento
de processos no Zantech ERP, incluindo:

- models.py: Constantes, estruturas de dados e configurações
- database.py: Operações de banco de dados via Firestore
- business_logic.py: Validações, filtros e lógica de negócio
- ui_components.py: Templates de UI e slots de tabela
- utils.py: Funções auxiliares e formatadores
- processos_page.py: Página principal do módulo

Uso:
    A função principal `processos()` é automaticamente registrada como
    rota '/processos' pelo NiceGUI quando importada.
"""

# Exporta a função principal para registro de rotas
from .visualizacoes.visualizacao_padrao import processos
from .visualizacoes.visualizacao_acesso import acesso_processos

# Exporta módulos para acesso externo se necessário
from . import models
from . import database
from . import business_logic
from . import ui_components
from . import utils

__all__ = [
    'processos',
    'acesso_processos',
    'models',
    'database',
    'business_logic',
    'ui_components',
    'utils',
]


