"""
models.py - Estruturas de dados, constantes e configurações para o módulo de Processos.

Este módulo contém:
- Constantes de tipos e opções de seleção
- Configuração de colunas da tabela
- Schemas e estruturas de dados
"""

from typing import Dict, List, Any, TypedDict, Optional


# =============================================================================
# CONSTANTES DE TIPOS E OPÇÕES
# =============================================================================

# Tipos de processo
PROCESS_TYPE_OPTIONS = ['Existente', 'Futuro']

# Status que indicam processo finalizado
FINALIZED_STATUSES = {'Concluído', 'Concluído com pendências'}

# Opções de sistemas processuais
SYSTEM_OPTIONS = [
    'eproc - TJSC - 1ª instância',
    'eproc - TJSC - 2ª instância',
    'eproc - TRF-4 - 1ª instância',
    'eproc - TRF-4 - 2ª instância',
    'Projudi',
    'SGPE',
    'SEI - Ibama',
    'SinFAT',
    'e-STF',
    'e-STJ'
]

# Opções de núcleo
NUCLEO_OPTIONS = ['Ambiental']

# Opções de área
AREA_OPTIONS = ['Administrativo', 'Criminal', 'Cível', 'Tributário', 'Técnico/projetos', 'Outros']

# Opções de status do processo
STATUS_OPTIONS = [
    'Em andamento', 
    'Concluído', 
    'Concluído com pendências', 
    'Em monitoramento'
]

# Opções de resultado do processo
RESULT_OPTIONS = ['Ganho', 'Perdido', 'Neutro']

# =============================================================================
# OPÇÕES PARA CENÁRIOS
# =============================================================================

SCENARIO_TYPE_OPTIONS = ['🟢 Positivo', '⚪ Neutro', '🔴 Negativo']
SCENARIO_CHANCE_OPTIONS = ['Muito alta', 'Alta', 'Média', 'Baixa', 'Muito baixa']
SCENARIO_IMPACT_OPTIONS = ['Muito bom', 'Bom', 'Moderado', 'Ruim', 'Muito ruim']
SCENARIO_STATUS_OPTIONS = ['Mapeado', 'Em análise', 'Próximo de ocorrer', 'Ocorrido', 'Descartado']

# =============================================================================
# CONFIGURAÇÃO DE COLUNAS DA TABELA
# =============================================================================

COLUMNS_CONFIG = [
    {
        'key': 'area',
        'label': 'Área',
        'definition': {
            'name': 'area', 
            'label': 'Área', 
            'field': 'area', 
            'align': 'left', 
            'sortable': True, 
            'style': 'width: 120px; max-width: 120px;'
        }
    },
    {
        'key': 'title',
        'label': 'Título',
        'definition': {
            'name': 'title', 
            'label': 'Título', 
            'field': 'title', 
            'align': 'left', 
            'sortable': True, 
            'style': 'max-width: 250px; white-space: normal; vertical-align: top;'
        }
    },
    {
        'key': 'cases',
        'label': 'Casos Vinculados',
        'definition': {
            'name': 'cases', 
            'label': 'Casos Vinculados', 
            'field': 'cases', 
            'align': 'left', 
            'style': 'max-width: 150px; white-space: normal; vertical-align: top;'
        }
    },
    {
        'key': 'number',
        'label': 'Número',
        'definition': {
            'name': 'number', 
            'label': 'Número', 
            'field': 'number', 
            'align': 'left', 
            'sortable': True, 
            'style': 'max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
        }
    },
    {
        'key': 'clients',
        'label': 'Clientes',
        'definition': {
            'name': 'clients', 
            'label': 'Clientes', 
            'field': 'clients', 
            'align': 'left', 
            'style': 'white-space: normal; vertical-align: top; max-width: 150px;'
        }
    },
    {
        'key': 'opposing',
        'label': 'Parte Contrária',
        'definition': {
            'name': 'opposing', 
            'label': 'Parte Contrária', 
            'field': 'opposing', 
            'align': 'left', 
            'style': 'max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
        }
    },
    {
        'key': 'status',
        'label': 'Status',
        'definition': {
            'name': 'status', 
            'label': 'Status', 
            'field': 'status', 
            'align': 'center', 
            'sortable': True, 
            'style': 'width: 150px; max-width: 150px;'
        }
    },
    {
        'key': 'nucleo',
        'label': 'Núcleo',
        'definition': {
            'name': 'nucleo', 
            'label': 'Núcleo', 
            'field': 'nucleo', 
            'align': 'center', 
            'sortable': True, 
            'style': 'max-width: 80px;'
        }
    },
    {
        'key': 'system',
        'label': 'Sistema',
        'definition': {
            'name': 'system', 
            'label': 'Sistema', 
            'field': 'system', 
            'align': 'left', 
            'sortable': True, 
            'style': 'max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
        }
    },
    {
        'key': 'link',
        'label': 'Link',
        'definition': {
            'name': 'link', 
            'label': 'Link', 
            'field': 'link', 
            'align': 'center', 
            'style': 'max-width: 50px;'
        }
    },
]

# Colunas visíveis por padrão (nesta ordem): área, título, casos vinculados, número, clientes, parte contrária, status
DEFAULT_VISIBLE_COLUMNS = ['area', 'title', 'cases', 'number', 'clients', 'opposing', 'status']

# =============================================================================
# CSS CUSTOMIZADO PARA TABELAS E SIDEBAR
# =============================================================================

PROCESSES_TABLE_CSS = '''
    .processes-table {
        table-layout: fixed !important;
        width: 100% !important;
    }
    .processes-table th, .processes-table td {
        padding: 6px 8px !important;
        font-size: 12px !important;
    }
    .processes-table th {
        font-size: 11px !important;
        font-weight: 600 !important;
    }
    .processes-table .q-table__middle tbody tr:nth-child(odd) {
        background: #f5f6f8 !important;
    }
    .processes-table .q-table__middle tbody tr:nth-child(even) {
        background: #ffffff !important;
    }
    .processes-table .q-table__middle tbody tr {
        border-bottom: 1px solid #111827 !important;
    }
    .process-sidebar-tabs .q-tab {
        justify-content: flex-start !important;
        flex-direction: row !important;
        padding: 6px 12px !important;
        min-height: 32px !important;
        height: 32px !important;
        font-size: 11px !important;
        color: white !important;
        border-radius: 0 !important;
        text-transform: none !important;
        text-align: left !important;
        align-items: center !important;
    }
    .process-sidebar-tabs .q-tab:hover {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
    }
    .process-sidebar-tabs .q-tab--active {
        background: rgba(255,255,255,0.12) !important;
        color: white !important;
        border-left: 2px solid rgba(255,255,255,0.8) !important;
    }
    .process-sidebar-tabs .q-tab__content {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        width: 100% !important;
    }
    .process-sidebar-tabs .q-tab__icon {
        font-size: 16px !important;
        margin: 0 !important;
        color: white !important;
        align-self: center !important;
        flex-shrink: 0 !important;
    }
    .process-sidebar-tabs .q-tab__label {
        font-weight: 400 !important;
        letter-spacing: 0.2px !important;
        color: white !important;
        text-align: left !important;
        align-self: center !important;
    }
    .process-sidebar-tabs .q-tabs__content {
        overflow: visible !important;
    }
    .process-sidebar-tabs .q-tab__indicator {
        display: none !important;
    }
'''

# =============================================================================
# TYPE DEFINITIONS (para documentação e type hints)
# =============================================================================

class ScenarioDict(TypedDict, total=False):
    """Estrutura de um cenário de processo."""
    title: str
    type: str
    status: str
    impact: str
    chance: str
    obs: str


class ProtocolDict(TypedDict, total=False):
    """Estrutura de um protocolo de processo."""
    title: str
    date: str
    link: str
    by: str


class ProcessDict(TypedDict, total=False):
    """Estrutura de um processo."""
    title: str
    number: str
    system: str
    link: str
    nucleo: str
    area: str
    status: str
    result: Optional[str]
    process_type: str
    clients: List[str]
    opposing_parties: List[str]
    other_parties: List[str]
    cases: List[str]
    strategy_objectives: str
    legal_thesis: str
    strategy_observations: str
    scenarios: List[ScenarioDict]
    protocols: List[ProtocolDict]
    access_lawyer: bool
    access_technicians: bool
    access_client: bool
    access_lawyer_comment: str
    access_technicians_comment: str
    access_client_comment: str
    access_lawyer_requested: bool
    access_lawyer_granted: bool
    access_technicians_requested: bool
    access_technicians_granted: bool
    access_client_requested: bool
    access_client_granted: bool


