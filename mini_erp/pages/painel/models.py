"""
Constantes e configurações do módulo Painel.
Centraliza TAB_CONFIG e outras constantes específicas do painel.

As cores são importadas do arquivo centralizado mini_erp/constants.py
para garantir consistência visual em todo o sistema.
"""

# Importa todas as cores do arquivo centralizado
from mini_erp.constants import (
    AREA_COLORS_CHART as AREA_COLORS,
    STATUS_COLORS,
    PROBABILITY_COLORS,
    STATE_COLORS,
    CASE_TYPE_COLORS,
    CATEGORY_COLORS,
    TEMPORAL_COLORS,
    FINANCIAL_COLORS,
    HEATMAP_COLORS,
    DEFAULT_CHART_COLORS,
    RESULT_COLORS,
)

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
# ESTILOS CSS PARA ABAS
# =============================================================================
TAB_STYLES = '''
<style>
    .q-tab__icon { font-size: 16px !important; }
    .q-tab { min-height: 36px !important; padding: 4px 8px !important; }
</style>
'''


