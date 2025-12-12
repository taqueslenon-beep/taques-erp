"""
Módulo de modelos e constantes para Casos do workspace Visão Geral.
Define tipos de dados, constantes e estruturas usadas no módulo.

Campos simplificados:
- titulo, nucleo, status, categoria, estado, clientes, descricao, prioridade
- REMOVIDOS: ano, mes, parte_contraria
"""
from typing import TypedDict, List, Any

# Imports de prioridades
from ....models.prioridade import (
    PRIORIDADES_PADRAO,
    PRIORIDADE_PADRAO,
    CODIGOS_PRIORIDADE,
    get_cor_por_prioridade,
    validar_prioridade,
    normalizar_prioridade
)

# =============================================================================
# CONSTANTES - NÚCLEOS
# =============================================================================

NUCLEO_OPTIONS = ['Ambiental', 'Cobranças', 'Generalista']

NUCLEO_CORES = {
    'Ambiental': '#223631',      # Verde escuro
    'Cobranças': '#1e3a5f',      # Azul escuro
    'Generalista': '#5b9bd5',    # Azul claro
}

# =============================================================================
# CONSTANTES - STATUS
# =============================================================================

STATUS_OPTIONS = ['Em andamento', 'Suspenso', 'Arquivado', 'Encerrado']

STATUS_CORES = {
    'Em andamento': {'bg': '#3b82f6', 'text': 'white'},    # Azul
    'Suspenso': {'bg': '#f59e0b', 'text': 'black'},        # Amarelo
    'Arquivado': {'bg': '#6b7280', 'text': 'white'},       # Cinza
    'Encerrado': {'bg': '#ef4444', 'text': 'white'},       # Vermelho
}

# =============================================================================
# CONSTANTES - CATEGORIAS
# =============================================================================

CATEGORIA_OPTIONS = ['Contencioso', 'Consultivo', 'Outro']

CATEGORIA_CORES = {
    'Contencioso': {'bg': '#fee2e2', 'text': '#991b1b', 'border': '#991b1b'},
    'Consultivo': {'bg': '#dcfce7', 'text': '#166534', 'border': '#166534'},
    'Outro': {'bg': '#f3f4f6', 'text': '#374151', 'border': '#d1d5db'},
}

# =============================================================================
# CONSTANTES - ESTADOS (simplificado: apenas SC, PR, RS)
# =============================================================================

ESTADOS = ['Santa Catarina', 'Paraná', 'Rio Grande do Sul']

# Mapeamento de abreviações para nomes completos
ESTADO_ABREVIACOES = {
    'SC': 'Santa Catarina',
    'PR': 'Paraná',
    'RS': 'Rio Grande do Sul',
}

# =============================================================================
# CONSTANTES - PRIORIDADES
# =============================================================================

PRIORIDADE_OPTIONS = CODIGOS_PRIORIDADE  # ['P1', 'P2', 'P3', 'P4']

# =============================================================================
# TIPOS ESTRUTURADOS (TypedDict)
# =============================================================================


class Caso(TypedDict, total=False):
    """Estrutura de um caso no sistema (simplificada)."""
    _id: str
    titulo: str                  # Título/Nome do caso (obrigatório)
    nucleo: str                  # Ambiental, Cobranças, Generalista (obrigatório)
    status: str                  # Em andamento, Suspenso, Arquivado, Encerrado
    categoria: str               # Contencioso, Consultivo, Outro
    estado: str                  # Santa Catarina, Paraná, Rio Grande do Sul
    prioridade: str              # P1, P2, P3, P4 (opcional, default: P4)
    clientes: List[str]          # Lista de IDs de clientes vinculados
    clientes_nomes: List[str]    # Lista de nomes de clientes (para exibição)
    descricao: str               # Descrição/observações do caso
    created_at: Any
    updated_at: Any


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================


def obter_cor_nucleo(nucleo: str) -> str:
    """Retorna a cor do badge do núcleo."""
    return NUCLEO_CORES.get(nucleo, '#6b7280')


def obter_cor_status(status: str) -> dict:
    """Retorna as cores (bg e text) do badge de status."""
    return STATUS_CORES.get(status, {'bg': '#6b7280', 'text': 'white'})


def obter_cor_categoria(categoria: str) -> dict:
    """Retorna as cores (bg, text, border) do badge de categoria."""
    return CATEGORIA_CORES.get(categoria, {'bg': '#f3f4f6', 'text': '#374151', 'border': '#d1d5db'})


def obter_cor_prioridade(codigo: str) -> str:
    """
    Retorna a cor hexadecimal de uma prioridade.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Cor hexadecimal (ex: '#DC2626')
    """
    try:
        return get_cor_por_prioridade(codigo)
    except (ValueError, TypeError):
        # Fallback para P4 se código inválido
        return get_cor_por_prioridade(PRIORIDADE_PADRAO)


def criar_caso_vazio() -> dict:
    """Retorna um dicionário com estrutura padrão de caso vazio."""
    return {
        'titulo': '',
        'nucleo': 'Generalista',
        'status': 'Em andamento',
        'categoria': 'Contencioso',
        'estado': 'Santa Catarina',
        'prioridade': PRIORIDADE_PADRAO,  # P4 por padrão
        'clientes': [],
        'clientes_nomes': [],
        'descricao': '',
    }


def sanitizar_estado(valor: str) -> str:
    """
    Converte abreviação de estado para nome completo.
    Resolve o erro 'ValueError: Invalid value: SC' do NiceGUI.

    Args:
        valor: Valor do estado (pode ser 'SC', 'PR', 'RS' ou nome completo)

    Returns:
        Nome completo do estado ou string vazia
    """
    if not valor:
        return ''
    # Se já é nome completo, retorna
    if valor in ESTADOS:
        return valor
    # Converte abreviação para nome completo
    return ESTADO_ABREVIACOES.get(valor.upper(), valor)


def validar_caso(dados: dict) -> tuple:
    """
    Valida os dados de um caso antes de salvar.

    Args:
        dados: Dicionário com dados do caso

    Returns:
        Tupla (valido: bool, mensagem_erro: str ou None)
    """
    # Título obrigatório
    titulo = dados.get('titulo', '').strip()
    if not titulo:
        return False, 'Título do caso é obrigatório.'

    if len(titulo) < 3:
        return False, 'Título deve ter pelo menos 3 caracteres.'

    # Núcleo obrigatório
    nucleo = dados.get('nucleo', '')
    if nucleo not in NUCLEO_OPTIONS:
        return False, 'Núcleo inválido.'

    # Status válido (se informado)
    status = dados.get('status', 'Em andamento')
    if status and status not in STATUS_OPTIONS:
        return False, 'Status inválido.'

    # Categoria válida (se informada)
    categoria = dados.get('categoria', 'Contencioso')
    if categoria and categoria not in CATEGORIA_OPTIONS:
        return False, 'Categoria inválida.'

    # Estado válido (se informado)
    estado = dados.get('estado', '')
    if estado and estado not in ESTADOS:
        return False, 'Estado inválido.'

    # Prioridade válida (se informada)
    prioridade = dados.get('prioridade', PRIORIDADE_PADRAO)
    if prioridade and not validar_prioridade(prioridade):
        return False, 'Prioridade inválida. Deve ser P1, P2, P3 ou P4.'

    return True, None
