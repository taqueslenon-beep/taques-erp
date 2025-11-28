"""
Constantes e configurações do módulo Painel.
Centraliza TAB_CONFIG, esquemas de cores e outras constantes.
"""

# =============================================================================
# CONFIGURAÇÃO DAS ABAS
# =============================================================================
TAB_CONFIG = [
    ('totais', 'Totais', 'dashboard'),
    ('comparativo', 'Comparativo', 'bar_chart'),
    ('categoria', 'Categoria', 'category'),
    ('temporal', 'Temporal', 'timeline'),
    ('status', 'Status', 'insights'),
    ('resultado', 'Resultado', 'assessment'),
    ('cliente', 'Cliente', 'person'),
    ('parte', 'Parte Contrária', 'gavel'),
    ('area', 'Área', 'domain'),
    ('area_ha', 'Área (HA)', 'landscape'),
    ('estado', 'Estado', 'map'),
    ('heatmap', 'Mapa de Calor', 'whatshot'),
    ('probabilidade', 'Probabilidades', 'trending_up'),
    ('financeiro', 'Financeiro', 'attach_money'),
]

# =============================================================================
# CORES DE STATUS
# =============================================================================
STATUS_COLORS = {
    'Em andamento': '#b45309',              # amarelo queimado
    'Concluído': '#166534',                 # verde escuro
    'Concluído com pendências': '#4d7c0f',  # verde militar
    'Em monitoramento': '#ea580c',          # laranja
    'Sem status': '#6b7280',                # cinza
}

# =============================================================================
# CORES DE ÁREA JURÍDICA
# =============================================================================
AREA_COLORS = {
    'Administrativo': '#6b7280',      # cinza
    'Criminal': '#dc2626',            # vermelho
    'Cível': '#2563eb',               # azul
    'Tributário': '#7c3aed',          # roxo
    'Técnico/projetos': '#22c55e',    # verde
    'Outros': '#d1d5db',              # cinza claro
    'Não informado': '#9ca3af',       # cinza médio
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

# =============================================================================
# ESTILOS CSS PARA ABAS
# =============================================================================
TAB_STYLES = '''
<style>
    .q-tab__icon { font-size: 16px !important; }
    .q-tab { min-height: 36px !important; padding: 4px 8px !important; }
</style>
'''


