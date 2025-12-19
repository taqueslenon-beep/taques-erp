"""
Módulo de modelos para Grupos de Relacionamento.
Define a estrutura de dados para grupos que agrupam pessoas relacionadas.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple


@dataclass
class GrupoRelacionamento:
    """
    Representa um grupo de relacionamento que agrupa pessoas relacionadas.
    
    Exemplo: Grupo "Schmidmeier" agrupa todas as empresas desse cliente.
    """
    _id: str = ""
    nome: str = ""
    descricao: str = ""
    icone: str = ""  # Emoji ou ícone, ex: "🇩🇪"
    cor: str = "#4CAF50"  # Cor para identificação visual
    ativo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicializa timestamps se não fornecidos."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o objeto para dicionário compatível com Firestore.
        
        Returns:
            Dicionário com os dados do grupo
        """
        dados = {
            'nome': self.nome,
            'descricao': self.descricao,
            'icone': self.icone,
            'cor': self.cor,
            'ativo': self.ativo,
        }
        
        # Adiciona timestamps se existirem
        if self.created_at:
            dados['created_at'] = self.created_at
        if self.updated_at:
            dados['updated_at'] = self.updated_at
        
        # Adiciona _id apenas se existir (não salva no Firestore)
        if self._id:
            dados['_id'] = self._id
        
        return dados
    
    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> 'GrupoRelacionamento':
        """
        Cria um GrupoRelacionamento a partir de um dicionário.
        
        Args:
            dados: Dicionário com os dados do grupo (do Firestore)
        
        Returns:
            Instância de GrupoRelacionamento
        """
        # Extrai _id se existir
        grupo_id = dados.pop('_id', '')
        
        # Converte timestamps se forem strings
        created_at = dados.get('created_at')
        updated_at = dados.get('updated_at')
        
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = None
        
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                updated_at = None
        
        # Cria instância
        grupo = cls(
            _id=grupo_id,
            nome=dados.get('nome', ''),
            descricao=dados.get('descricao', ''),
            icone=dados.get('icone', ''),
            cor=dados.get('cor', '#4CAF50'),
            ativo=dados.get('ativo', True),
            created_at=created_at or dados.get('created_at'),
            updated_at=updated_at or dados.get('updated_at'),
        )
        
        return grupo
    
    def validar(self) -> Tuple[bool, Optional[str]]:
        """
        Valida os dados do grupo.
        
        Returns:
            Tupla (valido: bool, mensagem_erro: str ou None)
        """
        if not self.nome or not self.nome.strip():
            return False, 'Nome do grupo é obrigatório.'
        
        if len(self.nome.strip()) < 2:
            return False, 'Nome do grupo deve ter pelo menos 2 caracteres.'
        
        # Valida formato de cor (hexadecimal)
        if self.cor and not self.cor.startswith('#'):
            return False, 'Cor deve estar no formato hexadecimal (#RRGGBB).'
        
        return True, None








