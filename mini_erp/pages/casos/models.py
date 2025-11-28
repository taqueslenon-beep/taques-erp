"""
Módulo de modelos e constantes para o módulo de Casos.

Define constantes, opções de seleção e estado global usado
em toda a aplicação de gerenciamento de casos.
"""

from datetime import datetime

# =============================================================================
# OPÇÕES DE ESTADO (UF)
# =============================================================================

STATE_OPTIONS = ['Paraná', 'Santa Catarina']

# URLs das bandeiras oficiais dos estados (Wikimedia Commons)
STATE_FLAG_URLS = {
    'Paraná': 'https://upload.wikimedia.org/wikipedia/commons/9/93/Bandeira_do_Paran%C3%A1.svg',
    'Santa Catarina': 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Bandeira_de_Santa_Catarina.svg'
}

# =============================================================================
# TIPOS DE CASO
# =============================================================================

# Mapeamento de tipos de caso para visualização
CASE_TYPE_OPTIONS = ['Antigo', 'Novo', 'Futuro']

CASE_TYPE_EMOJIS = {
    'Antigo': '🔴',
    'Novo': '🔥',
    'Futuro': '🔮'
}

# Prefixos numéricos por tipo de caso
CASE_TYPE_PREFIX = {
    'Antigo': 1,
    'Novo': 2,
    'Futuro': 2  # Consolidado com 'Novo' sob Main ID 2
}

# =============================================================================
# CATEGORIA DO CASO
# =============================================================================

# Opções de categoria do caso (Contencioso ou Consultivo)
CASE_CATEGORY_OPTIONS = ['Contencioso', 'Consultivo']

# =============================================================================
# OPÇÕES DE DATA
# =============================================================================

# Opções de mês para seleção
MONTH_OPTIONS = [
    {'value': 1, 'label': 'Janeiro'},
    {'value': 2, 'label': 'Fevereiro'},
    {'value': 3, 'label': 'Março'},
    {'value': 4, 'label': 'Abril'},
    {'value': 5, 'label': 'Maio'},
    {'value': 6, 'label': 'Junho'},
    {'value': 7, 'label': 'Julho'},
    {'value': 8, 'label': 'Agosto'},
    {'value': 9, 'label': 'Setembro'},
    {'value': 10, 'label': 'Outubro'},
    {'value': 11, 'label': 'Novembro'},
    {'value': 12, 'label': 'Dezembro'},
]

# Opções de ano (de 2000 até ano atual + 5)
current_year = datetime.now().year
YEAR_OPTIONS = list(range(2000, current_year + 6))

# =============================================================================
# OPÇÕES DE STATUS
# =============================================================================

STATUS_OPTIONS = [
    'Em andamento', 
    'Concluído', 
    'Concluído com pendências', 
    'Em monitoramento'
]

# =============================================================================
# OPÇÕES DE PARTE CONTRÁRIA
# =============================================================================

PARTE_CONTRARIA_OPTIONS = {
    'MP': 'Ministério Público',
    'OAB': 'OAB',
    'Defesa': 'Defesa/Réu',
    'Autor': 'Autor/Demandante',
    'União': 'União',
    'Estado': 'Estado',
    'Município': 'Município',
    'INSS': 'INSS',
    'Receita Federal': 'Receita Federal',
    'Outro': 'Outro',
    '-': 'Não especificado'
}

# =============================================================================
# ESTADO GLOBAL DOS FILTROS
# =============================================================================

# Estado dos filtros (global para a página)
filter_state = {
    'search': '',
    'status': None,
    'client': None,
    'state': None,
    'category': None,  # Filtro por categoria: Contencioso ou Consultivo
    # Tipo de visualização: 'old' (antigos), 'new' (novos) ou 'future' (futuros)
    'case_type': 'old',
}


