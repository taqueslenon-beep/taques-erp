"""
Módulo de constantes para Processos do workspace Visão Geral.
Todas as constantes usadas no módulo estão centralizadas aqui.
"""
# =============================================================================
# CONSTANTES - TIPOS DE PROCESSO
# =============================================================================

TIPOS_PROCESSO = ["Judicial", "Administrativo"]

# =============================================================================
# CONSTANTES - TIPO PROCESSO AMBIENTAL
# =============================================================================

TIPOS_PROCESSO_AMBIENTAL = ["Desmatamento", "APP", "Outro"]
TIPO_AMBIENTAL_PADRAO = "Desmatamento"

# =============================================================================
# CONSTANTES - STATUS
# =============================================================================

STATUS_PROCESSO = ["Em andamento", "Concluído", "Em monitoramento"]

STATUS_CORES = {
    'Em andamento': {'bg': '#fbbf24', 'text': '#1f2937'},       # amarelo
    'Concluído': {'bg': '#059669', 'text': 'white'},            # verde esmeralda (diferente do padrão)
    'Em monitoramento': {'bg': '#f97316', 'text': 'white'},     # laranja
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
# CONSTANTES - SISTEMAS PROCESSUAIS (igual ao workspace Área do Cliente)
# =============================================================================

SISTEMAS_PROCESSUAIS = [
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
    'SAT/PGE-Net',
    'Sistema Interno - MPPR',
    'Sistema Interno - MPSC',
    'Processo físico 📁',
]

# =============================================================================
# CONSTANTES - NÚCLEOS (igual ao módulo de Casos)
# =============================================================================

NUCLEOS_PROCESSO = ['Ambiental', 'Cobranças', 'Generalista']

NUCLEO_CORES = {
    'Ambiental': {'bg': '#10b981', 'text': 'white'},      # verde
    'Cobranças': {'bg': '#f59e0b', 'text': 'white'},      # laranja
    'Generalista': {'bg': '#6366f1', 'text': 'white'},    # roxo/índigo
}

# =============================================================================
# CONSTANTES - ESTADOS
# =============================================================================

ESTADOS = [
    "Santa Catarina",
    "Paraná",
    "Rio Grande do Sul",
    "Rio de Janeiro",
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
# CONSTANTES - PRIORIDADES
# =============================================================================

# Prioridades disponíveis para filtro
PRIORIDADES_PROCESSO = ['P1', 'P2', 'P3', 'P4']

# Rótulos amigáveis para exibição no filtro
PRIORIDADE_LABELS = {
    'P1': 'Urgente',
    'P2': 'Alta',
    'P3': 'Média',
    'P4': 'Baixa',
}

# Cores das prioridades (para referência)
PRIORIDADE_CORES = {
    'P1': {'bg': '#DC2626', 'text': 'white'},  # Vermelho - Urgente
    'P2': {'bg': '#CA8A04', 'text': 'white'},  # Amarelo escuro - Alta
    'P3': {'bg': '#2563EB', 'text': 'white'},  # Azul - Média
    'P4': {'bg': '#6B7280', 'text': 'white'},  # Cinza - Baixa
}

# Prioridade padrão para novos processos
PRIORIDADE_PADRAO = 'P4'

# =============================================================================
# CONSTANTES - FIRESTORE
# =============================================================================
COLECAO_PROCESSOS = "vg_processos"
