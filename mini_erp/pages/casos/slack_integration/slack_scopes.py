"""
Definição e explicação dos scopes (permissões) necessários para integração Slack.

Cada scope define uma permissão específica que a aplicação precisa
para funcionar corretamente. Este módulo documenta todos os scopes
usados e explica sua finalidade.
"""

from typing import List, Dict


# =============================================================================
# SCOPES OBRIGATÓRIOS
# =============================================================================

SLACK_SCOPES_REQUIRED = [
    'channels:read',        # Listar e obter informações de canais públicos
    'channels:history',     # Ler histórico de mensagens em canais públicos
    'users:read',           # Obter informações básicas de usuários
    'users:read.email',     # Obter email dos usuários (para identificar quem enviou mensagem)
]


# =============================================================================
# SCOPES RECOMENDADOS (para funcionalidades futuras)
# =============================================================================

SLACK_SCOPES_RECOMMENDED = [
    'groups:read',          # Listar canais privados (se necessário)
    'groups:history',       # Ler histórico de canais privados (se necessário)
    'files:read',           # Ler anexos de mensagens
    'emoji:read',           # Ler emojis customizados do workspace
]


# =============================================================================
# SCOPES OPCIONAIS (para expansão futura)
# =============================================================================

SLACK_SCOPES_OPTIONAL = [
    'chat:write',           # Enviar mensagens (para responder no Slack)
    'chat:write.public',    # Enviar mensagens em canais públicos
    'reactions:write',      # Adicionar reações em mensagens
    'files:write',          # Enviar arquivos
    'search:read',          # Buscar mensagens no Slack
]


# =============================================================================
# TODOS OS SCOPES (combinação de obrigatórios + recomendados)
# =============================================================================

SLACK_SCOPES_ALL = SLACK_SCOPES_REQUIRED + SLACK_SCOPES_RECOMMENDED


# =============================================================================
# DOCUMENTAÇÃO DETALHADA DE CADA SCOPE
# =============================================================================

SCOPE_DOCUMENTATION: Dict[str, Dict[str, str]] = {
    'channels:read': {
        'name': 'Ler informações de canais',
        'description': 'Permite que a aplicação liste canais públicos e obtenha informações sobre eles (nome, descrição, membros, etc.)',
        'required': True,
        'use_case': 'Necessário para buscar e vincular canais a casos jurídicos'
    },
    
    'channels:history': {
        'name': 'Ler histórico de canais',
        'description': 'Permite que a aplicação leia mensagens do histórico de canais públicos',
        'required': True,
        'use_case': 'Necessário para exibir mensagens do canal vinculado ao caso'
    },
    
    'users:read': {
        'name': 'Ler informações de usuários',
        'description': 'Permite que a aplicação obtenha informações básicas de usuários (nome, avatar, etc.)',
        'required': True,
        'use_case': 'Necessário para exibir quem enviou cada mensagem'
    },
    
    'users:read.email': {
        'name': 'Ler email de usuários',
        'description': 'Permite que a aplicação obtenha o email dos usuários',
        'required': True,
        'use_case': 'Necessário para identificar corretamente o autor das mensagens'
    },
    
    'groups:read': {
        'name': 'Ler informações de canais privados',
        'description': 'Permite que a aplicação liste canais privados (opcional, apenas se necessário)',
        'required': False,
        'use_case': 'Se você precisar vincular canais privados a casos'
    },
    
    'groups:history': {
        'name': 'Ler histórico de canais privados',
        'description': 'Permite que a aplicação leia mensagens de canais privados (opcional)',
        'required': False,
        'use_case': 'Se você precisar ler mensagens de canais privados'
    },
    
    'files:read': {
        'name': 'Ler arquivos',
        'description': 'Permite que a aplicação leia arquivos anexados em mensagens',
        'required': False,
        'use_case': 'Para exibir ou baixar anexos de mensagens do Slack'
    },
    
    'emoji:read': {
        'name': 'Ler emojis',
        'description': 'Permite que a aplicação obtenha lista de emojis customizados do workspace',
        'required': False,
        'use_case': 'Para renderizar corretamente emojis customizados nas mensagens'
    },
    
    'chat:write': {
        'name': 'Enviar mensagens',
        'description': 'Permite que a aplicação envie mensagens no Slack (não implementado ainda)',
        'required': False,
        'use_case': 'Para funcionalidade futura de responder mensagens do Slack'
    },
    
    'chat:write.public': {
        'name': 'Enviar mensagens em canais públicos',
        'description': 'Permite que a aplicação envie mensagens apenas em canais públicos',
        'required': False,
        'use_case': 'Alternativa mais restritiva a chat:write'
    },
    
    'reactions:write': {
        'name': 'Adicionar reações',
        'description': 'Permite que a aplicação adicione reações (emoji) em mensagens',
        'required': False,
        'use_case': 'Para funcionalidade futura de reagir a mensagens'
    },
    
    'files:write': {
        'name': 'Enviar arquivos',
        'description': 'Permite que a aplicação faça upload de arquivos no Slack',
        'required': False,
        'use_case': 'Para funcionalidade futura de anexar arquivos'
    },
    
    'search:read': {
        'name': 'Buscar mensagens',
        'description': 'Permite que a aplicação busque mensagens no Slack usando a busca nativa',
        'required': False,
        'use_case': 'Para funcionalidade futura de busca avançada'
    },
}


def get_scope_string(include_recommended: bool = True) -> str:
    """
    Retorna string de scopes formatada para usar na URL OAuth.
    
    Args:
        include_recommended: Se True, inclui scopes recomendados além dos obrigatórios
        
    Returns:
        String formatada com scopes separados por vírgula
    """
    scopes = SLACK_SCOPES_ALL if include_recommended else SLACK_SCOPES_REQUIRED
    return ','.join(scopes)


def get_scope_documentation(scope: str) -> Dict[str, str]:
    """
    Retorna documentação detalhada de um scope específico.
    
    Args:
        scope: Nome do scope (ex: 'channels:read')
        
    Returns:
        Dicionário com informações do scope ou dict vazio se não encontrado
    """
    return SCOPE_DOCUMENTATION.get(scope, {})


def list_all_scopes() -> List[str]:
    """
    Retorna lista de todos os scopes disponíveis.
    
    Returns:
        Lista de nomes de scopes
    """
    return list(SCOPE_DOCUMENTATION.keys())


def get_required_scopes() -> List[str]:
    """
    Retorna apenas os scopes obrigatórios.
    
    Returns:
        Lista de scopes obrigatórios
    """
    return SLACK_SCOPES_REQUIRED.copy()


def get_recommended_scopes() -> List[str]:
    """
    Retorna apenas os scopes recomendados.
    
    Returns:
        Lista de scopes recomendados
    """
    return SLACK_SCOPES_RECOMMENDED.copy()


