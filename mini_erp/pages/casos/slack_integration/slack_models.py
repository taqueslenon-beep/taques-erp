"""
Modelos de dados para mensagens, canais e usuários do Slack.

Este módulo define as estruturas de dados usadas para representar
entidades do Slack dentro do sistema.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class SlackUser:
    """
    Representa um usuário do Slack.
    """
    id: str
    name: str
    real_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    image_24: Optional[str] = None
    image_32: Optional[str] = None
    image_48: Optional[str] = None
    image_72: Optional[str] = None
    image_192: Optional[str] = None
    
    def get_avatar_url(self, size: int = 48) -> str:
        """
        Retorna URL do avatar no tamanho especificado.
        
        Args:
            size: Tamanho do avatar (24, 32, 48, 72, 192)
            
        Returns:
            URL do avatar ou URL padrão se não disponível
        """
        size_map = {
            24: self.image_24,
            32: self.image_32,
            48: self.image_48,
            72: self.image_72,
            192: self.image_192
        }
        
        url = size_map.get(size, self.image_48)
        return url or 'https://via.placeholder.com/48'
    
    def get_display_name(self) -> str:
        """Retorna o nome de exibição preferido."""
        return self.display_name or self.real_name or self.name
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'SlackUser':
        """Cria instância a partir de dados da API do Slack."""
        profile = data.get('profile', {})
        
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            real_name=profile.get('real_name'),
            display_name=profile.get('display_name'),
            email=profile.get('email'),
            image_24=profile.get('image_24'),
            image_32=profile.get('image_32'),
            image_48=profile.get('image_48'),
            image_72=profile.get('image_72'),
            image_192=profile.get('image_192')
        )


@dataclass
class SlackChannel:
    """
    Representa um canal do Slack.
    """
    id: str
    name: str
    is_private: bool = False
    is_archived: bool = False
    topic: Optional[str] = None
    purpose: Optional[str] = None
    created: Optional[int] = None
    creator: Optional[str] = None
    num_members: Optional[int] = None
    
    @property
    def display_name(self) -> str:
        """Retorna nome formatado para exibição."""
        prefix = '# ' if not self.is_private else '🔒 '
        return f"{prefix}{self.name}"
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'SlackChannel':
        """Cria instância a partir de dados da API do Slack."""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            is_private=data.get('is_private', False),
            is_archived=data.get('is_archived', False),
            topic=data.get('topic', {}).get('value') if isinstance(data.get('topic'), dict) else data.get('topic'),
            purpose=data.get('purpose', {}).get('value') if isinstance(data.get('purpose'), dict) else data.get('purpose'),
            created=data.get('created'),
            creator=data.get('creator'),
            num_members=data.get('num_members')
        )


@dataclass
class SlackMessage:
    """
    Representa uma mensagem do Slack.
    """
    ts: str  # Timestamp único da mensagem
    channel_id: str
    user_id: Optional[str] = None
    text: str = ''
    thread_ts: Optional[str] = None  # Se presente, esta mensagem é resposta em thread
    reply_count: int = 0
    reactions: List[Dict[str, Any]] = field(default_factory=list)
    files: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    edited: Optional[Dict[str, Any]] = None
    pinned_to: List[str] = field(default_factory=list)
    subscribed: bool = False
    subtype: Optional[str] = None  # Ex: 'bot_message', 'channel_join', etc.
    
    # Metadados adicionais (não vêm diretamente da API)
    user: Optional[SlackUser] = None
    formatted_text: Optional[str] = None
    parsed_at: Optional[datetime] = None
    
    @property
    def timestamp(self) -> datetime:
        """
        Converte timestamp do Slack (ts) para datetime Python.
        
        Slack usa formato: segundos.fracionado (ex: 1609459200.123456)
        """
        try:
            ts_float = float(self.ts)
            return datetime.fromtimestamp(ts_float)
        except (ValueError, TypeError):
            return datetime.now()
    
    @property
    def is_thread_reply(self) -> bool:
        """Verifica se a mensagem é uma resposta em thread."""
        return self.thread_ts is not None and self.thread_ts != self.ts
    
    @property
    def is_bot_message(self) -> bool:
        """Verifica se a mensagem é de um bot."""
        return self.subtype == 'bot_message' or self.user_id is None
    
    def get_reaction_count(self, name: str) -> int:
        """
        Retorna número de reações de um tipo específico.
        
        Args:
            name: Nome da reação (ex: 'thumbsup')
            
        Returns:
            Número de reações
        """
        for reaction in self.reactions:
            if reaction.get('name') == name:
                return reaction.get('count', 0)
        return 0
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any], channel_id: str, 
                     user_cache: Optional[Dict[str, SlackUser]] = None) -> 'SlackMessage':
        """
        Cria instância a partir de dados da API do Slack.
        
        Args:
            data: Dados da mensagem da API
            channel_id: ID do canal
            user_cache: Cache opcional de usuários para preenchimento automático
            
        Returns:
            Instância de SlackMessage
        """
        user = None
        user_id = data.get('user')
        
        # Tenta buscar usuário do cache se disponível
        if user_cache and user_id:
            user = user_cache.get(user_id)
        
        return cls(
            ts=data.get('ts', ''),
            channel_id=channel_id,
            user_id=user_id,
            text=data.get('text', ''),
            thread_ts=data.get('thread_ts'),
            reply_count=data.get('reply_count', 0),
            reactions=data.get('reactions', []),
            files=data.get('files', []),
            attachments=data.get('attachments', []),
            edited=data.get('edited'),
            pinned_to=data.get('pinned_to', []),
            subscribed=data.get('subscribed', False),
            subtype=data.get('subtype'),
            user=user,
            parsed_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte mensagem para dicionário (para armazenamento em cache)."""
        return {
            'ts': self.ts,
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'text': self.text,
            'thread_ts': self.thread_ts,
            'reply_count': self.reply_count,
            'reactions': self.reactions,
            'files': self.files,
            'attachments': self.attachments,
            'edited': self.edited,
            'pinned_to': self.pinned_to,
            'subscribed': self.subscribed,
            'subtype': self.subtype,
            'parsed_at': self.parsed_at.isoformat() if self.parsed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SlackMessage':
        """Cria instância a partir de dicionário (de cache)."""
        parsed_at = None
        if data.get('parsed_at'):
            try:
                parsed_at = datetime.fromisoformat(data['parsed_at'])
            except (ValueError, TypeError):
                pass
        
        return cls(
            ts=data.get('ts', ''),
            channel_id=data.get('channel_id', ''),
            user_id=data.get('user_id'),
            text=data.get('text', ''),
            thread_ts=data.get('thread_ts'),
            reply_count=data.get('reply_count', 0),
            reactions=data.get('reactions', []),
            files=data.get('files', []),
            attachments=data.get('attachments', []),
            edited=data.get('edited'),
            pinned_to=data.get('pinned_to', []),
            subscribed=data.get('subscribed', False),
            subtype=data.get('subtype'),
            parsed_at=parsed_at
        )


