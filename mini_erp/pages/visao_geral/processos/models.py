"""
Módulo de modelos para Processos do workspace Visão Geral.
Define tipos de dados, estruturas e validações usadas no módulo.
"""
from typing import TypedDict, List, Any, Optional
from .constants import (
    TIPOS_PROCESSO, STATUS_PROCESSO, STATUS_CORES,
    RESULTADOS_PROCESSO, RESULTADO_CORES,
    AREAS_PROCESSO, AREA_CORES,
    SISTEMAS_PROCESSUAIS, ESTADOS, PARTE_CONTRARIA_TIPOS
)
# Import de prioridades
from mini_erp.models.prioridade import (
    PRIORIDADE_PADRAO,
    CODIGOS_PRIORIDADE,
    get_cor_por_prioridade,
    validar_prioridade,
    normalizar_prioridade
)

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
    
    # Hierarquia (suporta múltiplos pais e filhos)
    processos_pai_ids: List[str]     # IDs dos processos pai (um processo pode ter múltiplos pais)
    processos_pai_titulos: List[str] # Títulos dos processos pai para exibição
    processo_pai_id: str             # ID do processo pai principal (legado/compatibilidade)
    processo_pai_titulo: str         # Título do processo pai principal (legado/compatibilidade)
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
    
    # Responsável
    responsavel: str            # UID do responsável pelo processo
    responsavel_nome: str       # Nome de exibição do responsável
    
    # Prioridade
    prioridade: str             # P1, P2, P3, P4 (opcional, default: P4)
    
    # Observações
    observacoes: str             # Observações gerais (texto livre)
    
    # Chaves de acesso
    chaves_acesso: List[dict]    # Lista de chaves de acesso do E-PROC


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================


def obter_cor_status(status: str) -> dict:
    """Retorna as cores (bg e text) do badge de status."""
    from .constants import STATUS_CORES
    return STATUS_CORES.get(status, {'bg': '#6b7280', 'text': 'white'})


def obter_cor_resultado(resultado: str) -> dict:
    """Retorna as cores (bg e text) do badge de resultado."""
    from .constants import RESULTADO_CORES
    return RESULTADO_CORES.get(resultado, {'bg': '#f3f4f6', 'text': '#374151'})


def obter_cor_area(area: str) -> dict:
    """Retorna as cores (bg, text, border) do badge de área."""
    from .constants import AREA_CORES
    return AREA_CORES.get(area, {'bg': '#f3f4f6', 'text': '#374151', 'border': '#d1d5db'})


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
        'processos_pai_ids': [],
        'processos_pai_titulos': [],
        'processo_pai_id': '',
        'processo_pai_titulo': '',
        'processos_filhos_ids': [],
        'cenario_melhor': '',
        'cenario_intermediario': '',
        'cenario_pior': '',
        'data_abertura': '',
        'data_ultima_movimentacao': '',
        'responsavel': '',
        'responsavel_nome': '',
        'prioridade': PRIORIDADE_PADRAO,  # P4 por padrão
        'observacoes': '',
        'chaves_acesso': [],  # Lista de chaves de acesso do E-PROC
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

    # Status válido (se informado) - aceita status antigos para migração
    status = dados.get('status', 'Em andamento')
    status_validos = STATUS_PROCESSO + ['Ativo', 'Suspenso', 'Arquivado', 'Baixado', 'Encerrado']
    if status and status not in status_validos:
        return False, 'Status inválido.'

    # Área válida (se informada) - permite vazio
    area = dados.get('area', '')
    if area and area not in AREAS_PROCESSO:
        return False, 'Área inválida.'

    # Estado válido (se informado) - permite vazio
    estado = dados.get('estado', '')
    if estado and estado not in ESTADOS:
        return False, 'Estado inválido.'

    # Resultado válido (se informado) - permite vazio
    resultado = dados.get('resultado', '')
    if resultado and resultado not in RESULTADOS_PROCESSO:
        return False, 'Resultado inválido.'

    # Prioridade válida (se informada) - permite vazio
    prioridade = dados.get('prioridade', '')
    if prioridade and not validar_prioridade(prioridade):
        return False, 'Prioridade inválida. Deve ser P1, P2, P3 ou P4.'

    return True, None
