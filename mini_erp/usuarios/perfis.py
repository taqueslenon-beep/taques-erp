"""
Definição de perfis de acesso do sistema TAQUES-ERP.
"""

PERFIS_ACESSO = {
    'cliente': {
        'nome': 'Cliente',
        'descricao': 'Acesso apenas ao workspace do cliente específico',
        'workspaces': ['schmidmeier'],  # apenas um workspace
        'pode_editar': False,
        'pode_excluir': False,
    },
    'interno': {
        'nome': 'Usuário Interno',
        'descricao': 'Acesso a todos os workspaces do escritório',
        'workspaces': ['schmidmeier', 'visao_geral'],  # ambos workspaces
        'pode_editar': True,
        'pode_excluir': False,
    },
    'admin': {
        'nome': 'Administrador',
        'descricao': 'Acesso total ao sistema',
        'workspaces': ['schmidmeier', 'visao_geral'],
        'pode_editar': True,
        'pode_excluir': True,
    },
}


def obter_perfil(perfil_id: str) -> dict:
    """
    Retorna informações de um perfil de acesso.
    
    Args:
        perfil_id: ID do perfil ('cliente', 'interno', 'admin')
    
    Returns:
        Dicionário com informações do perfil ou None se não encontrado
    """
    return PERFIS_ACESSO.get(perfil_id)


def listar_perfis() -> list:
    """
    Retorna lista de todos os perfis disponíveis.
    
    Returns:
        Lista de dicionários com informações dos perfis
    """
    return [
        {'id': k, **v} for k, v in PERFIS_ACESSO.items()
    ]












