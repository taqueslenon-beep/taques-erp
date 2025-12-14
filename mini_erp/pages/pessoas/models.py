"""
Módulo de modelos e constantes para o módulo Pessoas.
Define tipos de dados, constantes e estruturas usadas em todo o módulo.
"""
from typing import TypedDict, List, Optional

# =============================================================================
# CONSTANTES - TIPOS DE CLIENTE
# =============================================================================

# Opções simplificadas: apenas PF e PJ (lista para compatibilidade com NiceGUI)
CLIENT_TYPE_OPTIONS = ['PF', 'PJ']

# Opções para tipo de filial PJ (lista para compatibilidade com NiceGUI)
BRANCH_TYPE_OPTIONS = ['Matriz', 'Filial']

# Labels exibidos – mantemos mapeamento para registros antigos, mas dropdown usa apenas PF e PJ
CLIENT_TYPE_LABELS = {
    'PF': 'PF',
    'PJ': 'PJ',
    'PF/PJ': 'PF e PJ',  # legado, não exibido no seletor
}

DEFAULT_CLIENT_TYPE = 'PF'

# =============================================================================
# CONSTANTES - TIPOS DE ENTIDADE (Outros Envolvidos)
# =============================================================================

ENTITY_TYPES = ['PF', 'PJ', 'Órgão Público']

# =============================================================================
# CONSTANTES - ORIGEM DE LEADS
# =============================================================================

LEAD_ORIGEM_OPTIONS = ['Indicação', 'Site', 'Telefone', 'Evento', 'Redes Sociais', 'Outro']

# =============================================================================
# CONSTANTES - TIPOS DE VÍNCULOS
# =============================================================================

BOND_TYPES = [
    'Pai', 'Mãe', 'Filho(a)', 'Irmão(ã)', 'Cônjuge', 'Avô(ó)', 'Neto(a)',
    'Tio(a)', 'Sobrinho(a)', 'Primo(a)', 'Sócio(a)', 'CNPJ relacionado',
    'Representante legal', 'Procurador', 'Outro'
]

# =============================================================================
# TIPOS ESTRUTURADOS (TypedDict)
# =============================================================================

class Partner(TypedDict, total=False):
    """Estrutura de um sócio/proprietário de PJ."""
    full_name: str
    cpf: str
    share: str  # Participação societária (%)
    type: str   # 'client' ou 'opposing_party'


class Bond(TypedDict, total=False):
    """Estrutura de um vínculo entre pessoas."""
    person: str    # Nome da pessoa vinculada
    type: str      # Tipo do vínculo (de BOND_TYPES)
    source: str    # Fonte: '[C]' para cliente, '[PC]' para parte contrária


class Cliente(TypedDict, total=False):
    """Estrutura de um cliente."""
    _id: str
    full_name: str
    nome_exibicao: str    # Campo obrigatório para exibição (renomeado de display_name)
    display_name: str     # Mantido para compatibilidade
    nickname: str
    client_type: str  # 'PF' ou 'PJ'
    cpf: str
    cnpj: str
    cpf_cnpj: str     # Campo de exibição formatado
    document: str     # Alias para cpf_cnpj (compatibilidade)
    email: str
    phone: str
    bonds: List[Bond]
    # Campos específicos de PJ
    branch_type: str  # 'Matriz' ou 'Filial'
    partners: List[Partner]
    created_at: any
    updated_at: any


class ParteContraria(TypedDict, total=False):
    """Estrutura de um outro envolvido (parte contrária)."""
    _id: str
    full_name: str
    nome_exibicao: str    # Campo obrigatório para exibição (renomeado de display_name)
    display_name: str     # Mantido para compatibilidade
    nickname: str
    cpf_cnpj: str
    document: str     # Alias para cpf_cnpj (compatibilidade)
    entity_type: str  # 'PF', 'PJ' ou 'Órgão Público'
    email: str
    phone: str
    created_at: any
    updated_at: any


# =============================================================================
# DEFINIÇÕES DE COLUNAS PARA TABELAS
# =============================================================================

CLIENTS_TABLE_COLUMNS = [
    {'name': 'full_name', 'label': 'Nome Completo', 'field': 'full_name', 'align': 'left', 'sortable': True},
    {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left'},
    {'name': 'cpf_cnpj', 'label': 'CPF/CNPJ', 'field': 'cpf_cnpj', 'align': 'left'},
    {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
]

OPPOSING_TABLE_COLUMNS = [
    {'name': 'full_name', 'label': 'Nome Completo', 'field': 'full_name', 'align': 'left', 'sortable': True},
    {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left'},
    {'name': 'entity_type', 'label': 'Tipo', 'field': 'entity_type', 'align': 'left'},
    {'name': 'cpf_cnpj', 'label': 'CPF/CNPJ', 'field': 'cpf_cnpj', 'align': 'left'},
    {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
]

LEADS_TABLE_COLUMNS = [
    {'name': 'nome', 'label': 'Nome', 'field': 'nome', 'align': 'left', 'sortable': True},
    {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left'},
    {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
    {'name': 'telefone', 'label': 'Telefone', 'field': 'telefone', 'align': 'left'},
    {'name': 'origem', 'label': 'Origem', 'field': 'origem', 'align': 'left'},
    {'name': 'cpf_cnpj', 'label': 'CPF/CNPJ', 'field': 'cpf_cnpj', 'align': 'left'},
    {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
]

# =============================================================================
# CONFIGURAÇÕES DE GRUPOS PARA EXIBIÇÃO
# =============================================================================

CLIENT_GROUP_CONFIG = [
    {'type': 'PJ', 'title': 'Pessoas Jurídicas – PJ'},
    {'type': 'PF', 'title': 'Pessoas Físicas – PF'},
]


