"""
Constantes centralizadas do sistema Zantech ERP.

Este módulo centraliza todas as cores, opções e configurações 
compartilhadas entre diferentes módulos do sistema.
"""

# =============================================================================
# CORES DE ÁREAS JURÍDICAS (FONTE ÚNICA DE VERDADE)
# =============================================================================
# Cores usadas no módulo de Processos (badges nas tabelas) e no Painel (gráficos)
# Estas cores são aplicadas consistentemente em toda a aplicação

AREA_COLORS_BACKGROUND = {
    'Administrativo': '#d1d5db',      # cinza claro
    'Criminal': '#fecaca',            # vermelho claro
    'Cível': '#bfdbfe',               # azul claro
    'Civil': '#bfdbfe',               # azul claro (alias)
    'Tributário': '#ddd6fe',          # roxo claro
    'Técnico/projetos': '#bbf7d0',    # verde claro
    'Projeto/Técnicos': '#bbf7d0',    # verde claro (alias)
    'Outros': '#e5e7eb',              # cinza claro neutro
}

AREA_COLORS_TEXT = {
    'Administrativo': '#1f2937',      # cinza escuro
    'Criminal': '#7f1d1d',            # vermelho escuro
    'Cível': '#1e3a8a',               # azul escuro
    'Civil': '#1e3a8a',               # azul escuro (alias)
    'Tributário': '#4c1d95',          # roxo escuro
    'Técnico/projetos': '#14532d',    # verde escuro
    'Projeto/Técnicos': '#14532d',    # verde escuro (alias)
    'Outros': '#374151',              # cinza escuro neutro
}

AREA_COLORS_BORDER = {
    'Administrativo': '#9ca3af',      # cinza médio
    'Criminal': '#f87171',            # vermelho médio
    'Cível': '#60a5fa',               # azul médio
    'Civil': '#60a5fa',               # azul médio (alias)
    'Tributário': '#a78bfa',          # roxo médio
    'Técnico/projetos': '#4ade80',    # verde médio
    'Projeto/Técnicos': '#4ade80',    # verde médio (alias)
    'Outros': '#9ca3af',              # cinza médio neutro
}

# Cores principais para gráficos (usa a cor de fundo como cor principal)
AREA_COLORS_CHART = {
    'Administrativo': '#9ca3af',      # cinza médio (mais visível em gráficos)
    'Criminal': '#ef4444',            # vermelho
    'Cível': '#3b82f6',               # azul
    'Civil': '#3b82f6',               # azul (alias)
    'Tributário': '#8b5cf6',          # roxo
    'Técnico/projetos': '#22c55e',    # verde
    'Projeto/Técnicos': '#22c55e',    # verde (alias)
    'Outros': '#d1d5db',              # cinza claro
    'Não informado': '#9ca3af',       # cinza médio
}

# =============================================================================
# CORES DE STATUS (para casos e processos)
# =============================================================================
STATUS_COLORS = {
    'Em andamento': '#b45309',              # amarelo queimado
    'Concluído': '#166534',                 # verde escuro
    'Concluído com pendências': '#4d7c0f',  # verde militar
    'Em monitoramento': '#ea580c',          # laranja
    'Substabelecido': '#86efac',            # verde claro
    'Sem status': '#6b7280',                # cinza
}

# =============================================================================
# CORES DE PROBABILIDADE
# =============================================================================
PROBABILITY_COLORS = {
    'Alta': '#16a34a',          # verde
    'Média': '#f59e0b',         # amarelo
    'Baixa': '#dc2626',         # vermelho
    'Não informado': '#6b7280', # cinza
}

# =============================================================================
# CORES DE ESTADO
# =============================================================================
STATE_COLORS = {
    'Paraná': '#007934',         # verde bandeira PR
    'Santa Catarina': '#d52b1e', # vermelho bandeira SC
}

# =============================================================================
# CORES DE TIPO DE CASO (Antigo/Novo/Futuro)
# =============================================================================
CASE_TYPE_COLORS = {
    'Antigo': '#0891b2',  # cyan-600
    'Novo': '#16a34a',    # green-600
    'Futuro': '#9333ea',  # purple-600
}

# =============================================================================
# CORES DE CATEGORIA (Contencioso/Consultivo)
# =============================================================================
CATEGORY_COLORS = {
    'Contencioso': '#dc2626',  # vermelho
    'Consultivo': '#16a34a',   # verde
}

# =============================================================================
# CORES TEMPORAIS (para gráfico de linha)
# =============================================================================
TEMPORAL_COLORS = {
    'cases': '#455A64',        # Cinza azulado
    'processes': '#2d4a3f',    # Verde escuro (cor do sistema)
}

# =============================================================================
# CORES FINANCEIRAS
# =============================================================================
FINANCIAL_COLORS = {
    'exposicao': '#dc2626',    # vermelho
    'pago': '#16a34a',         # verde
    'futuro': '#9333ea',       # roxo
    'confirmado': '#b45309',   # amarelo queimado
    'em_analise': '#0891b2',   # cyan
}

# =============================================================================
# CORES DO HEATMAP
# =============================================================================
HEATMAP_COLORS = ['#e0f2fe', '#0ea5e9', '#0284c7', '#0369a1', '#075985', '#0c4a6e']

# =============================================================================
# CORES DE RESULTADO (Ganho/Perdido/Neutro)
# =============================================================================
RESULT_COLORS = {
    'Ganho': '#16a34a',           # verde
    'Perdido': '#dc2626',         # vermelho
    'Neutro': '#9ca3af',          # cinza
    'Não informado': '#6b7280',   # cinza escuro
}

# =============================================================================
# CORES PADRÃO PARA GRÁFICOS
# =============================================================================
DEFAULT_CHART_COLORS = [
    '#0891b2',  # cyan-600
    '#16a34a',  # green-600
    '#9333ea',  # purple-600
    '#dc2626',  # red-600
    '#f59e0b',  # amber-500
    '#6366f1',  # indigo-500
    '#ec4899',  # pink-500
    '#14b8a6',  # teal-500
]



