"""
Módulo de constantes para Processos do workspace Visão Geral.
Todas as constantes usadas no módulo estão centralizadas aqui.
"""
# =============================================================================
# CONSTANTES - TIPOS DE PROCESSO
# =============================================================================

TIPOS_PROCESSO = ["Judicial", "Administrativo"]

# =============================================================================
# CONSTANTES - STATUS
# =============================================================================

STATUS_PROCESSO = ["Ativo", "Suspenso", "Arquivado", "Baixado", "Encerrado"]

STATUS_CORES = {
    'Ativo': {'bg': '#22c55e', 'text': 'white'},              # verde
    'Suspenso': {'bg': '#eab308', 'text': '#1f2937'},         # amarelo
    'Arquivado': {'bg': '#6b7280', 'text': 'white'},          # cinza
    'Baixado': {'bg': '#ef4444', 'text': 'white'},            # vermelho
    'Encerrado': {'bg': '#166534', 'text': 'white'},          # verde escuro
}

# =============================================================================
# CONSTANTES - RESULTADOS
# =============================================================================

RESULTADOS_PROCESSO = [
    "Procedente",
    "Improcedente",
    "Parcialmente Procedente",
    "Acordo",
    "Desistência",
    "Pendente",
    "-"
]

RESULTADO_CORES = {
    'Procedente': {'bg': '#22c55e', 'text': 'white'},          # verde
    'Improcedente': {'bg': '#ef4444', 'text': 'white'},        # vermelho
    'Parcialmente Procedente': {'bg': '#f59e0b', 'text': 'white'},  # laranja
    'Acordo': {'bg': '#3b82f6', 'text': 'white'},              # azul
    'Desistência': {'bg': '#6b7280', 'text': 'white'},         # cinza
    'Pendente': {'bg': '#eab308', 'text': '#1f2937'},          # amarelo
    '-': {'bg': '#f3f4f6', 'text': '#374151'},                 # cinza claro
}

# =============================================================================
# CONSTANTES - ÁREAS
# =============================================================================

AREAS_PROCESSO = [
    "Cível",
    "Criminal",
    "Trabalhista",
    "Tributário",
    "Ambiental",
    "Administrativo"
]

AREA_CORES = {
    'Cível': {'bg': '#dbeafe', 'text': '#1e40af', 'border': '#3b82f6'},
    'Criminal': {'bg': '#fee2e2', 'text': '#991b1b', 'border': '#ef4444'},
    'Trabalhista': {'bg': '#fef3c7', 'text': '#92400e', 'border': '#f59e0b'},
    'Tributário': {'bg': '#ddd6fe', 'text': '#5b21b6', 'border': '#8b5cf6'},
    'Ambiental': {'bg': '#d1fae5', 'text': '#065f46', 'border': '#10b981'},
    'Administrativo': {'bg': '#f3f4f6', 'text': '#374151', 'border': '#9ca3af'},
}

# =============================================================================
# CONSTANTES - SISTEMAS PROCESSUAIS
# =============================================================================

SISTEMAS_PROCESSUAIS = [
    "TJSC",
    "TJPR",
    "TJRS",
    "TRF4",
    "STJ",
    "STF",
    "TST",
    "IBAMA",
    "IAT",
    "IMA",
    "FATMA",
    "Outro"
]

# =============================================================================
# CONSTANTES - ESTADOS
# =============================================================================

ESTADOS = [
    "Santa Catarina",
    "Paraná",
    "Rio Grande do Sul",
    "São Paulo",
    "Outro"
]

# =============================================================================
# CONSTANTES - TIPOS DE PARTE CONTRÁRIA
# =============================================================================

PARTE_CONTRARIA_TIPOS = ["PF", "PJ", "Ente Público"]

# =============================================================================
# CONSTANTES - CENÁRIOS
# =============================================================================

SCENARIO_TYPE_OPTIONS = ['🟢 Positivo', '⚪ Neutro', '🔴 Negativo']
SCENARIO_CHANCE_OPTIONS = ['Muito alta', 'Alta', 'Média', 'Baixa', 'Muito baixa']
SCENARIO_IMPACT_OPTIONS = ['Muito bom', 'Bom', 'Moderado', 'Ruim', 'Muito ruim']
SCENARIO_STATUS_OPTIONS = ['Mapeado', 'Em análise', 'Próximo de ocorrer', 'Ocorrido', 'Descartado']

# =============================================================================
# CONSTANTES - FIRESTORE
# =============================================================================

COLECAO_PROCESSOS = "vg_processos"



