"""
Módulo de modelos para o sistema de Entregáveis.

Define a estrutura de dados, constantes e validações para entregáveis.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .prioridade import get_cor_por_prioridade, validar_prioridade, normalizar_prioridade


# =============================================================================
# CONSTANTES - STATUS
# =============================================================================

STATUS_OPCOES = [
    'Em espera',
    'Pendente',
    'Em andamento',
    'Concluído',
]

STATUS_PADRAO = 'Em espera'

# Mapeamento de status antigos para novos (migração)
MIGRAR_STATUS = {
    'Aguardando': 'Em espera',
    'Pendente': 'Pendente',
    'Em andamento': 'Em andamento',
    'Concluído': 'Concluído',
}

# =============================================================================
# CORES DAS COLUNAS DO KANBAN
# =============================================================================

CORES_STATUS = {
    'Em espera': {
        'bg': '#FFF7ED',        # laranja claro (fundo)
        'header': '#F97316',    # laranja (header)
        'text': '#9A3412',      # laranja escuro (texto)
    },
    'Pendente': {
        'bg': '#FEF2F2',        # vermelho claro (fundo)
        'header': '#EF4444',    # vermelho (header)
        'text': '#991B1B',      # vermelho escuro (texto)
    },
    'Em andamento': {
        'bg': '#FEFCE8',        # amarelo claro (fundo)
        'header': '#EAB308',    # amarelo (header)
        'text': '#854D0E',      # amarelo escuro (texto)
    },
    'Concluído': {
        'bg': '#F0FDF4',        # verde claro (fundo)
        'header': '#22C55E',    # verde (header)
        'text': '#166534',      # verde escuro (texto)
    },
}


# =============================================================================
# CONSTANTES - CATEGORIAS
# =============================================================================

CATEGORIAS_OPCOES = [
    'Operacional',
    'Marketing',
    'Vendas',
    'Administrativo',
    'Estratégico'
]

CATEGORIA_PADRAO = 'Operacional'


# =============================================================================
# CORES DE PRIORIDADE (padronizadas)
# P1 = Vermelho, P2 = Amarelo, P3 = Azul, P4 = Cinza
# =============================================================================

CORES_PRIORIDADE = {
    'P1': '#DC2626',  # Vermelho
    'P2': '#F59E0B',  # Amarelo
    'P3': '#3B82F6',  # Azul
    'P4': '#6B7280',  # Cinza
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_cor_prioridade_entregavel(codigo: str) -> str:
    """
    Retorna a cor hexadecimal de uma prioridade para entregáveis.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Cor hexadecimal conforme especificação
    """
    return CORES_PRIORIDADE.get(codigo.upper(), CORES_PRIORIDADE['P4'])


def validar_status(status: str) -> bool:
    """
    Valida se um status é válido.

    Args:
        status: Status a validar

    Returns:
        True se válido, False caso contrário
    """
    return status in STATUS_OPCOES


def normalizar_status(status: str) -> str:
    """
    Normaliza um status, convertendo valores antigos para os novos.

    Args:
        status: Status a normalizar

    Returns:
        Status normalizado
    """
    if status in STATUS_OPCOES:
        return status
    return MIGRAR_STATUS.get(status, STATUS_PADRAO)


def validar_categoria(categoria: str) -> bool:
    """
    Valida se uma categoria é válida.
    
    Args:
        categoria: Categoria a validar
    
    Returns:
        True se válida, False caso contrário
    """
    return categoria in CATEGORIAS_OPCOES


# =============================================================================
# CLASSE ENTREGAVEL
# =============================================================================

class Entregavel:
    """
    Classe que representa um entregável.

    Atributos:
        id: ID único do entregável (gerado automaticamente)
        titulo: Título do entregável
        responsavel_id: ID do usuário responsável
        responsavel_nome: Nome do responsável (para exibição rápida)
        categoria: Categoria do entregável
        status: Status atual do entregável
        prioridade: Prioridade (P1, P2, P3, P4)
        prazo: Data de prazo (opcional)
        slack_link: Link para mensagem no Slack (opcional)
        criado_em: Data de criação
        atualizado_em: Data da última atualização
        criado_por: ID do usuário que criou
    """

    def __init__(
        self,
        titulo: str,
        responsavel_id: str,
        responsavel_nome: str,
        categoria: str = CATEGORIA_PADRAO,
        status: str = STATUS_PADRAO,
        prioridade: str = 'P4',
        prazo: Optional[datetime] = None,
        slack_link: Optional[str] = None,
        criado_por: Optional[str] = None,
        id: Optional[str] = None,
        criado_em: Optional[datetime] = None,
        atualizado_em: Optional[datetime] = None
    ):
        """
        Inicializa uma instância de Entregavel.
        
        Args:
            titulo: Título do entregável (obrigatório)
            responsavel_id: ID do responsável (obrigatório)
            responsavel_nome: Nome do responsável (obrigatório)
            categoria: Categoria (padrão: Operacional)
            status: Status (padrão: Pendente)
            prioridade: Prioridade (padrão: P4)
            prazo: Data de prazo (opcional)
            criado_por: ID do usuário criador (opcional)
            id: ID do entregável (gerado automaticamente se None)
            criado_em: Data de criação (gerada automaticamente se None)
            atualizado_em: Data de atualização (gerada automaticamente se None)
        """
        if not titulo or not titulo.strip():
            raise ValueError("Título é obrigatório")
        
        if not responsavel_id:
            raise ValueError("Responsável é obrigatório")
        
        if not responsavel_nome:
            raise ValueError("Nome do responsável é obrigatório")
        
        if not validar_categoria(categoria):
            raise ValueError(f"Categoria inválida: {categoria}")
        
        if not validar_status(status):
            raise ValueError(f"Status inválido: {status}")
        
        if not validar_prioridade(prioridade):
            raise ValueError(f"Prioridade inválida: {prioridade}")
        
        self.id = id
        self.titulo = titulo.strip()
        self.responsavel_id = responsavel_id
        self.responsavel_nome = responsavel_nome
        self.categoria = categoria
        self.status = status
        self.prioridade = normalizar_prioridade(prioridade)
        self.prazo = prazo
        self.slack_link = slack_link or ''
        self.criado_por = criado_por
        self.criado_em = criado_em or datetime.now()
        self.atualizado_em = atualizado_em or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o entregável para dicionário (para salvar no Firestore).
        
        Returns:
            Dicionário com os dados do entregável
        """
        dados = {
            'titulo': self.titulo,
            'responsavel_id': self.responsavel_id,
            'responsavel_nome': self.responsavel_nome,
            'categoria': self.categoria,
            'status': self.status,
            'prioridade': self.prioridade,
            'slack_link': self.slack_link,
            'criado_por': self.criado_por,
        }

        if self.prazo:
            # Converte datetime para timestamp
            if isinstance(self.prazo, datetime):
                dados['prazo'] = self.prazo.timestamp()
            else:
                dados['prazo'] = self.prazo
        
        if self.criado_em:
            if isinstance(self.criado_em, datetime):
                dados['criado_em'] = self.criado_em.timestamp()
            else:
                dados['criado_em'] = self.criado_em
        
        if self.atualizado_em:
            if isinstance(self.atualizado_em, datetime):
                dados['atualizado_em'] = self.atualizado_em.timestamp()
            else:
                dados['atualizado_em'] = self.atualizado_em
        
        return dados
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: Optional[str] = None) -> 'Entregavel':
        """
        Cria uma instância de Entregavel a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados do entregável
            doc_id: ID do documento no Firestore (opcional)
        
        Returns:
            Instância de Entregavel
        """
        # Converte timestamps para datetime
        criado_em = None
        if 'criado_em' in data:
            if isinstance(data['criado_em'], (int, float)):
                criado_em = datetime.fromtimestamp(data['criado_em'])
            else:
                criado_em = data['criado_em']
        
        atualizado_em = None
        if 'atualizado_em' in data:
            if isinstance(data['atualizado_em'], (int, float)):
                atualizado_em = datetime.fromtimestamp(data['atualizado_em'])
            else:
                atualizado_em = data['atualizado_em']
        
        prazo = None
        if 'prazo' in data and data['prazo']:
            if isinstance(data['prazo'], (int, float)):
                prazo = datetime.fromtimestamp(data['prazo'])
            else:
                prazo = data['prazo']
        
        return cls(
            id=doc_id or data.get('_id'),
            titulo=data.get('titulo', ''),
            responsavel_id=data.get('responsavel_id', ''),
            responsavel_nome=data.get('responsavel_nome', ''),
            categoria=data.get('categoria', CATEGORIA_PADRAO),
            status=data.get('status', STATUS_PADRAO),
            prioridade=data.get('prioridade', 'P4'),
            prazo=prazo,
            slack_link=data.get('slack_link', ''),
            criado_por=data.get('criado_por'),
            criado_em=criado_em,
            atualizado_em=atualizado_em
        )










