"""
models.py - Modelos e constantes para o módulo Prazos.

Define tipos de dados e estruturas usadas em todo o módulo.
"""
from typing import TypedDict, List, Optional, Dict, Any


# =============================================================================
# CONSTANTES - STATUS DE PRAZO
# =============================================================================

STATUS_OPCOES = ['pendente', 'concluido']

STATUS_LABELS = {
    'pendente': 'Pendente',
    'concluido': 'Concluído',
}


# =============================================================================
# CONSTANTES - TIPOS DE RECORRÊNCIA
# =============================================================================

TIPOS_RECORRENCIA = ['anual', 'mensal', 'semanal', 'variavel']

TIPOS_RECORRENCIA_LABELS = {
    'anual': 'Anual',
    'mensal': 'Mensal',
    'semanal': 'Semanal',
    'variavel': 'Variável',
}


# =============================================================================
# CONSTANTES - OPÇÕES DE SEMANA
# =============================================================================

OPCOES_SEMANA = ['primeira', 'segunda', 'terceira', 'quarta', 'ultima']

OPCOES_SEMANA_LABELS = {
    'primeira': 'Primeira',
    'segunda': 'Segunda',
    'terceira': 'Terceira',
    'quarta': 'Quarta',
    'ultima': 'Última',
}


# =============================================================================
# CONSTANTES - OPÇÕES DE DIA DA SEMANA
# =============================================================================

OPCOES_DIA_SEMANA = [
    'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo'
]

OPCOES_DIA_SEMANA_LABELS = {
    'segunda': 'Segunda-feira',
    'terca': 'Terça-feira',
    'quarta': 'Quarta-feira',
    'quinta': 'Quinta-feira',
    'sexta': 'Sexta-feira',
    'sabado': 'Sábado',
    'domingo': 'Domingo',
}


# =============================================================================
# TIPOS ESTRUTURADOS (TypedDict)
# =============================================================================

class ConfigRecorrencia(TypedDict, total=False):
    """Estrutura de configuração de recorrência de prazo."""
    tipo: str  # 'anual' | 'mensal' | 'semanal' | 'variavel'
    dia_especifico: Optional[int]  # 1-31 ou None
    ultimo_dia_mes: bool
    dia_semana_especifico: Optional[Dict[str, str]]  # {'semana': str, 'dia': str}


class Prazo(TypedDict, total=False):
    """Estrutura de um prazo."""
    _id: str  # ID do documento no Firestore
    titulo: str  # Título do prazo (obrigatório)
    responsaveis: List[str]  # Lista de user_ids
    clientes: List[str]  # Lista de cliente_ids
    casos: List[str]  # Lista de caso_ids (slugs)
    prazo_fatal: float  # Timestamp (time.time())
    status: str  # 'pendente' | 'concluido'
    recorrente: bool
    config_recorrencia: Optional[ConfigRecorrencia]
    observacoes: str
    criado_em: float  # Timestamp
    atualizado_em: float  # Timestamp
    criado_por: str  # user_id





