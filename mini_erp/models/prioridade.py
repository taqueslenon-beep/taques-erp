"""
Módulo de modelos para o sistema de prioridades de casos.

Define a estrutura de dados e constantes para prioridades (P1, P2, P3, P4).
"""

from typing import Optional, Dict, Any


# =============================================================================
# CONSTANTES - PRIORIDADES PADRÃO
# =============================================================================

PRIORIDADES_PADRAO = [
    {
        'codigo': 'P1',
        'cor_hex': '#DC2626',
        'ordem': 1,
        'descricao_interna': 'Máxima'
    },
    {
        'codigo': 'P2',
        'cor_hex': '#CA8A04',
        'ordem': 2,
        'descricao_interna': 'Alta'
    },
    {
        'codigo': 'P3',
        'cor_hex': '#2563EB',
        'ordem': 3,
        'descricao_interna': 'Média'
    },
    {
        'codigo': 'P4',
        'cor_hex': '#6B7280',
        'ordem': 4,
        'descricao_interna': 'Baixa'
    }
]

# Prioridade padrão para novos casos
PRIORIDADE_PADRAO = 'P4'

# Códigos válidos de prioridade
CODIGOS_PRIORIDADE = ['P1', 'P2', 'P3', 'P4']


# =============================================================================
# CLASSE PRIORIDADE
# =============================================================================

class Prioridade:
    """
    Classe que representa uma prioridade de caso.
    
    Atributos:
        codigo: Código da prioridade (P1, P2, P3, P4)
        cor_hex: Cor hexadecimal para exibição
        ordem: Ordem numérica (1-4) para classificação
        descricao_interna: Descrição interna (não exibida ao usuário)
    """
    
    def __init__(self, codigo: str, cor_hex: str, ordem: int, descricao_interna: str = ''):
        """
        Inicializa uma instância de Prioridade.
        
        Args:
            codigo: Código da prioridade (P1, P2, P3, P4)
            cor_hex: Cor hexadecimal (ex: '#DC2626')
            ordem: Ordem numérica (1-4)
            descricao_interna: Descrição interna opcional
        """
        if not validar_prioridade(codigo):
            raise ValueError(f"Código de prioridade inválido: {codigo}. Deve ser P1, P2, P3 ou P4.")
        
        self.codigo = codigo
        self.cor_hex = cor_hex
        self.ordem = ordem
        self.descricao_interna = descricao_interna
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a prioridade para dicionário.
        
        Returns:
            Dicionário com os dados da prioridade
        """
        return {
            'codigo': self.codigo,
            'cor_hex': self.cor_hex,
            'ordem': self.ordem,
            'descricao_interna': self.descricao_interna
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prioridade':
        """
        Cria uma instância de Prioridade a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados da prioridade
            
        Returns:
            Instância de Prioridade
        """
        return cls(
            codigo=data.get('codigo', 'P4'),
            cor_hex=data.get('cor_hex', '#6B7280'),
            ordem=data.get('ordem', 4),
            descricao_interna=data.get('descricao_interna', '')
        )


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_cor_por_prioridade(codigo: str) -> str:
    """
    Retorna a cor hexadecimal de uma prioridade.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Cor hexadecimal (ex: '#DC2626')
        
    Raises:
        ValueError: Se o código de prioridade for inválido
    """
    if not validar_prioridade(codigo):
        raise ValueError(f"Código de prioridade inválido: {codigo}")
    
    for prioridade in PRIORIDADES_PADRAO:
        if prioridade['codigo'] == codigo:
            return prioridade['cor_hex']
    
    # Fallback para P4 se não encontrar
    return PRIORIDADES_PADRAO[3]['cor_hex']


def get_ordem_por_prioridade(codigo: str) -> int:
    """
    Retorna a ordem numérica de uma prioridade.
    
    Args:
        codigo: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Ordem numérica (1-4)
        
    Raises:
        ValueError: Se o código de prioridade for inválido
    """
    if not validar_prioridade(codigo):
        raise ValueError(f"Código de prioridade inválido: {codigo}")
    
    for prioridade in PRIORIDADES_PADRAO:
        if prioridade['codigo'] == codigo:
            return prioridade['ordem']
    
    # Fallback para P4 se não encontrar
    return PRIORIDADES_PADRAO[3]['ordem']


def validar_prioridade(codigo: str) -> bool:
    """
    Valida se um código de prioridade é válido.
    
    Args:
        codigo: Código da prioridade a validar
    
    Returns:
        True se válido (P1, P2, P3 ou P4), False caso contrário
    """
    if not codigo:
        return False
    
    return codigo.upper() in CODIGOS_PRIORIDADE


def normalizar_prioridade(codigo: Optional[str]) -> str:
    """
    Normaliza um código de prioridade (converte para maiúscula e valida).
    
    Args:
        codigo: Código da prioridade (pode ser None ou vazio)
    
    Returns:
        Código normalizado ou PRIORIDADE_PADRAO se inválido
    """
    if not codigo:
        return PRIORIDADE_PADRAO
    
    codigo_upper = codigo.upper().strip()
    
    if validar_prioridade(codigo_upper):
        return codigo_upper
    
    return PRIORIDADE_PADRAO












