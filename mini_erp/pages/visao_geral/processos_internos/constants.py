"""
Constantes do módulo de Processos Internos.
Define categorias, prioridades e cores padronizadas.
"""

# =============================================================================
# CATEGORIAS DE PROCESSOS INTERNOS
# =============================================================================

CATEGORIAS_PROCESSO_INTERNO = [
    "operacional",
    "administrativo",
    "marketing",
    "financeiro",
    "relacionamento_cliente"
]

CATEGORIAS_DISPLAY = {
    "operacional": "Operacional",
    "administrativo": "Administrativo",
    "marketing": "Marketing",
    "financeiro": "Financeiro",
    "relacionamento_cliente": "Relacionamento com Cliente"
}

# =============================================================================
# PRIORIDADES
# =============================================================================

PRIORIDADES = ["P1", "P2", "P3", "P4"]

PRIORIDADE_DISPLAY = {
    "P1": "P1 - Crítica",
    "P2": "P2 - Alta",
    "P3": "P3 - Média",
    "P4": "P4 - Baixa"
}

# =============================================================================
# CORES DE PRIORIDADE
# =============================================================================

PRIORIDADE_CORES = {
    "P1": {
        "bg": "#EF4444",      # Vermelho
        "text": "white",
        "border": "#DC2626"
    },
    "P2": {
        "bg": "#F97316",      # Laranja
        "text": "white",
        "border": "#EA580C"
    },
    "P3": {
        "bg": "#EAB308",      # Amarelo
        "text": "#1F2937",    # Cinza escuro para contraste
        "border": "#CA8A04"
    },
    "P4": {
        "bg": "#22C55E",      # Verde
        "text": "white",
        "border": "#16A34A"
    }
}

# =============================================================================
# STATUS
# =============================================================================

STATUS_PROCESSO_INTERNO = ["ativo", "inativo", "concluido"]

STATUS_DISPLAY = {
    "ativo": "Ativo",
    "inativo": "Inativo",
    "concluido": "Concluído"
}

# =============================================================================
# COLECAO FIRESTORE
# =============================================================================

COLECAO_PROCESSOS_INTERNOS = "processos_internos"









