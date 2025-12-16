"""
Módulo de modelos e constantes para Processos do workspace Visão Geral.
Define tipos de dados, constantes e estruturas usadas no módulo.
"""
from typing import TypedDict, List, Any, Optional

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
# TIPOS ESTRUTURADOS (TypedDict)
# =============================================================================


class Processo(TypedDict, total=False):
    """Estrutura de um processo no sistema."""
    # Identificação
    _id: str
    titulo: str                  # Título do processo (obrigatório)
    numero: str                  # Número do processo (ex: 0001234-56.2024.8.24.0000)
    tipo: str                    # "Judicial" ou "Administrativo"
    sistema_processual: str      # TJSC, TJPR, TRF4, IBAMA, IAT, etc.
    
    # Status
    status: str                  # "Ativo", "Suspenso", "Arquivado", "Baixado", "Encerrado"
    resultado: str               # "Procedente", "Improcedente", etc.
    
    # Localização
    area: str                    # "Cível", "Criminal", "Trabalhista", etc.
    estado: str                  # "Santa Catarina", "Paraná", etc.
    comarca: str                 # Nome da comarca
    vara: str                    # Nome da vara
    
    # Vinculação
    caso_id: str                 # ID do caso vinculado (opcional)
    caso_titulo: str             # Título do caso para exibição
    clientes: List[str]          # Lista de IDs de clientes
    clientes_nomes: List[str]    # Nomes dos clientes para exibição
    parte_contraria: str         # Nome da parte contrária
    parte_contraria_tipo: str    # "PF", "PJ", "Ente Público"
    
    # Grupo
    grupo_id: str                # ID do grupo de relacionamento
    grupo_nome: str              # Nome do grupo (ex: "Schmidmeier")
    
    # Hierarquia
    processo_pai_id: str         # ID do processo pai (para recursos, agravos, etc.)
    processo_pai_titulo: str     # Título do processo pai
    processos_filhos_ids: List[str]  # IDs dos processos filhos
    
    # Cenários
    cenario_melhor: str          # Descrição do melhor cenário
    cenario_intermediario: str   # Descrição do cenário intermediário
    cenario_pior: str            # Descrição do pior cenário
    
    # Datas
    data_abertura: str           # Data de abertura/distribuição
    data_ultima_movimentacao: str  # Data da última movimentação
    created_at: Any              # Data de criação do registro
    updated_at: Any              # Data de atualização
    
    # Observações
    observacoes: str             # Observações gerais (texto livre)


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================


def obter_cor_status(status: str) -> dict:
    """Retorna as cores (bg e text) do badge de status."""
    return STATUS_CORES.get(status, {'bg': '#6b7280', 'text': 'white'})


def obter_cor_resultado(resultado: str) -> dict:
    """Retorna as cores (bg e text) do badge de resultado."""
    return RESULTADO_CORES.get(resultado, {'bg': '#f3f4f6', 'text': '#374151'})


def obter_cor_area(area: str) -> dict:
    """Retorna as cores (bg, text, border) do badge de área."""
    return AREA_CORES.get(area, {'bg': '#f3f4f6', 'text': '#374151', 'border': '#d1d5db'})


def criar_processo_vazio() -> dict:
    """Retorna um dicionário com estrutura padrão de processo vazio."""
    return {
        'titulo': '',
        'numero': '',
        'tipo': 'Judicial',
        'sistema_processual': '',
        'status': 'Ativo',
        'resultado': 'Pendente',
        'area': '',
        'estado': 'Santa Catarina',
        'comarca': '',
        'vara': '',
        'caso_id': '',
        'caso_titulo': '',
        'clientes': [],
        'clientes_nomes': [],
        'parte_contraria': '',
        'parte_contraria_tipo': 'PF',
        'grupo_id': '',
        'grupo_nome': '',
        'processo_pai_id': '',
        'processo_pai_titulo': '',
        'processos_filhos_ids': [],
        'cenario_melhor': '',
        'cenario_intermediario': '',
        'cenario_pior': '',
        'data_abertura': '',
        'data_ultima_movimentacao': '',
        'observacoes': '',
    }


def validar_processo(dados: dict) -> tuple:
    """
    Valida os dados de um processo antes de salvar.

    Args:
        dados: Dicionário com dados do processo

    Returns:
        Tupla (valido: bool, mensagem_erro: str ou None)
    """
    # Título obrigatório
    titulo = dados.get('titulo', '').strip()
    if not titulo:
        return False, 'Título do processo é obrigatório.'

    if len(titulo) < 3:
        return False, 'Título deve ter pelo menos 3 caracteres.'

    # Tipo válido (se informado)
    tipo = dados.get('tipo', 'Judicial')
    if tipo and tipo not in TIPOS_PROCESSO:
        return False, 'Tipo de processo inválido.'

    # Status válido (se informado)
    status = dados.get('status', 'Ativo')
    if status and status not in STATUS_PROCESSO:
        return False, 'Status inválido.'

    # Área válida (se informada)
    area = dados.get('area', '')
    if area and area not in AREAS_PROCESSO:
        return False, 'Área inválida.'

    # Estado válido (se informado)
    estado = dados.get('estado', '')
    if estado and estado not in ESTADOS:
        return False, 'Estado inválido.'

    # Resultado válido (se informado)
    resultado = dados.get('resultado', 'Pendente')
    if resultado and resultado not in RESULTADOS_PROCESSO:
        return False, 'Resultado inválido.'

    return True, None



