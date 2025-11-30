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
    'e-STF',
    'e-STJ',
    'eProtocolo',
    'Projudi',
    'SEI - Ibama',
    'SGPE',
    'SinFAT',
    # Sistemas internos do Ministério Público
    'Sistema Interno - MPPR',  # Ministério Público do Paraná
    'Sistema Interno - MPSC',  # Ministério Público de Santa Catarina
    # Processo físico (não eletrônico)
    'Processo físico 📁',
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
    'Em monitoramento',
    'Futuro/Previsto'
]

# Constantes de status padronizadas (para evitar inconsistências)
STATUS_EM_ANDAMENTO = 'Em andamento'
STATUS_CONCLUIDO = 'Concluído'
STATUS_CONCLUIDO_PENDENCIAS = 'Concluído com pendências'
STATUS_EM_MONITORAMENTO = 'Em monitoramento'
STATUS_FUTURO_PREVISTO = 'Futuro/Previsto'

# Dicionário de mapeamento de status (para compatibilidade e validação)
STATUS_MAP = {
    'EM_ANDAMENTO': STATUS_EM_ANDAMENTO,
    'CONCLUIDO': STATUS_CONCLUIDO,
    'CONCLUIDO_PENDENCIAS': STATUS_CONCLUIDO_PENDENCIAS,
    'EM_MONITORAMENTO': STATUS_EM_MONITORAMENTO,
    'FUTURO_PREVISTO': STATUS_FUTURO_PREVISTO,
}

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
    number: str
    system: str
    link: str  # Link externo do protocolo (ex: URL do sistema)
    observations: str
    case_ids: List[str]  # Slugs dos casos vinculados
    process_ids: List[str]  # IDs dos processos vinculados


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
    data_abertura: Optional[str]  # Data de abertura aproximada: DD/MM/AAAA, MM/AAAA ou AAAA
    # Hierarquia de Processos (pai-filho-neto-bisneto)
    parent_id: Optional[str]  # ID do processo pai (DEPRECATED - usar parent_ids)
    parent_ids: List[str]  # Lista de IDs dos processos pais (vínculos)
    depth: int  # Nível: 0=raiz, 1=filho, 2=neto, 3=bisneto, etc.
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


# =============================================================================
# ACOMPANHAMENTO DE TERCEIROS
# =============================================================================

# Status de acompanhamento
THIRD_PARTY_MONITORING_STATUS_OPTIONS = ['ativo', 'concluído', 'suspenso']

# Tipos de acompanhamento
THIRD_PARTY_MONITORING_TYPE_OPTIONS = [
    'Acompanhamento de Sócio',
    'Acompanhamento Familiar',
    'Acompanhamento Corporativo',
    'Acompanhamento de Devedor',
    'Acompanhamento de Jurisprudência',
    'Acompanhamento de Legislação',
    'Acompanhamento de Risco',
    'Acompanhamento de Oportunidade',
    'Acompanhamento de Conformidade',
]

# Níveis de envolvimento
THIRD_PARTY_INVOLVEMENT_LEVEL_OPTIONS = [
    'Acompanhamento Informativo',
    'Acompanhamento Consultivo',
    'Acompanhamento Ativo',
    'Acompanhamento de Interesse',
]

# Intensidade de monitoramento
THIRD_PARTY_MONITORING_INTENSITY_OPTIONS = [
    'Monitoramento Passivo',
    'Monitoramento Regular',
    'Monitoramento Intenso',
]

# Frequência de check-in
THIRD_PARTY_CHECK_IN_FREQUENCY_OPTIONS = [
    'Semanal',
    'Quinzenal',
    'Mensal',
    'Trimestral',
    'Semestral',
    'Conforme necessário',
]


class ThirdPartyMonitoringDict(TypedDict, total=False):
    """Estrutura de um acompanhamento de terceiros."""
    id: str  # Identificador único (gerado automaticamente)
    # Campos básicos
    link_do_processo: str
    tipo_de_processo: str
    data_de_abertura: str
    # Partes envolvidas (novo schema)
    parte_ativa: List[str]  # Obrigatório - array de IDs/nomes
    parte_passiva: List[str]  # Opcional - array de IDs/nomes
    outros_envolvidos: List[str]  # Opcional - array de IDs/nomes
    # Vínculos
    processos_pais: List[str]
    cases: List[str]
    # Campos legados (para compatibilidade durante migração)
    clientes: List[str]  # Deprecated - usar parte_ativa
    client_id: str  # Deprecated
    client_name: str  # Deprecated
    parte_contraria: List[str]  # Deprecated - usar parte_passiva
    third_party_name: str  # Deprecated - nome da pessoa/entidade sendo acompanhada
    # Status e metadata
    status: str
    created_at: str
    updated_at: str
    process_title: str  # Título/descrição do acompanhamento
    process_number: Optional[str]  # Número do processo (se aplicável)
    monitoring_type: str  # Tipo de acompanhamento
    start_date: str  # Data de início (formato DD/MM/AAAA)
    status: str  # ativo | concluído | suspenso
    created_at: str  # Data de criação (ISO format)
    updated_at: str  # Data última atualização (ISO format)
    observations: Optional[str]  # Observações adicionais


