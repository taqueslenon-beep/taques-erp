"""
models.py - Estruturas de dados e constantes para o módulo de Acordos.

Este módulo contém:
- Constantes de status e opções
- Estruturas de dados (TypedDict)
- Configurações de exibição
"""

from typing import Dict, List, Any, TypedDict, Optional
from datetime import datetime


# =============================================================================
# CONSTANTES DE STATUS E OPÇÕES
# =============================================================================

# Status permitidos para acordos
STATUS_OPTIONS = ['Rascunho', 'Ativo', 'Arquivado', 'Cancelado']

# Constantes de status padronizadas
STATUS_RASCUNHO = 'Rascunho'
STATUS_ATIVO = 'Ativo'
STATUS_ARQUIVADO = 'Arquivado'
STATUS_CANCELADO = 'Cancelado'

# Dicionário de mapeamento de status
STATUS_MAP = {
    'RASCUNHO': STATUS_RASCUNHO,
    'ATIVO': STATUS_ATIVO,
    'ARQUIVADO': STATUS_ARQUIVADO,
    'CANCELADO': STATUS_CANCELADO,
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class ClausulaDict(TypedDict, total=False):
    """Estrutura de uma cláusula de acordo."""
    tipo_clausula: str  # Tipo: "Geral" ou "Específica" (obrigatório)
    titulo: str  # Título da cláusula (obrigatório)
    numero: Optional[str]  # Número da cláusula (opcional) (ex: "1", "2.1", "3.2.1")
    descricao: Optional[str]  # Descrição breve da cláusula (opcional)
    status: str  # Status: "Cumprida", "Pendente", "Atrasada" (obrigatório)
    prazo_seguranca: Optional[str]  # Prazo de segurança (opcional) (formato YYYY-MM-DD)
    prazo_fatal: Optional[str]  # Prazo fatal (opcional) (formato YYYY-MM-DD)
    # Campos de comprovação (obrigatórios se status = "Cumprida")
    descricao_comprovacao: Optional[str]  # Descrição de como/onde foi cumprida (obrigatório se cumprida)
    link_comprovacao: Optional[str]  # Link de comprovação (opcional)
    data_cumprimento: Optional[str]  # Data de cumprimento (preenchida automaticamente quando status = "Cumprida")


class AcordoDict(TypedDict, total=False):
    """Estrutura de um acordo."""
    id: str  # ID único do acordo
    titulo: str  # Título/descrição do acordo
    descricao: Optional[str]  # Descrição detalhada
    casos_vinculados: List[str]  # Lista de IDs dos casos vinculados
    processos_vinculados: List[str]  # Lista de IDs dos processos vinculados
    data_celebracao: Optional[str]  # Data de celebração (formato YYYY-MM-DD)
    responsavel: Optional[str]  # ID do usuário responsável pela celebração (DEPRECATED - pode ser removido)
    clientes_ids: List[str]  # Lista de IDs dos clientes vinculados (múltiplos)
    parte_contraria: Optional[str]  # ID da parte contrária (singular)
    outros_envolvidos: List[str]  # Lista de IDs de outros envolvidos (múltiplos)
    clausulas: List[ClausulaDict]  # Lista de cláusulas do acordo
    # Campos DEPRECATED (mantidos para compatibilidade)
    cliente_id: Optional[str]  # DEPRECATED - usar clientes_ids
    outra_parte: Optional[str]  # DEPRECATED - usar parte_contraria
    partes_envolvidas: List[str]  # DEPRECATED - usar outros_envolvidos
    valor: Optional[float]  # Valor do acordo (se aplicável)
    data_assinatura: Optional[str]  # Data de assinatura (formato DD/MM/AAAA) - DEPRECATED, usar data_celebracao
    partes: List[str]  # Lista de partes envolvidas no acordo - DEPRECATED, usar partes_envolvidas
    processo_id: Optional[str]  # ID do processo vinculado (se aplicável) - DEPRECATED, usar processos_vinculados
    status: str  # Status do acordo (Rascunho, Ativo, Arquivado, Cancelado)
    data_criacao: str  # Data de criação (ISO format)
    data_atualizacao: str  # Data última atualização (ISO format)
    observacoes: Optional[str]  # Observações adicionais


# Constantes para status de cláusulas
CLAUSULA_STATUS_OPTIONS = ['Cumprida', 'Pendente', 'Atrasada']
CLAUSULA_STATUS_CUMPRIDA = 'Cumprida'
CLAUSULA_STATUS_PENDENTE = 'Pendente'
CLAUSULA_STATUS_ATRASADA = 'Atrasada'

# Constantes para tipo de cláusula
CLAUSULA_TIPO_OPTIONS = ['Geral', 'Específica']
CLAUSULA_TIPO_GERAL = 'Geral'
CLAUSULA_TIPO_ESPECIFICA = 'Específica'


# =============================================================================
# CONFIGURAÇÃO DE COLUNAS DA TABELA (para uso futuro)
# =============================================================================

COLUMNS_CONFIG = [
    {
        'key': 'titulo',
        'label': 'Título',
        'definition': {
            'name': 'titulo',
            'label': 'Título',
            'field': 'titulo',
            'align': 'left',
            'sortable': True,
            'style': 'max-width: 250px; white-space: normal;'
        }
    },
    {
        'key': 'cliente',
        'label': 'Cliente',
        'definition': {
            'name': 'cliente',
            'label': 'Cliente',
            'field': 'cliente',
            'align': 'left',
            'sortable': True,
            'style': 'max-width: 150px;'
        }
    },
    {
        'key': 'valor',
        'label': 'Valor',
        'definition': {
            'name': 'valor',
            'label': 'Valor',
            'field': 'valor',
            'align': 'right',
            'sortable': True,
            'style': 'max-width: 120px;'
        }
    },
    {
        'key': 'data_assinatura',
        'label': 'Data Assinatura',
        'definition': {
            'name': 'data_assinatura',
            'label': 'Data Assinatura',
            'field': 'data_assinatura',
            'align': 'center',
            'sortable': True,
            'style': 'max-width: 120px;'
        }
    },
    {
        'key': 'status',
        'label': 'Status',
        'definition': {
            'name': 'status',
            'label': 'Status',
            'field': 'status',
            'align': 'center',
            'sortable': True,
            'style': 'width: 120px; max-width: 120px;'
        }
    },
]

